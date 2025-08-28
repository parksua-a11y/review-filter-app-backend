from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import urllib.request
import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import cv2
import numpy as np
try:
    import tensorflow as tf
except ImportError:
    tf = None
    print("TensorFlow not available - image classification disabled")
try:
    import easyocr
except ImportError:
    easyocr = None
    print("EasyOCR not available - OCR disabled")
from thefuzz import fuzz
from math import ceil

# Flask 애플리케이션 초기화
app = Flask(__name__)
CORS(app) # CORS 활성화

# --- 환경변수에서 API 키 가져오기 (보안 개선) ---
client_id = os.environ.get('NAVER_CLIENT_ID', 'uCwYzWa2eaaSrAT6Dvm5')
client_secret = os.environ.get('NAVER_CLIENT_SECRET', '2H6UEylob9')

# --- OCR 리더 초기화 (조건부) ---
ocr_reader = None
if easyocr:
    try:
        print("EasyOCR 리더를 초기화합니다...")
        ocr_reader = easyocr.Reader(['ko', 'en'])
        print("EasyOCR 리더 초기화 완료.")
    except Exception as e:
        print(f"EasyOCR 초기화 실패: {e}")

# --- 모델 로드 (조건부) ---
MODEL_PATH = 'sponsorship_image_classifier.h5'
model = None
if tf and os.path.exists(MODEL_PATH):
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        print(f"'{MODEL_PATH}' 모델을 성공적으로 불러왔습니다.")
    except Exception as e:
        print(f"모델 로드 중 오류 발생: {e}")

IMG_WIDTH, IMG_HEIGHT = 150, 150
PREDICTION_THRESHOLD = 0.7
SIMILARITY_THRESHOLD = 85

SPONSORSHIP_KEYWORDS = [
    '협찬', '제공받아', '제공받고', '원고료', '소정의', '지원받아', '유료광고', '대가로', '업체로부터', '제공받았습니다', '수수료', '파트너스',
    '리뷰노트', '가보자체험단', '체험단', '디너의여왕', '슈퍼멤버스', '식사권', 'revu', '서울오빠', '링뷰', '원더블', '원블', '미블', '업체'
    '공정거래위원회', '공정위', '지급받아', '링블', 'MRBLE'
]
SPONSORSHIP_URL_KEYWORDS = [
    'revu.net', 'seoulouba.co.kr', 'dinnerqueen.net', 'reviewnote.co.kr', '가보자체험단.com', 'wenxiblog.com',
    'mrblog.net', 'reviewplace.co.kr', '강남맛집.net', 'supermembers.co.kr', 'ringview.co.kr', 'ddok.co.kr', 'ringble.co.kr', 'assaview.co.kr'
    'storyn.kr', 'odiya.kr', 'chvu.co.kr', 'reviewer.cashnote.kr', '4blog.net', 'popomon.com', 'cometoplay.kr', 'dailyview.kr',
    'revu.net', 'reviewjin.com', 'modublog.co.kr', 'assaview.co.kr', 'kormedia.co.kr', 'cherivu.co.kr', '클립뷰.kr', 'tagby.io',
    'www.tble.kr', 'popomon.com', 'blogdexreview.space'
]
POSTS_PER_PAGE = 6

# --- 웹드라이버 설정 (배포 환경용) ---
def create_driver():
    """배포 환경에 맞는 웹드라이버 생성"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
    
    try:
        # Railway 등 클라우드 환경에서는 시스템 Chrome 사용
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(5)
        return driver
    except Exception as e:
        print(f"웹 드라이버 생성 실패: {e}")
        return None

# --- 기존 함수들 (간소화) ---
def find_element(soup, selectors):
    for selector in selectors:
        element = soup.select_one(selector)
        if element: return element
    return None

def predict_image(image_bytes):
    if not model: return 0.0
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None: return 0.0
        resized_img = cv2.resize(img, (IMG_WIDTH, IMG_HEIGHT))
        normalized_img = resized_img / 255.0
        input_img = np.expand_dims(normalized_img, axis=0)
        prediction = model.predict(input_img, verbose=0)
        return prediction[0][0]
    except Exception:
        return 0.0

def check_image_with_expert_ocr(image_bytes, reader):
    if not reader: return False
    MIN_TEXT_LENGTH = 2
    try:
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None: return False

        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        results = reader.readtext(gray_img, detail=0)
        
        for text in results:
            processed_text = text.replace(" ", "").lower()
            if len(processed_text) < MIN_TEXT_LENGTH: continue
            
            for keyword in SPONSORSHIP_KEYWORDS:
                score = fuzz.partial_ratio(processed_text, keyword)
                if score >= SIMILARITY_THRESHOLD:
                    print(f"이미지에서 키워드 '{keyword}' 발견")
                    return True
    except Exception as e:
        print(f"OCR 처리 중 오류: {e}")
        return False
    return False

def is_sponsored_post(content_element):
    """간소화된 협찬 여부 판단"""
    # 기본값
    author_name = '네이버 블로거'
    
    if not content_element:
        return False, author_name

    # 텍스트 기반 협찬 키워드 확인
    main_text = content_element.get_text(separator=" ").lower()
    is_sponsored_by_text = any(keyword in main_text for keyword in SPONSORSHIP_KEYWORDS[:10])  # 주요 키워드만 사용
    
    if is_sponsored_by_text:
        print("텍스트에서 협찬 키워드 발견")
        return True, author_name

    # URL 기반 확인
    is_sponsored_by_url = any(url_keyword in main_text for url_keyword in SPONSORSHIP_URL_KEYWORDS[:10])  # 주요 URL만 확인
    if is_sponsored_by_url:
        print("URL에서 협찬 키워드 발견")
        return True, author_name

    return False, author_name

# --- Flask 라우트 ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_blogs():
    """간소화된 블로그 검색 API"""
    data = request.json
    keyword = data.get('keyword')
    page = int(data.get('page', 1))
    include_sponsored = data.get('includeSponsored', False)
    
    if not keyword:
        return jsonify({"error": "키워드를 입력해주세요."}), 400

    print(f"'{keyword}' 키워드로 검색 시작")

    # 네이버 검색 API로 URL 수집
    naver_urls = []
    encText = urllib.parse.quote(keyword)
    MAX_SEARCH_PAGES = 1  # 배포 환경에서는 1페이지만 크롤링
    display = 10
    
    url = f"https://openapi.naver.com/v1/search/blog?query={encText}&start=1&display={display}"
    try:
        req = urllib.request.Request(url)
        req.add_header("X-Naver-Client-Id", client_id)
        req.add_header("X-Naver-Client-Secret", client_secret)
        res = urllib.request.urlopen(req)
        if res.getcode() == 200:
            items = json.loads(res.read().decode('utf-8'))['items']
            for row in items:
                if 'blog.naver.com' in row['link']:
                    naver_urls.append(row['link'])
        else:
            return jsonify({"error": f"네이버 API 오류: {res.getcode()}"}), 500
    except Exception as e:
        print(f"API 요청 중 오류: {e}")
        return jsonify({"error": "네이버 API 요청 실패"}), 500

    if not naver_urls:
        return jsonify({"error": "검색 결과가 없습니다."}), 404

    # 웹드라이버 생성
    driver = create_driver()
    if not driver:
        return jsonify({"error": "웹드라이버 생성 실패"}), 500

    all_posts = []
    sponsored_count = 0
    
    try:
        # 최대 5개 URL만 크롤링 (성능 고려)
        for i, url in enumerate(naver_urls[:5]):
            print(f"[{i+1}/5] {url} 확인 중...")
            
            post_info = {
                "title": "제목 없음",
                "url": url,
                "author": "네이버 블로거",
                "is_sponsored": False,
                "date": "날짜 정보 없음"
            }
            
            try:
                driver.get(url)
                time.sleep(2)
                driver.switch_to.frame("mainFrame")
                
                soup = BeautifulSoup(driver.page_source, "html.parser")
                
                # 제목 추출
                title_selectors = ['div.se-module.se-module-text.se-title-text', 'div.pcol1 > span']
                title_tag = find_element(soup, title_selectors)
                if title_tag:
                    post_info["title"] = title_tag.get_text(strip=True)
                
                # 본문 추출 및 협찬 여부 판단
                content_selectors = ['div.se-main-container', 'div#postViewArea']
                content_tag = find_element(soup, content_selectors)
                
                is_sponsored, author_name = is_sponsored_post(content_tag)
                
                post_info["is_sponsored"] = is_sponsored
                post_info["author"] = author_name
                
                if is_sponsored:
                    sponsored_count += 1
                
                driver.switch_to.default_content()
                
            except Exception as e:
                print(f"크롤링 중 오류: {e}")
                try: driver.switch_to.default_content()
                except: pass
            finally:
                all_posts.append(post_info)
                
    finally:
        driver.quit()

    # 필터링
    final_posts = all_posts if include_sponsored else [post for post in all_posts if not post['is_sponsored']]
    
    # 페이지네이션
    total_posts = len(final_posts)
    total_pages = ceil(total_posts / POSTS_PER_PAGE) if total_posts > 0 else 1
    
    start_index = (page - 1) * POSTS_PER_PAGE
    end_index = start_index + POSTS_PER_PAGE
    paginated_posts = final_posts[start_index:end_index]

    print(f"크롤링 완료. {total_posts}개 게시물 반환")
    
    return jsonify({
        "status": "success",
        "results": paginated_posts,
        "total_posts": total_posts,
        "total_pages": total_pages,
        "filtered_count": sponsored_count
    })

@app.route('/health')
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({"status": "healthy"})

# --- 메인 실행부 ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

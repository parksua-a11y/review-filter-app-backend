from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import urllib.request
import urllib.parse
import os
import re
from math import ceil

app = Flask(__name__)
CORS(app)

# API 키
client_id = os.environ.get('NAVER_CLIENT_ID')
client_secret = os.environ.get('NAVER_CLIENT_SECRET')

# 협찬 키워드 (더 포괄적으로)
SPONSORSHIP_KEYWORDS = [
    '협찬', '제공받아', '제공받고', '원고료', '소정의', '지원받아', '유료광고', 
    '리뷰노트', '체험단', 'revu', '서울오빠', '가보자체험단', '디너의여왕',
    '슈퍼멤버스', '원더블', '미블', '링뷰', '원블', '링블', '업체로부터',
    '제공받았습니다', '대가로', '파트너스', '수수료', '공정거래위원회', '공정위'
]

# 협찬 URL 키워드
SPONSORSHIP_URL_KEYWORDS = [
    'revu.net', 'seoulouba.co.kr', 'dinnerqueen.net', 'reviewnote.co.kr',
    '가보자체험단.com', 'mrblog.net', 'reviewplace.co.kr', 'supermembers.co.kr',
    'ringview.co.kr', 'ringble.co.kr', 'assaview.co.kr'
]

# 페이지당 게시물 수
POSTS_PER_PAGE = 6

def clean_html_tags(text):
    """HTML 태그 제거"""
    if not text:
        return ""
    # <b>, </b> 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def is_sponsored_content(title, description, url):
    """제목, 설명, URL을 기반으로 협찬 여부 판단"""
    
    # 모든 텍스트를 소문자로 변환하여 검사
    content_text = f"{title} {description}".lower()
    url_lower = url.lower()
    
    # 1. 텍스트에서 협찬 키워드 확인
    for keyword in SPONSORSHIP_KEYWORDS:
        if keyword.lower() in content_text:
            return True
    
    # 2. URL에서 협찬 키워드 확인
    for url_keyword in SPONSORSHIP_URL_KEYWORDS:
        if url_keyword.lower() in url_lower:
            return True
    
    return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return {
        "status": "ok",
        "message": "블로그 분석 API",
        "api_ready": bool(client_id and client_secret)
    }

@app.route('/api/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()
        page = int(data.get('page', 1))
        include_sponsored = data.get('includeSponsored', False)
        
        if not keyword:
            return jsonify({"error": "키워드를 입력해주세요"}), 400
            
        if not client_id or not client_secret:
            return jsonify({"error": "네이버 API 키가 설정되지 않았습니다"}), 500

        print(f"🔍 검색 시작: '{keyword}' (페이지: {page}, 협찬글 포함: {include_sponsored})")

        # 더 많은 데이터를 가져오기 위해 여러 페이지 검색
        all_posts = []
        sponsored_count = 0
        
        # 최대 3페이지까지 검색 (총 60개 게시물)
        for search_page in range(1, 4):
            start_num = (search_page - 1) * 20 + 1
            
            # 네이버 API 호출
            url = f"https://openapi.naver.com/v1/search/blog?query={urllib.parse.quote(keyword)}&start={start_num}&display=20"
            req = urllib.request.Request(url)
            req.add_header("X-Naver-Client-Id", client_id)
            req.add_header("X-Naver-Client-Secret", client_secret)
            
            try:
                res = urllib.request.urlopen(req)
                result = json.loads(res.read().decode('utf-8'))
                
                for item in result.get('items', []):
                    # HTML 태그 제거
                    title = clean_html_tags(item.get('title', ''))
                    description = clean_html_tags(item.get('description', ''))
                    blog_url = item.get('link', '')
                    author = item.get('bloggername', '네이버 블로거')
                    post_date = item.get('postdate', '')
                    
                    # 네이버 블로그만 필터링
                    if 'blog.naver.com' not in blog_url:
                        continue
                    
                    # 날짜 형식 변환 (YYYYMMDD → YYYY-MM-DD)
                    if post_date and len(post_date) == 8:
                        formatted_date = f"{post_date[:4]}-{post_date[4:6]}-{post_date[6:8]}"
                    else:
                        formatted_date = post_date
                    
                    # 협찬 여부 체크
                    is_sponsored = is_sponsored_content(title, description, blog_url)
                    
                    if is_sponsored:
                        sponsored_count += 1
                    
                    post = {
                        "title": title or "제목 없음",
                        "url": blog_url,
                        "author": author,
                        "date": formatted_date,
                        "is_sponsored": is_sponsored
                    }
                    
                    all_posts.append(post)
                    
            except Exception as api_error:
                print(f"API 호출 오류 (페이지 {search_page}): {api_error}")
                continue

        # 중복 URL 제거
        seen_urls = set()
        unique_posts = []
        for post in all_posts:
            if post['url'] not in seen_urls:
                seen_urls.add(post['url'])
                unique_posts.append(post)

        # 협찬글 포함 여부에 따라 필터링
        if include_sponsored:
            filtered_posts = unique_posts
        else:
            filtered_posts = [post for post in unique_posts if not post['is_sponsored']]

        # 페이지네이션 적용
        total_posts = len(filtered_posts)
        total_pages = ceil(total_posts / POSTS_PER_PAGE) if total_posts > 0 else 1
        
        start_index = (page - 1) * POSTS_PER_PAGE
        end_index = start_index + POSTS_PER_PAGE
        
        paginated_posts = filtered_posts[start_index:end_index]

        print(f"✅ 검색 완료: 전체 {len(unique_posts)}개, 협찬 {sponsored_count}개, 필터링 후 {total_posts}개, 현재 페이지 {len(paginated_posts)}개")

        return jsonify({
            "status": "success", 
            "results": paginated_posts,
            "total_posts": total_posts,
            "total_pages": total_pages,
            "sponsored_count": sponsored_count,  # 전체 협찬글 수
            "current_page": page
        })
        
    except Exception as e:
        print(f"❌ 검색 오류: {e}")
        return jsonify({"error": f"검색 중 오류가 발생했습니다: {str(e)}"}), 500

@app.route('/health')
def health():
    return {"status": "ok"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import urllib.request
import os

app = Flask(__name__)
CORS(app)

# API 키
client_id = os.environ.get('NAVER_CLIENT_ID')
client_secret = os.environ.get('NAVER_CLIENT_SECRET')

# 협찬 키워드
KEYWORDS = ['협찬', '제공받아', '원고료', '리뷰노트', '체험단', 'revu', '제공받고', '소정의', '지원받아', '유료광고']

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
        include_sponsored = data.get('includeSponsored', False)
        
        if not keyword:
            return {"error": "키워드를 입력해주세요"}, 400
            
        if not client_id or not client_secret:
            return {"error": "네이버 API 키가 설정되지 않았습니다"}, 500

        print(f"🔍 검색 시작: '{keyword}' (협찬글 포함: {include_sponsored})")

        # 네이버 API 호출
        url = f"https://openapi.naver.com/v1/search/blog?query={urllib.parse.quote(keyword)}&display=20"
        req = urllib.request.Request(url)
        req.add_header("X-Naver-Client-Id", client_id)
        req.add_header("X-Naver-Client-Secret", client_secret)
        
        res = urllib.request.urlopen(req)
        result = json.loads(res.read().decode('utf-8'))
        
        all_posts = []
        sponsored_count = 0
        
        for item in result.get('items', []):
            title = item.get('title', '').replace('<b>', '').replace('</b>', '')
            desc = item.get('description', '').replace('<b>', '').replace('</b>', '')
            
            # 네이버 블로그만 필터링
            if 'blog.naver.com' not in item.get('link', ''):
                continue
            
            # 협찬 여부 체크
            content = f"{title} {desc}".lower()
            is_sponsored = any(k in content for k in KEYWORDS)
            
            if is_sponsored:
                sponsored_count += 1
            
            post = {
                "title": title,
                "url": item.get('link', ''),
                "author": item.get('bloggername', '네이버 블로거'),
                "is_sponsored": is_sponsored
            }
            
            all_posts.append(post)

        # 필터링
        if include_sponsored:
            final_posts = all_posts
        else:
            final_posts = [post for post in all_posts if not post['is_sponsored']]

        print(f"✅ 검색 완료: 전체 {len(all_posts)}개, 협찬 {sponsored_count}개, 결과 {len(final_posts)}개")

        return {
            "status": "success", 
            "results": final_posts,
            "total_posts": len(final_posts),
            "sponsored_count": sponsored_count
        }
        
    except Exception as e:
        print(f"❌ 검색 오류: {e}")
        return {"error": f"검색 중 오류가 발생했습니다: {str(e)}"}, 500

@app.route('/health')
def health():
    return {"status": "ok"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import urllib.request
import os

app = Flask(__name__)
CORS(app)

# API 키
client_id = os.environ.get('NAVER_CLIENT_ID')
client_secret = os.environ.get('NAVER_CLIENT_SECRET')

# 협찬 키워드 (최소한)
KEYWORDS = ['협찬', '제공받아', '원고료', '리뷰노트', '체험단', 'revu']

@app.route('/')
def home():
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
        
        if not keyword:
            return {"error": "키워드 필요"}, 400
            
        if not client_id:
            return {"error": "API 키 없음"}, 500

        # 네이버 API 호출
        url = f"https://openapi.naver.com/v1/search/blog?query={urllib.parse.quote(keyword)}&display=10"
        req = urllib.request.Request(url)
        req.add_header("X-Naver-Client-Id", client_id)
        req.add_header("X-Naver-Client-Secret", client_secret)
        
        res = urllib.request.urlopen(req)
        result = json.loads(res.read().decode('utf-8'))
        
        posts = []
        for item in result.get('items', []):
            title = item.get('title', '').replace('<b>', '').replace('</b>', '')
            desc = item.get('description', '').replace('<b>', '').replace('</b>', '')
            
            # 간단한 협찬 체크
            is_sponsored = any(k in f"{title} {desc}".lower() for k in KEYWORDS)
            
            posts.append({
                "title": title,
                "url": item.get('link', ''),
                "author": item.get('bloggername', ''),
                "is_sponsored": is_sponsored
            })
        
        return {"status": "success", "results": posts}
        
    except Exception as e:
        return {"error": str(e)}, 500

@app.route('/health')
def health():
    return {"status": "ok"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

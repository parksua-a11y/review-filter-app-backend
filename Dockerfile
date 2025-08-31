FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 업데이트 및 기본 도구 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# 포트 설정
EXPOSE 8000

# 애플리케이션 실행
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]

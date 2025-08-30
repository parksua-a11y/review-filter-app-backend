FROM python:3.11-slim

WORKDIR /app

# 빌드에 필요한 모든 시스템 라이브러리 설치
# opencv, tensorflow, easyocr을 위한 핵심 종속성
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    zlib1g-dev \
    libwebp-dev \
    tesseract-ocr \
    libleptonica-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# requirements.txt 파일에 명시된 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 컨테이너 포트 설정
EXPOSE 8000

# Gunicorn 실행 명령어
# 파이썬 인터프리터를 명시적으로 지정하여 환경 충돌 방지
CMD ["python3", "-m", "gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
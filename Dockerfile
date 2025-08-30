FROM python:3.11-slim

WORKDIR /app

# 빌드 및 런타임에 필요한 모든 시스템 라이브러리 설치
# opencv-python-headless, tensorflow, easyocr을 위한 핵심 종속성 포함
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    zlib1g-dev \
    libwebp-dev \
    tesseract-ocr \
    libleptonica-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 파이썬 인터프리터를 명시적으로 지정하여 환경 충돌 방지
CMD ["python3", "-m", "gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
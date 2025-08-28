# 경량화된 Python 베이스 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 기본 빌드 도구
    gcc \
    g++ \
    make \
    # OpenCV 의존성
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    # 네트워크 도구
    curl \
    wget \
    # Chrome 브라우저 의존성
    gnupg \
    unzip \
    xvfb \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Google Chrome 설치 (headless 모드용)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver 설치
RUN CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1) \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}") \
    && wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" \
    && unzip chromedriver_linux64.zip \
    && rm chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver

# pip 업그레이드
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .

# Python 의존성을 단계별로 설치 (빌드 안정성 향상)
RUN pip install --no-cache-dir --only-binary=all \
    Flask==2.3.3 \
    Flask-CORS==4.0.0 \
    requests==2.31.0 \
    beautifulsoup4==4.12.2 \
    gunicorn==21.2.0

# OpenCV와 numpy 설치 (headless 버전)
RUN pip install --no-cache-dir \
    opencv-python-headless==4.8.1.78 \
    numpy==1.24.3

# Selenium 설치
RUN pip install --no-cache-dir selenium==4.15.0

# TensorFlow CPU 버전 설치 (더 가벼움)
RUN pip install --no-cache-dir tensorflow-cpu==2.13.0

# 나머지 의존성 설치
RUN pip install --no-cache-dir \
    easyocr==1.7.0 \
    thefuzz==0.20.0

# 애플리케이션 파일 복사
COPY . .

# 애플리케이션용 사용자 생성
RUN groupadd -r app && useradd -r -g app app \
    && chown -R app:app /app

# 사용자 전환
USER app

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DISPLAY=:99
ENV PORT=8000

# 포트 노출
EXPOSE 8000

# 헬스 체크 (간소화)
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# 애플리케이션 실행
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 1 --timeout 300 --max-requests 1000 --max-requests-jitter 100 app:app"]
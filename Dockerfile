FROM python:3.9-slim

WORKDIR /app

RUN pip install --upgrade pip setuptools wheel
COPY requirements.txt .

RUN apt-get update && apt-get install -y build-essential libgl1-mesa-glx && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
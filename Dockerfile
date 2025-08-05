FROM python:3.9-slim

WORKDIR /app

# Sistem bağımlılıklarını yükle
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    fonts-dejavu-core \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıklarını kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# Port ayarı
EXPOSE 8080

# Uygulamayı çalıştır - Yeni bot token ile
CMD ["sh", "-c", "killall python || true && pkill -f python || true && ps aux | grep python | awk '{print $2}' | xargs kill -9 || true && sleep 60 && python app.py"] 
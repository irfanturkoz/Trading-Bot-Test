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
CMD ["sh", "-c", "pkill -9 -f 'python.*app.py' || true && pkill -9 -f 'telebot' || true && sleep 120 && python app.py"] 
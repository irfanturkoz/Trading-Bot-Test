import os

print("🔍 Railway Environment Variables Debug")
print("=" * 50)

# Bot token'ını kontrol et
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
print(f"📝 TELEGRAM_BOT_TOKEN: {bot_token[:20] if bot_token else 'None'}...")

# Admin chat ID'yi kontrol et
admin_id = os.getenv('ADMIN_CHAT_ID')
print(f"📝 ADMIN_CHAT_ID: {admin_id}")

# Tüm environment variables'ları listele
print("\n🔍 Tüm Environment Variables:")
for key, value in os.environ.items():
    if 'TELEGRAM' in key or 'ADMIN' in key:
        print(f"  {key}: {value[:20] if value else 'None'}...")

print("\n✅ Debug tamamlandı!") 
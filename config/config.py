import discord
import configparser
import os

def get_token():
    config = configparser.ConfigParser()
    config.read('sifrelenmistoken.ini')

    try:
        token = config['Discord']['TOKEN']
    except KeyError:
        raise ValueError("sifrelenmistoken.ini dosyasından TOKEN alınamadı. 'discord' bölümü veya 'TOKEN' anahtarı eksik.")

    if not token:
        raise ValueError("TOKEN boş geldi. Lütfen sifrelenmistoken.ini dosyasını kontrol edin.")

    return token

# Kanal ID'leri
BAN_LOG_KANAL_ID = 1281700459991666748
WARN_LOG_KANAL_ID = 1281700488156414102
TIMEOUT_LOG_KANAL_ID = 1281700527473819699
MESSAGE_LOG_KANAL_ID = 1281700552929185882
USER_LOG_KANAL_ID = 1359645505948221572
VOICE_LOG_KANAL_ID = 1359645396330090617
WELCOME_CHANNEL_ID = 1267938558250057909

# Seviye rol ID'leri
LEVEL_ROLES = {
    1: 1267945080132603934,   # Seviye 1
    5: 1267945082510639225,   # Seviye 5
    10: 1267945084532428860,  # Seviye 10
    20: 1267945086315003965,  # Seviye 20
    25: 1267945087741198540,  # Seviye 25
    30: 1267945089498615912,  # Seviye 30
    40: 1267945091029405807,  # Seviye 40
    50: 1267945092283629639   # Seviye 50
}

# Rol ID'leri
IZIN_VERILEN_ROLLER = [1267942292711276645, 1267942295093907456, 1267942293277642804]
YASAKLI = 1357413870226112624

# Bot intentleri
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True
INTENTS.presences = True

# Embed Rengi
EMBED_COLOR = 0x8B008B

# Otomatik Mesaj Kanalı
AUTO_MESSAGE_CHANNEL = 1371057475058401380

# Dashboard için OAuth2 bilgileri
OAUTH2 = {
    "client_id": "1357403500761452675",  # Discord Developer Portal'dan alın
    "client_secret": "OkEiJYmhzqjFiZeGYX9iU_3YmGs3dIb0",  # Discord Developer Portal'dan alın
    "redirect_uri": "http://localhost:8080/callback"
}

def get_oauth_creds():
    """Dashboard için OAuth bilgilerini döndürür"""
    return OAUTH2

# Dashboard OAuth2 Configuration
DASHBOARD_CLIENT_ID = "1357403500761452675"  # Discord Developer Portal'dan alınan Client ID
DASHBOARD_CLIENT_SECRET = "OkEiJYmhzqjFiZeGYX9iU_3YmGs3dIb0"  # Discord Developer Portal'dan alınan Client Secret
DASHBOARD_REDIRECT_URI = "http://localhost:8080/callback"  # OAuth2 yönlendirme URI'si
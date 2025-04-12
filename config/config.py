import discord
import configparser
import os

def get_token():
    # TOKEN çevresel değişkenini al
    my_secret = os.environ['TOKEN']

    if not my_secret:
        raise ValueError("Token environment variable'ı bulunamadı. Lütfen Replit Secrets üzerinden ekleyin.")
    
    return my_secret

# Kanal ID'leri
BAN_LOG_KANAL_ID = 1281700459991666748
WARN_LOG_KANAL_ID = 1281700488156414102
TIMEOUT_LOG_KANAL_ID = 1281700527473819699
MESSAGE_LOG_KANAL_ID = 1281700552929185882
USER_LOG_KANAL_ID = 1359645505948221572
VOICE_LOG_KANAL_ID = 1359645396330090617

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
AUTO_MESSAGE_CHANNEL = 1292912455390855233
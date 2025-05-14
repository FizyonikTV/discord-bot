import discord
import os
from dotenv import load_dotenv

# Çevre değişkenlerini yükle
load_dotenv()

# Bot token'ını al
def get_token():
    """Bot token'ını .env dosyasından alır"""
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN çevre değişkeni bulunamadı! .env dosyası oluşturun.")
    return token

# Log kanalları
MESSAGE_LOG_KANAL_ID = int(os.environ.get("MESSAGE_LOG_CHANNEL", "0"))
WARN_LOG_KANAL_ID = int(os.environ.get("WARN_LOG_CHANNEL", "0"))
BAN_LOG_KANAL_ID = int(os.environ.get("BAN_LOG_CHANNEL", "0"))
TIMEOUT_LOG_KANAL_ID = int(os.environ.get("TIMEOUT_LOG_CHANNEL", "0"))
USER_LOG_KANAL_ID = int(os.environ.get("USER_LOG_CHANNEL", "0"))
VOICE_LOG_KANAL_ID = int(os.environ.get("VOICE_LOG_CHANNEL", "0"))
WELCOME_CHANNEL_ID = int(os.environ.get("WELCOME_CHANNEL_ID", "0"))


GAME_WEBHOOK_URL = os.environ.get("GAME_WEBHOOK_URL", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# Komut kanalları
COMMAND_CHANNELS = [
    1267944262067134464,  # BOT KOMUT
    1267944263858065479,  # Yetkili Komut
]

# Seviye Rolleri
LEVEL_ROLES = {
    5: 1267945078651887736,    # Seviye 5
    10: 1267945080933152839,   # Seviye 10
    15: 1267945082992992380,   # Seviye 15
    20: 1267945086315003965,   # Seviye 20
    25: 1267945087741198540,   # Seviye 25
    30: 1267945089498615912,   # Seviye 30
    40: 1267945091029405807,   # Seviye 40
    50: 1267945092283629639    # Seviye 50
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
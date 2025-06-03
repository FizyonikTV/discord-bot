import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Console encoding ayarlama (Windows için)
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Log klasörü
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Bugünün tarihi
today = datetime.now().strftime("%Y-%m-%d")

# Log formatı
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Console handler (debugging için)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.WARNING)  # Sadece WARNING ve üzeri console'a yazsın

# Bot log dosyası (rotating) - UTF-8 encoding ile
bot_handler = RotatingFileHandler(
    f"{log_dir}/bot_{today}.log",
    maxBytes=5*1024*1024,  # 5 MB
    backupCount=10,
    encoding='utf-8'
)
bot_handler.setFormatter(formatter)

# Komut log dosyası - UTF-8 encoding ile
cmd_handler = RotatingFileHandler(
    f"{log_dir}/commands_{today}.log",
    maxBytes=2*1024*1024,  # 2 MB
    backupCount=5,
    encoding='utf-8'
)
cmd_handler.setFormatter(formatter)

# Hata log dosyası - UTF-8 encoding ile
error_handler = RotatingFileHandler(
    f"{log_dir}/errors_{today}.log", 
    maxBytes=2*1024*1024,  # 2 MB
    backupCount=5,
    encoding='utf-8'
)
error_handler.setFormatter(formatter)

# Dashboard log dosyası - UTF-8 encoding ile
dashboard_handler = RotatingFileHandler(
    f"{log_dir}/dashboard_{today}.log",
    maxBytes=2*1024*1024,  # 2 MB
    backupCount=5,
    encoding='utf-8'
)
dashboard_handler.setFormatter(formatter)

# Ana bot logger'ı
bot_logger = logging.getLogger('bot')
bot_logger.setLevel(logging.INFO)
bot_logger.addHandler(bot_handler)
bot_logger.addHandler(console_handler)

# Komut logger'ı
cmd_logger = logging.getLogger('commands')
cmd_logger.setLevel(logging.INFO)
cmd_logger.addHandler(cmd_handler)

# Hata logger'ı
error_logger = logging.getLogger('errors')
error_logger.setLevel(logging.ERROR)
error_logger.addHandler(error_handler)
error_logger.addHandler(console_handler)

# Dashboard logger'ı
dashboard_logger = logging.getLogger('dashboard')
dashboard_logger.setLevel(logging.INFO)
dashboard_logger.addHandler(dashboard_handler)
dashboard_logger.addHandler(console_handler)

# Loggerları dışa aktar
def get_bot_logger():
    return bot_logger

def get_cmd_logger():
    return cmd_logger

def get_error_logger():
    return error_logger

def get_dashboard_logger():
    return dashboard_logger

# Log fonksiyonları
def log_command(ctx, success=True):
    """Komut çalıştırma logları"""
    cmd_logger.info(
        f"USER: {ctx.author} ({ctx.author.id}) | "
        f"CMD: {ctx.command} | "
        f"ARGS: {ctx.args[2:] if len(ctx.args) > 2 else 'N/A'} | "
        f"GUILD: {ctx.guild.name} ({ctx.guild.id}) | "
        f"CHANNEL: #{ctx.channel.name} ({ctx.channel.id}) | "
        f"STATUS: {'SUCCESS' if success else 'FAILED'}"
    )

def log_error(error, ctx=None):
    """Hata logları"""
    if ctx:
        error_logger.error(
            f"ERROR: {error} | "
            f"USER: {ctx.author} ({ctx.author.id}) | "
            f"CMD: {ctx.command} | "
            f"GUILD: {ctx.guild.name} ({ctx.guild.id})"
        )
    else:
        error_logger.error(f"ERROR: {error}")

# Logger'da emoji kullanımını değiştirin
def log_event(message, success=True):
    """Olay logları"""
    status = "[✅]" if success else "[❌]"
    bot_logger.info(f"{status} {message}")
import discord
from discord.ext import commands
import asyncio
import os
import logging
from datetime import datetime, timezone
from config.config import get_token, INTENTS, IZIN_VERILEN_ROLLER
from utils.helpers import command_check, COMMAND_CHANNELS
from dotenv import load_dotenv
from utils.logger import get_bot_logger, get_cmd_logger, log_command, log_error
from utils.shared_models import SharedDataManager

# Çevre değişkenlerini yükle
load_dotenv()

# Loggerları al
bot_logger = get_bot_logger()
cmd_logger = get_cmd_logger()

class LunarisBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=INTENTS,
            case_insensitive=True
        )
        self.start_time = datetime.now(timezone.utc)
        bot_logger.info("Bot başlatılıyor...")
        self.shared_data = SharedDataManager(self)  # Ortak veri modelini ekle

    async def add_cog(self, cog):
        """Cogları kontrol eder"""
        for cmd in cog.get_commands():
            cmd.add_check(command_check())
        await super().add_cog(cog)
        
    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Log komutları çalıştırıldığında."""
        log_command(ctx)
        
    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        """Log başarılı komutları."""
        log_command(ctx, success=True)
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Log komut hatalarını."""
        log_command(ctx, success=False)
        log_error(error, ctx)

    async def setup_hook(self):
        # Hata yakalama sistemini ilk yükle
        try:
            await self.load_extension("utils.error_handler")
            bot_logger.info("[✅] Error handler yüklendi")
            print("[✅] Error handler yüklendi")
        except Exception as e:
            bot_logger.error(f"[❌] Error handler yüklenemedi: {e}")
            print(f"[❌] Error handler yüklenemedi: {e}")        # Diğer cog'ları yükle
        cogs_to_load = [f for f in os.listdir('./cogs') if f.endswith('.py') and not f.startswith('__')]
        # Sorunlu cog'ları atla
        skip_cogs = [''] 
        cogs_to_load = [cog for cog in cogs_to_load if cog not in skip_cogs]
        
        # Öncelikli cog'ları belirle - Notes ve AI enhanced fixed önce yüklensin
        priority_cogs = ['notes.py', 'ai_chat.py']
        other_cogs = [cog for cog in cogs_to_load if cog not in priority_cogs]
        ordered_cogs = priority_cogs + other_cogs
        
        bot_logger.info(f"Yüklenecek {len(ordered_cogs)} cog bulundu")
        print(f"Yüklenecek {len(ordered_cogs)} cog bulundu")
        
        for filename in ordered_cogs:
            try:
                print(f"Yüklemeye çalışılıyor: {filename}...")
                await self.load_extension(f'cogs.{filename[:-3]}')
                bot_logger.info(f'[✅] Yüklenen özellik: {filename}')
                print(f'[✅] Yüklenen özellik: {filename}')
            except Exception as e:
                bot_logger.error(f'[❌] Özellik yüklenemedi {filename}: {e}')
                print(f'[❌] Özellik yüklenemedi {filename}: {e}')
                import traceback
                log_error(f"Cog yükleme hatası {filename}: {e}")
                traceback.print_exc()

    async def on_ready(self):
        """Triggered when the bot is ready."""
        bot_logger.info(f"[✅] Bot {self.user} olarak giriş yaptı!")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.streaming,
                name="🦊 LunarisBot | Moderasyon Botu",
                url="https://www.kick.com/eonjinwoo"
            )
        )
        print(f'[✅] Bot {self.user} olarak giriş yaptı!')

async def main():
    """Botan başlatma fonksiyonu."""
    token = get_token()

    async with LunarisBot() as bot:
        # Botu başlat
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
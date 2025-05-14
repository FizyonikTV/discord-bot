import discord
from discord.ext import commands
import asyncio
import os
import logging
from datetime import datetime, timezone
from config.config import get_token, INTENTS, IZIN_VERILEN_ROLLER
from utils.helpers import command_check, COMMAND_CHANNELS
from webdashboard import Dashboard
from dotenv import load_dotenv
from utils.logger import get_bot_logger, get_cmd_logger, log_command, log_error

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

    async def add_cog(self, cog):
        """Add checks to all commands in a cog."""
        for cmd in cog.get_commands():
            cmd.add_check(command_check())
        await super().add_cog(cog)
        
    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Log commands when they are triggered."""
        log_command(ctx)
        
    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        """Log successful commands."""
        log_command(ctx, success=True)
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Log command errors."""
        log_command(ctx, success=False)
        log_error(error, ctx)

    async def setup_hook(self):
        # Hata yakalama sistemini ilk yükle
        try:
            await self.load_extension("utils.error_handler")
            bot_logger.info("[OK] Error handler yüklendi")
            print("[OK] Error handler yüklendi")
        except Exception as e:
            bot_logger.error(f"[NO] Error handler yüklenemedi: {e}")
            print(f"[NO] Error handler yüklenemedi: {e}")
        
        # Diğer cog'ları yükle
        cogs_to_load = [f for f in os.listdir('./cogs') if f.endswith('.py') and not f.startswith('__')]
        
        # Sorunlu cog'ları atla
        skip_cogs = ['image_mod.py']
        cogs_to_load = [cog for cog in cogs_to_load if cog not in skip_cogs]
        
        # Öncelikli cog'ları belirle - Notes önce yüklensin
        priority_cogs = ['notes.py']
        other_cogs = [cog for cog in cogs_to_load if cog not in priority_cogs]
        ordered_cogs = priority_cogs + other_cogs
        
        bot_logger.info(f"Yüklenecek {len(ordered_cogs)} cog bulundu")
        print(f"Yüklenecek {len(ordered_cogs)} cog bulundu")
        
        for filename in ordered_cogs:
            try:
                print(f"Yüklemeye çalışılıyor: {filename}...")
                await self.load_extension(f'cogs.{filename[:-3]}')
                bot_logger.info(f'[OK] Loaded cog: {filename}')
                print(f'[OK] Loaded cog: {filename}')
            except Exception as e:
                bot_logger.error(f'[NO] Failed to load cog {filename}: {e}')
                print(f'[NO] Failed to load cog {filename}: {e}')
                import traceback
                log_error(f"Cog yükleme hatası {filename}: {e}")
                traceback.print_exc()
        
        # Dashboard başlatma
        try:
            print("Dashboard başlatılıyor...")
            
            # .env dosyasından yapılandırma al
            dashboard_config = {
                "client_id": os.environ.get("DISCORD_CLIENT_ID"),
                "client_secret": os.environ.get("DISCORD_CLIENT_SECRET"), 
                "redirect_uri": os.environ.get("DISCORD_REDIRECT_URI"),
                "base_url": os.environ.get("DASHBOARD_BASE_URL"),
                "port": int(os.environ.get("DASHBOARD_PORT", 8080))
            }
            
            # Dashboard'u başlat
            self.dashboard = Dashboard(
                bot=self,
                client_id=dashboard_config["client_id"],
                client_secret=dashboard_config["client_secret"],
                base_url=dashboard_config["base_url"],
                port=dashboard_config["port"],
                redirect_uri=dashboard_config["redirect_uri"]
            )
            
            # Dashboard başlatma fonksiyonunu çağır
            await self.dashboard.start()
            print("[OK] Dashboard başarıyla başlatıldı!")
        except Exception as e:
            import traceback
            print(f"[NO] Dashboard başlatılamadı: {e}")
            traceback.print_exc()

    async def on_ready(self):
        """Triggered when the bot is ready."""
        bot_logger.info(f"[OK] Bot is ready as {self.user}")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.streaming,
                name="🦊 LunarisBot | Moderasyon Botu",
                url="https://www.twitch.tv/eonjinwoo"
            )
        )
        print(f'[OK] Bot {self.user} olarak giriş yaptı!')

async def main():
    """Main entry point for the bot."""
    token = get_token()

    async with LunarisBot() as bot:
        # Start the bot
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
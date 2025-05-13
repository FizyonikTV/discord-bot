import discord
from discord.ext import commands
import re
import os
import json
from datetime import datetime
from config.config import WARN_LOG_KANAL_ID

class ImageMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.automod = None
    
    async def cog_load(self):
        """AutoMod sınıfına erişim sağla"""
        await self.bot.wait_until_ready()
        self.automod = self.bot.get_cog("AutoMod")
        
    # Basit bir görsel kontrol fonksiyonu
    async def check_image_filename(self, message):
        """Mesajdaki resimleri kontrol et (basit kontrol)"""
        if message.author.bot or not self.automod or self.automod.is_exempt(message):
            return
            
        # Mesajda ek varsa kontrol et
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                # Dosya adı kontrolü (basit örnek)
                if any(bad_term in attachment.filename.lower() for bad_term in ['uygunsuz', 'nsfw', 'adult']):
                    try:
                        await message.delete()
                        await self.automod.add_violation(message.author.id, f"Uygunsuz dosya adı")
                        
                        # Kullanıcıya uyarı mesajı gönder
                        violation_count = self.automod.get_violation_count(message.author.id)
                        await self.automod.send_warning_message(
                            message.author,
                            "uygunsuz görsel",
                            violation_count,
                            message.guild
                        )
                        
                        # Log kanalına bildir
                        await self.automod.log_moderation_action(
                            message.guild, 
                            message.author,
                            "Uygunsuz Görsel Silindi", 
                            f"Dosya adı uygunsuz: {attachment.filename}", 
                            None, 
                            WARN_LOG_KANAL_ID
                        )
                    except Exception as e:
                        print(f"Görsel moderasyon hatası: {e}")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Mesajdaki resimleri kontrol et"""
        await self.check_image_filename(message)

async def setup(bot):
    await bot.add_cog(ImageMod(bot))
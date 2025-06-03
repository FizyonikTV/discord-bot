import discord
import traceback
import sys
from discord.ext import commands
import logging

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("[⚠️] Hata yakalama sistemi yüklendi.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        Global hata işleyici
        Tüm komut hatalarını yakalayıp uygun şekilde işler
        """
        # Eğer bir CheckFailure hatası ise (izin hataları)
        if isinstance(error, commands.CheckFailure):
            return await ctx.send("❌ Bu komutu kullanma izniniz yok.")
        
        # Eğer komut bulunamazsa ve yakın komut varsa öner
        elif isinstance(error, commands.CommandNotFound):
            return  # Komut bulunamadı hatalarını görmezden gel
        
        # Komutun beklediği argümanlar eksikse
        elif isinstance(error, commands.MissingRequiredArgument):
            param = error.param.name
            return await ctx.send(f"❌ Eksik argüman: `{param}`. Doğru kullanım için `!yardım {ctx.command}` yazın.")
            
        # Argüman dönüştürme hatası (örn. sayı yerine yazı)
        elif isinstance(error, commands.BadArgument):
            return await ctx.send(f"❌ Geçersiz argüman. Doğru kullanım için `!yardım {ctx.command}` yazın.")
        
        # Kullanım hatası (örn. yanlış parametre sırası)
        elif isinstance(error, commands.UserInputError):
            return await ctx.send(f"❌ Komut kullanımında hata. Doğru kullanım için `!yardım {ctx.command}` yazın.")
        
        # Komutun cooldown süresi dolmadıysa
        elif isinstance(error, commands.CommandOnCooldown):
            seconds = round(error.retry_after)
            return await ctx.send(f"❌ Bu komutu çok sık kullanıyorsunuz. {seconds} saniye sonra tekrar deneyin.")
        
        # Discord API hataları
        elif isinstance(error, discord.HTTPException):
            return await ctx.send(f"❌ Discord API hatası: {error.status} - {error.text}")
        
        # Discord izin hataları
        elif isinstance(error, discord.Forbidden):
            return await ctx.send("❌ Bu işlemi gerçekleştirmek için yetkim yok.")
            
        # Komut içinde ortaya çıkan diğer hatalar
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            
            # Log hatayı
            logging.error(f"Komut çalıştırılırken hata: {original}")
            print(f"Komut hatası: {original}")
            traceback.print_exception(type(original), original, original.__traceback__, file=sys.stderr)
            
            # Kullanıcıya bildirim gönder
            error_embed = discord.Embed(
                title="❌ Komut Hatası", 
                description="Komut çalıştırılırken bir hata oluştu.",
                color=discord.Color.red()
            )
            error_embed.add_field(
                name="Hata Tipi",
                value=f"`{type(original).__name__}`",
                inline=False
            )
            error_embed.add_field(
                name="Hata Mesajı",
                value=f"```{str(original)}```",
                inline=False
            )
            
            await ctx.send(embed=error_embed)
            
        else:
            # Bilinmeyen hatalar için
            logging.error(f"Bilinmeyen hata: {error}")
            print(f"Bilinmeyen hata: {error}")
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            await ctx.send("❌ Bilinmeyen bir hata oluştu.")

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
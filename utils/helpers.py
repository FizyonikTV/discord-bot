import discord
from discord.ext import commands
from datetime import datetime
from config.config import (
    BAN_LOG_KANAL_ID, 
    WARN_LOG_KANAL_ID, 
    TIMEOUT_LOG_KANAL_ID,
    MESSAGE_LOG_KANAL_ID,
    EMBED_COLOR,
    IZIN_VERILEN_ROLLER
)

COMMAND_CHANNELS = [
    1357419585678086195,
    1267939573976268930,
    1267940282947604531
]

def izin_kontrol(ctx):
    """Kullanıcının yetkili rollerine sahip olup olmadığını kontrol eder"""
    return any(role.id in IZIN_VERILEN_ROLLER for role in ctx.author.roles)

def command_check():
    async def predicate(ctx):
        # Komut kanalı kontrolü
        if ctx.channel.id not in COMMAND_CHANNELS:
            await ctx.message.delete()
            await ctx.send("❌ Bu komutu sadece komut kanallarında kullanabilirsiniz!", delete_after=5)
            return False
            
        # Return True if the check passes
        return True
    return predicate  # Return the predicate function, not commands.check(predicate)

def create_embed(title, description, color=EMBED_COLOR, thumbnail_url=None):
    """Standart embed oluşturma yardımcısı"""
    embed = discord.Embed(title=title, description=description, color=color)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="LunarisBot | Daha fazla bilgi için yöneticilere ulaşın.")
    return embed

async def send_log(bot, channel_id, embed):
    """Log gönderme yardımcısı"""
    channel = bot.get_channel(channel_id)
    if channel:
        try:
            await channel.send(embed=embed)
            return True
        except discord.Forbidden:
            print(f"❌ Log kanalına mesaj gönderme yetkisi yok: {channel_id}")
        except Exception as e:
            print(f"❌ Log gönderilirken hata oluştu: {e}")
    return False

async def log_handler(bot, log_type, **kwargs):
    log_channels = {
        'ban': BAN_LOG_KANAL_ID,
        'warn': WARN_LOG_KANAL_ID,
        'timeout': TIMEOUT_LOG_KANAL_ID,
        'message': MESSAGE_LOG_KANAL_ID
    }
    
    channel = bot.get_channel(log_channels.get(log_type))
    if not channel:
        return
    
    embed = discord.Embed(
        title=f"{log_type.title()} Log",
        color=EMBED_COLOR,
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(name="Kullanıcı", value=kwargs.get('user', 'Bilinmiyor'), inline=False)
    embed.add_field(name="Moderatör", value=kwargs.get('moderator', 'Bilinmiyor'), inline=False)
    embed.add_field(name="Sebep", value=kwargs.get('reason', 'Sebep belirtilmedi'), inline=False)
    
    await channel.send(embed=embed)

def format_duration(seconds):
    """Süreyi formatlama yardımcısı"""
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}g")
    if hours > 0:
        parts.append(f"{hours}s")
    if minutes > 0:
        parts.append(f"{minutes}d")
    if seconds > 0:
        parts.append(f"{seconds}s")
    return " ".join(parts) if parts else "0s"
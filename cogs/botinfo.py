import discord
from discord.ext import commands
import platform
import psutil
import datetime
from config.config import IZIN_VERILEN_ROLLER
from utils.permissions import has_mod_role, has_admin

def has_required_role():
    async def predicate(ctx):
        return any(role.id in IZIN_VERILEN_ROLLER for role in ctx.author.roles)
    return commands.check(predicate)

class BotInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.datetime.utcnow()

    @commands.command(name="botinfo")
    @has_mod_role()
    async def botinfo(self, ctx):
        # Bot uptime hesaplama
        uptime = datetime.datetime.utcnow() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}s {minutes}d {seconds}s"

        # Sistem bilgilerini alma
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_usage = memory.percent

        embed = discord.Embed(
            title="✨ Bot Bilgileri ve Sistem Durumu",
            description="Botun detaylı bilgileri ve sistem istatistikleri aşağıda listelenmiştir.",
            color=discord.Color.from_rgb(114, 137, 218),  # Discord'un klasik mor rengi
            timestamp=datetime.datetime.utcnow()
        )

        embed.add_field(
            name="🤖 Bot Detayları",
            value=f"```yml\n"
                  f"İsim: {self.bot.user.name}\n"
                  f"ID: {self.bot.user.id}\n"
                  f"Çalışma Süresi: {uptime_str}\n"
                  f"Ping: {round(self.bot.latency * 1000)}ms```",
            inline=True
        )

        embed.add_field(
            name="🖥️ Sistem Durumu",
            value=f"```yml\n"
                  f"CPU: {cpu_usage}%\n"
                  f"RAM: {memory_usage}%```",
            inline=True
        )

        embed.add_field(
            name="⚙️ Teknik Bilgiler",
            value=f"```yml\n"
                  f"Python: v{platform.python_version()}\n"
                  f"Discord.py: v{discord.__version__}\n"
                  f"OS: {platform.system()} {platform.release()}```",
            inline=False
        )

        embed.add_field(
            name="📊 İstatistikler",
            value=f"```yml\n"
                  f"Sunucu Sayısı: {len(self.bot.guilds)}\n"
                  f"Kullanıcı Sayısı: {len(set(self.bot.get_all_members()))}```",
            inline=False
        )

        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.default_avatar.url)
        embed.set_footer(text=f"📝 {ctx.author.name} tarafından istendi", 
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BotInfo(bot))
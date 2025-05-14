import discord
from discord.ext import commands, tasks
import datetime
import pytz

class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.morning_message.start()
        self.night_message.start()
        self.channel_id = 1371057475058401380  # Mesajların gönderileceği kanal ID'si

    def cog_unload(self):
        self.morning_message.cancel()
        self.night_message.cancel()

    @tasks.loop(time=datetime.time(hour=6, minute=0, tzinfo=pytz.timezone('Europe/Istanbul')))
    async def morning_message(self):
        """Her sabah 06:00'da çalışır"""
        channel = self.bot.get_channel(self.channel_id)
        if channel:
            embed = discord.Embed(
                title="🌅 Günaydın!",
                description="Günaydın dostlarım <3 Mükemmel bir gün dilerim sizlere. \n\n"
                            "Küfürsüz, düzgün ve özel bir gün geçirelim. \n\n"
                            "Bugün de birlikte güzel anılar biriktirelim.",
                color=0xffd700  # Altın sarısı
            )
            embed.set_footer(text="Lunaris Bot | Günlük Mesaj Sistemi")
            await channel.send(embed=embed)

    @tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=pytz.timezone('Europe/Istanbul')))
    async def night_message(self):
        """Her gece 00:00'da çalışır"""
        channel = self.bot.get_channel(self.channel_id)
        if channel:
            embed = discord.Embed(
                title="🌙 İyi Geceler!",
                description="İyi geceler dostlarım <3 Hepinize tatlı rüyalar dilerim.",
                color=0x2b2d31  # Koyu gri
            )
            embed.set_footer(text="Lunaris Bot | Günlük Mesaj Sistemi")
            await channel.send(embed=embed)

    @morning_message.before_loop
    @night_message.before_loop
    async def before_loops(self):
        """Bot hazır olana kadar bekle"""
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Tasks(bot))
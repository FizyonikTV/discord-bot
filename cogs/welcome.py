import discord
from discord.ext import commands
from datetime import datetime
from config.config import WELCOME_CHANNEL_ID

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        welcome_channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        
        if not welcome_channel:
            return

        embed_gif = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExdG00MDAzMnIzdnliN2ZoN2ZuaG9jZnVhYmx4aTJ2ZmV5bWFnNjZhMyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xUPGGDNsLvqsBOhuU0/giphy.gif"

        embed = discord.Embed(
            title="**★ Sunucuya hoş geldin! ★**",
            description=(
                f"Selam, {member.mention} ★\n"
                f"{member.guild.name} sunucusuna hoş geldin!\n\n"
                f"Lütfen, <#1267938623659966547> kanalını kontrol et! ▼\n\n"
                f"Umarım ki, kaldığın süreçte mutlu zaman geçirirsin!"
            ),
            color=0xFF69B4
        )

        embed.set_author(
            name=f"Sayın {member.name},",
            icon_url=member.avatar.url if member.avatar else member.default_avatar.url
        )

        embed.set_thumbnail(
            url=member.avatar.url if member.avatar else member.default_avatar.url
        )
        embed.set_image(url=embed_gif)

        member_count = len([m for m in member.guild.members if not m.bot])
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        embed.set_footer(text=f"Seninle birlikte şu kadar kişi olduk: {member_count} • {current_time}")

        await welcome_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
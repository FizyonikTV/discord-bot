import discord
from discord.ext import commands
import asyncio
import os
import logging
from datetime import datetime
from config.config import get_token, INTENTS, IZIN_VERILEN_ROLLER

# İzin verilen kanal ID'leri
COMMAND_CHANNELS = [
    1357419585678086195,
    1267939573976268930,
    1267940282947604531
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    filename="bot.log",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def command_check():
    async def predicate(ctx):
        # Komut kanalı kontrolü
        if ctx.channel.id not in COMMAND_CHANNELS:
            await ctx.message.delete()
            await ctx.send("❌ Bu komutu sadece komut kanallarında kullanabilirsiniz!", delete_after=5)
            raise commands.CheckFailure("Bu komut sadece belirli kanallarda kullanılabilir")
            
        # Rol kontrolü  
        member_roles = [role.id for role in ctx.author.roles]
        if not any(role in IZIN_VERILEN_ROLLER for role in member_roles):
            await ctx.message.delete()
            await ctx.send("❌ Bu komutu kullanmak için yeterli yetkiye sahip değilsiniz!", delete_after=5)
            raise commands.CheckFailure("Bu komut için yeterli yetkiye sahip değilsiniz")
            
        return True
    return commands.check(predicate)

class LunarisBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=INTENTS,
            case_insensitive=True
        )
        self.start_time = datetime.utcnow()
        
    # Tüm komutlara check ekleme
    async def add_cog(self, cog):
        for cmd in cog.get_commands():
            cmd.add_check(command_check())
        await super().add_cog(cog)

    async def setup_hook(self):
        """Initial setup and loading cogs"""
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'✅ Loaded cog: {filename}')
                except Exception as e:
                    print(f'❌ Failed to load cog {filename}: {e}')

    async def on_ready(self):
        """Bot hazır olduğunda çalışır"""
        print(f'✅ Bot {self.user} olarak giriş yaptı!')
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="LunarisBot | !yardım"
            )
        )
        logging.info(f"Bot is ready as {self.user}")

async def main():

    token = get_token()

    async with LunarisBot() as bot:
        await bot.start(get_token())

if __name__ == "__main__":
    asyncio.run(main())
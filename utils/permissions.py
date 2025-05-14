from discord.ext import commands
from config.config import IZIN_VERILEN_ROLLER

def has_mod_role():
    """Komut kullanımını moderatör rolüne sahip kullanıcılara sınırlar"""
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        return any(role.id in IZIN_VERILEN_ROLLER for role in ctx.author.roles)
    return commands.check(predicate)

def has_admin():
    """Komutu sadece administrator yetkisi olanlara sınırlar"""
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)
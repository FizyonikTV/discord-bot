import discord
from discord.ext import commands
import datetime
import json
from typing import Optional, Union
from config.config import *

def has_mod_role():
    async def predicate(ctx):
        return any(role.id in IZIN_VERILEN_ROLLER for role in ctx.author.roles)
    return commands.check(predicate)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notes_file = "data/notes.json"
        self.load_notes()

    def load_notes(self):
        try:
            with open(self.notes_file, "r", encoding="utf-8") as f:
                self.notes = json.load(f)
        except:
            self.notes = {}
            self.save_notes()

    def save_notes(self):
        with open(self.notes_file, "w", encoding="utf-8") as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=4)

    async def add_mod_note(self, user_id: str, mod_type: str, reason: str, moderator, duration: int = None):
        if str(user_id) not in self.notes:
            self.notes[str(user_id)] = {"UYARILAR": [], "TIMEOUTLAR": [], "BANLAR": []}

        note_data = {
            "sebep": reason,
            "moderator": str(moderator),
            "moderator_id": moderator.id,
            "tarih": datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        
        if duration:
            note_data["süre"] = f"{duration} saniye"

        self.notes[str(user_id)][mod_type].append(note_data)
        self.save_notes()

    async def get_member(self, ctx, user_id: Union[int, str]) -> Optional[discord.Member]:
        """Kullanıcıyı ID veya mention ile bulur"""
        try:
            # Mention veya ID'yi temizle
            if isinstance(user_id, str):
                user_id = user_id.strip("<@!>")
            
            member = ctx.guild.get_member(int(user_id))
            if not member:
                member = await ctx.guild.fetch_member(int(user_id))
            return member
        except:
            return None

    def create_base_embed(self, title: str, description: str, color: discord.Color):
        """Temel embed oluşturma fonksiyonu"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Lunaris Moderasyon Sistemi")
        return embed

    @commands.command(name="uyar", aliases=["warn"])
    @has_mod_role()
    async def warn(self, ctx, member: discord.Member, *, reason: str):
        """Kullanıcıyı uyarır"""
        if ctx.author.top_role <= member.top_role:
            return await ctx.send("❌ Bu kullanıcıyı uyaramazsınız!")

        await self.add_mod_note(member.id, "UYARILAR", reason, ctx.author)
        embed = self.create_base_embed(
            "⚠️ Kullanıcı Uyarıldı",
            f"```diff\n- {member} kullanıcısı uyarıldı.\n+ Sebep: {reason}```",
            discord.Color.yellow()
        )
        await self.send_mod_message(ctx, member, embed, WARN_LOG_KANAL_ID, "Uyarı Aldınız")

    @commands.command(name="zaman", aliases=["to", "timeout", "mute"])
    @has_mod_role()
    async def timeout(self, ctx, member: discord.Member, duration: int, *, reason: str = None):
        """Kullanıcıya timeout verir"""
        if ctx.author.top_role <= member.top_role:
            return await ctx.send("❌ Bu kullanıcıya timeout veremezsiniz!")

        try:
            await member.timeout(datetime.timedelta(seconds=duration), reason=f"{ctx.author}: {reason}")
            await self.add_mod_note(member.id, "TIMEOUTLAR", reason or "Belirtilmedi", ctx.author, duration)
            
            embed = self.create_base_embed(
                "⏳ Timeout Verildi",
                f"```diff\n- {member} kullanıcısı timeout aldı.\n+ Süre: {duration} saniye\n+ Sebep: {reason or 'Belirtilmedi'}```",
                discord.Color.orange()
            )
            await self.send_mod_message(ctx, member, embed, TIMEOUT_LOG_KANAL_ID, "Timeout Aldınız")
        except Exception as e:
            await ctx.send(f"❌ Bir hata oluştu: {e}")

    @commands.command(name="zamankaldir", aliases=["untimeout", "unmute", "unto"])
    @has_mod_role()
    async def untimeout(self, ctx, member: discord.Member):
        """Kullanıcının timeoutunu kaldırır"""
        try:
            await member.timeout(None, reason=f"Timeout Kaldıran: {ctx.author}")
            embed = self.create_base_embed(
                "✅ Timeout Kaldırıldı",
                f"```diff\n+ {member} kullanıcısının timeout'u kaldırıldı.```",
                discord.Color.green()
            )
            await self.send_mod_message(ctx, member, embed, TIMEOUT_LOG_KANAL_ID, "Timeout'unuz Kaldırıldı")
        except Exception as e:
            await ctx.send(f"❌ Bir hata oluştu: {e}")

    @commands.command(name="yasakla", aliases=["ban"])
    @has_mod_role()
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        """Kullanıcıya yasaklı rolü verir"""
        if ctx.author.top_role <= member.top_role:
            return await ctx.send("❌ Bu kullanıcıyı yasaklayamazsınız!")

        try:
            yasakli_rol = ctx.guild.get_role(YASAKLI)
            if not yasakli_rol:
                return await ctx.send("❌ Yasaklı rolü bulunamadı!")

            await member.add_roles(yasakli_rol, reason=f"Yasaklayan: {ctx.author} - Sebep: {reason}")
            await self.add_mod_note(member.id, "BANLAR", reason or "Belirtilmedi", ctx.author)

            embed = self.create_base_embed(
                "🔨 Kullanıcı Yasaklandı",
                f"```diff\n- {member} kullanıcısı yasaklandı.\n+ Sebep: {reason or 'Belirtilmedi'}```",
                discord.Color.red()
            )
            await self.send_mod_message(ctx, member, embed, BAN_LOG_KANAL_ID, "Yasaklandınız")
        except Exception as e:
            await ctx.send(f"❌ Bir hata oluştu: {e}")

    @commands.command(name="yasakkaldir", aliases=["unban"])
    @has_mod_role()
    async def unban(self, ctx, member: discord.Member):
        """Kullanıcının yasaklı rolünü kaldırır"""
        try:
            yasakli_rol = ctx.guild.get_role(YASAKLI)
            if not yasakli_rol:
                return await ctx.send("❌ Yasaklı rolü bulunamadı!")

            if yasakli_rol in member.roles:
                await member.remove_roles(yasakli_rol, reason=f"Yasak Kaldıran: {ctx.author}")
                embed = self.create_base_embed(
                    "🔓 Yasak Kaldırıldı",
                    f"```diff\n+ {member} kullanıcısının yasaklaması kaldırıldı.```",
                    discord.Color.green()
                )
                await self.send_mod_message(ctx, member, embed, BAN_LOG_KANAL_ID, "Yasaklamanız Kaldırıldı")
            else:
                await ctx.send("❌ Bu kullanıcı zaten yasaklı değil!")
        except Exception as e:
            await ctx.send(f"❌ Bir hata oluştu: {e}")

    async def send_mod_message(self, ctx, member: discord.Member, embed: discord.Embed, log_channel_id: int, dm_title: str):
        """Moderasyon mesajlarını gönderen yardımcı fonksiyon"""
        # Ana embed'e kullanıcı ve moderatör bilgilerini ekle
        embed.add_field(
            name="👤 Kullanıcı Bilgileri",
            value=f"```yaml\nKullanıcı: {member}\nID: {member.id}```",
            inline=False
        )
        embed.add_field(
            name="👮 Moderatör Bilgileri",
            value=f"```yaml\nModeratör: {ctx.author}\nID: {ctx.author.id}```",
            inline=False
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        # Log kanalına gönder
        log_channel = self.bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)

        # DM Gönder
        try:
            dm_embed = self.create_base_embed(
                f"{embed.title.split()[0]} {dm_title}",
                f"```diff\n- {ctx.guild.name} sunucusunda {dm_title.lower()}\n{embed.description.split('```diff\n')[1]}",
                embed.color
            )
            await member.send(embed=dm_embed)
        except:
            pass

        # Komut kanalına gönder
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
import discord
from discord.ext import commands
import datetime
from config.config import *

class Notes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.moderation = None

    async def cog_load(self):
        """Moderation cog'una erişim sağla"""
        self.moderation = self.bot.get_cog('Moderation')

    @commands.command(name="notlar", aliases=["geçmiş", "gecmis", "logs"])
    @commands.has_permissions(kick_members=True)
    async def view_notes(self, ctx, user_id: int):
        """Kullanıcının tüm moderasyon geçmişini gösterir"""
        if not self.moderation:
            return await ctx.send("❌ Moderasyon sistemi yüklenemedi!")

        notes = self.moderation.notes.get(str(user_id))
        if not notes:
            return await ctx.send("❌ Bu kullanıcı için kayıt bulunmuyor!")

        try:
            user = await self.bot.fetch_user(user_id)
            embed = discord.Embed(
                title=f"📋 {user.name} Kullanıcısının Moderasyon Geçmişi",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
        except:
            embed = discord.Embed(
                title=f"📋 ID: {user_id} Kullanıcısının Moderasyon Geçmişi",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )

        # Uyarıları listele
        if notes.get("UYARILAR"):
            uyari_text = ""
            for idx, note in enumerate(notes["UYARILAR"], 1):
                uyari_text += f"**#{idx}** | {note['tarih']}\n"
                uyari_text += f"➜ Sebep: {note['sebep']}\n"
                uyari_text += f"➜ Moderatör: {note['moderator']}\n\n"
            embed.add_field(
                name=f"⚠️ Uyarılar [{len(notes['UYARILAR'])}]",
                value=uyari_text or "Bulunmuyor",
                inline=False
            )

        # Timeoutları listele
        if notes.get("TIMEOUTLAR"):
            timeout_text = ""
            for idx, note in enumerate(notes["TIMEOUTLAR"], 1):
                timeout_text += f"**#{idx}** | {note['tarih']}\n"
                timeout_text += f"➜ Sebep: {note['sebep']}\n"
                timeout_text += f"➜ Süre: {note.get('süre', 'Belirtilmedi')}\n"
                timeout_text += f"➜ Moderatör: {note['moderator']}\n\n"
            embed.add_field(
                name=f"⏳ Timeout Geçmişi [{len(notes['TIMEOUTLAR'])}]",
                value=timeout_text or "Bulunmuyor",
                inline=False
            )

        # Banları listele
        if notes.get("BANLAR"):
            ban_text = ""
            for idx, note in enumerate(notes["BANLAR"], 1):
                ban_text += f"**#{idx}** | {note['tarih']}\n"
                ban_text += f"➜ Sebep: {note['sebep']}\n"
                ban_text += f"➜ Moderatör: {note['moderator']}\n\n"
            embed.add_field(
                name=f"🔨 Ban Geçmişi [{len(notes['BANLAR'])}]",
                value=ban_text or "Bulunmuyor",
                inline=False
            )

        total_actions = (
            len(notes.get("UYARILAR", [])) +
            len(notes.get("TIMEOUTLAR", [])) +
            len(notes.get("BANLAR", []))
        )
        
        embed.description = f"**Toplam İşlem Sayısı:** {total_actions}"
        embed.set_footer(text=f"ID: {user_id} | Sorgulayan: {ctx.author}")
        await ctx.send(embed=embed)

    @commands.command(name="notsil")
    @commands.has_permissions(administrator=True)
    async def delete_note(self, ctx, user_id: int, type: str, index: int):
        """Belirtilen moderasyon kaydını siler
        Kullanım: !notsil <user_id> <uyari/timeout/ban> <sıra_no>"""
        if not self.moderation:
            return await ctx.send("❌ Moderasyon sistemi yüklenemedi!")

        type = type.upper()
        if type == "UYARI":
            type = "UYARILAR"
        elif type == "TIMEOUT":
            type = "TIMEOUTLAR"
        elif type == "BAN":
            type = "BANLAR"
        else:
            return await ctx.send("❌ Geçersiz tür! Kullanım: `!notsil <user_id> <uyari/timeout/ban> <sıra_no>`")

        try:
            notes = self.moderation.notes.get(str(user_id))
            if not notes or type not in notes or not notes[type]:
                return await ctx.send("❌ Belirtilen kayıt bulunamadı!")

            if index < 1 or index > len(notes[type]):
                return await ctx.send("❌ Geçersiz sıra numarası!")

            deleted_note = notes[type].pop(index - 1)
            if not notes[type] and not notes["UYARILAR"] and not notes["TIMEOUTLAR"] and not notes["BANLAR"]:
                del self.moderation.notes[str(user_id)]
            self.moderation.save_notes()

            embed = discord.Embed(
                title="🗑️ Moderasyon Kaydı Silindi",
                description=(
                    f"**Kullanıcı ID:** {user_id}\n"
                    f"**Tür:** {type}\n"
                    f"**Sıra:** #{index}\n"
                    f"**Sebep:** {deleted_note['sebep']}\n"
                    f"**Moderatör:** {deleted_note['moderator']}\n"
                    f"**Tarih:** {deleted_note['tarih']}"
                ),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Bir hata oluştu: {e}")

    @commands.command(name="nottemizle")
    @commands.has_permissions(administrator=True)
    async def clear_notes(self, ctx, user_id: int):
        """Kullanıcının tüm moderasyon geçmişini temizler"""
        if not self.moderation:
            return await ctx.send("❌ Moderasyon sistemi yüklenemedi!")

        if str(user_id) not in self.moderation.notes:
            return await ctx.send("❌ Bu kullanıcı için kayıt bulunmuyor!")

        try:
            user = await self.bot.fetch_user(user_id)
            user_name = user.name
        except:
            user_name = str(user_id)

        del self.moderation.notes[str(user_id)]
        self.moderation.save_notes()

        embed = discord.Embed(
            title="🧹 Moderasyon Geçmişi Temizlendi",
            description=f"**{user_name}** kullanıcısının tüm moderasyon kayıtları silindi.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Notes(bot))
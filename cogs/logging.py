import discord
from discord.ext import commands
from datetime import datetime
from utils.helpers import izin_kontrol, create_embed, send_log
from config.config import *  # Import constants

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Kanal ID'leri
        self.BAN_LOG_KANAL_ID = 1281700459991666748
        self.WARN_LOG_KANAL_ID = 1281700488156414102
        self.TIMEOUT_LOG_KANAL_ID = 1281700527473819699
        self.MESSAGE_LOG_KANAL_ID = 1281700552929185882
        self.USER_LOG_KANAL_ID = 1359645505948221572
        self.ROLE_LOG_KANAL_ID = 1281700727172894800
        self.VOICE_LOG_KANAL_ID = 1359645396330090617

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        channel = self.bot.get_channel(self.MESSAGE_LOG_KANAL_ID)
        if not channel:
            return

        embed = discord.Embed(
            title="🗑️ Mesaj Silindi",
            description=(
                f"**Kanal:** {message.channel.mention} (`#{message.channel.name}`)\n"
                f"**Yazan:** {message.author.mention} (`{message.author}`)\n"
            ),
            color=0xff3366,
            timestamp=discord.utils.utcnow()
        )

        # Mesaj içeriği
        if message.content:
            if len(message.content) > 1024:
                content = message.content[:1021] + "..."
            else:
                content = message.content
            embed.add_field(
                name="📝 Silinen Mesaj İçeriği",
                value=f"```{content}```",
                inline=False
            )

        # Dosya ekleri
        if message.attachments:
            files = "\n".join([f"• {attachment.filename} ({attachment.url})" for attachment in message.attachments])
            embed.add_field(
                name="📎 Silinen Dosya Ekleri",
                value=f"```{files}```",
                inline=False
            )

        # Embed içeriği
        if message.embeds:
            embed.add_field(
                name="🔗 Silinen Embed Bilgisi",
                value=f"`Bu mesaj {len(message.embeds)} adet embed içeriyordu`",
                inline=False
            )

        # Detaylı bilgiler
        embed.add_field(
            name="⏰ Mesaj Bilgileri",
            value=(
                f"• Oluşturulma: <t:{int(message.created_at.timestamp())}:R>\n"
                f"• Silinme: <t:{int(discord.utils.utcnow().timestamp())}:R>\n"
                f"• Mesaj ID: `{message.id}`\n"
                f"• Kanal ID: `{message.channel.id}`"
            ),
            inline=False
        )

        embed.set_author(
            name=str(message.author),
            icon_url=message.author.display_avatar.url
        )
        
        embed.set_footer(
            text=f"Kullanıcı ID: {message.author.id}"
        )
        
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return

        channel = self.bot.get_channel(self.MESSAGE_LOG_KANAL_ID)
        if not channel:
            return

        embed = discord.Embed(
            title="✏️ Mesaj Düzenlendi",
            description=(
                f"**Kanal:** {before.channel.mention} (`#{before.channel.name}`)\n"
                f"**Yazan:** {before.author.mention} (`{before.author}`)\n"
                f"**[Mesaja Git]({before.jump_url})**"
            ),
            color=0x3498db,
            timestamp=discord.utils.utcnow()
        )

        # Eski mesaj içeriği
        if len(before.content) > 1024:
            old_content = before.content[:1021] + "..."
        else:
            old_content = before.content

        embed.add_field(
            name="📤 Eski Mesaj",
            value=f"```{old_content}```",
            inline=False
        )

        # Yeni mesaj içeriği
        if len(after.content) > 1024:
            new_content = after.content[:1021] + "..."
        else:
            new_content = after.content

        embed.add_field(
            name="📥 Yeni Mesaj",
            value=f"```{new_content}```",
            inline=False
        )

        # Değişiklik istatistikleri
        old_len = len(before.content)
        new_len = len(after.content)
        embed.add_field(
            name="📊 Değişiklik İstatistikleri",
            value=(
                f"• Eski uzunluk: `{old_len}` karakter\n"
                f"• Yeni uzunluk: `{new_len}` karakter\n"
                f"• Fark: `{new_len - old_len:+}` karakter"
            ),
            inline=False
        )

        # Zaman bilgileri
        embed.add_field(
            name="⏰ Mesaj Bilgileri",
            value=(
                f"• Oluşturulma: <t:{int(before.created_at.timestamp())}:R>\n"
                f"• Düzenleme: <t:{int(discord.utils.utcnow().timestamp())}:R>\n"
                f"• Mesaj ID: `{before.id}`\n"
                f"• Kanal ID: `{before.channel.id}`"
            ),
            inline=False
        )

        embed.set_author(
            name=str(before.author),
            icon_url=before.author.display_avatar.url
        )

        embed.set_footer(
            text=f"Kullanıcı ID: {before.author.id}"
        )

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        channel = self.bot.get_channel(self.USER_LOG_KANAL_ID)
        if not channel:
            return

        embed = discord.Embed(
            title="👤 Kullanıcı Güncellemesi",
            description=f"**Kullanıcı:** {before.mention}\n**ID:** `{before.id}`",
            color=0x2ECC71,
            timestamp=discord.utils.utcnow()
        )

        if before.nick != after.nick:
            embed.add_field(
                name="📝 Takma Ad Değişikliği",
                value=f"**Eski:** {before.nick or 'Yok'}\n**Yeni:** {after.nick or 'Yok'}", 
                inline=False
            )

        if before.roles != after.roles:
            removed_roles = set(before.roles) - set(after.roles)
            added_roles = set(after.roles) - set(before.roles)

            if removed_roles:
                embed.add_field(
                    name="🔴 Kaldırılan Roller",
                    value="\n".join([f"└ {role.mention}" for role in removed_roles]),
                    inline=False
                )
            if added_roles:
                embed.add_field(
                    name="🟢 Eklenen Roller",
                    value="\n".join([f"└ {role.mention}" for role in added_roles]),
                    inline=False
                )

        if embed.fields:
            embed.set_thumbnail(url=before.avatar.url if before.avatar else before.default_avatar.url)
            embed.set_footer(text=f"Kullanıcı ID: {before.id} • {datetime.utcnow().strftime('%H:%M:%S')}")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        channel = self.bot.get_channel(self.VOICE_LOG_KANAL_ID)
        if not channel:
            return

        if before.channel != after.channel:
            embed = discord.Embed(
                title="🔊 Ses Kanalı Güncellemesi",
                description=f"{member.mention} ses kanalını değiştirdi.",
                color=0x1ABC9C
            )
            if before.channel:
                embed.add_field(name="⬅️ Önceki Kanal", value=before.channel.name, inline=True)
            if after.channel:
                embed.add_field(name="➡️ Yeni Kanal", value=after.channel.name, inline=True)
            await channel.send(embed=embed)

    async def log_handler(self, log_type, **kwargs):
        log_channels = {
            "ban": self.BAN_LOG_KANAL_ID,
            "unban": self.BAN_LOG_KANAL_ID,
            "warn": self.WARN_LOG_KANAL_ID,
            "timeout": self.TIMEOUT_LOG_KANAL_ID,
            "timeout_remove": self.TIMEOUT_LOG_KANAL_ID
        }

        log_styles = {
            "ban": {"emoji": "⛔", "color": 0xE74C3C, "title": "Kullanıcı Yasaklandı"},
            "unban": {"emoji": "🔓", "color": 0x2ECC71, "title": "Kullanıcı Yasağı Kaldırıldı"},
            "warn": {"emoji": "⚠️", "color": 0xFFA500, "title": "Kullanıcı Uyarıldı"},
            "timeout": {"emoji": "⏳", "color": 0x3498DB, "title": "Zaman Aşımı Uygulandı"},
            "timeout_remove": {"emoji": "⏱️", "color": 0x2ECC71, "title": "Zaman Aşımı Kaldırıldı"}
        }

        channel = self.bot.get_channel(log_channels.get(log_type))
        if not channel:
            return

        style = log_styles.get(log_type, {"emoji": "ℹ️", "color": 0x7289DA, "title": "Log Kaydı"})
        embed = discord.Embed(
            title=f"{style['emoji']} {style['title']} {style['emoji']}",
            color=style["color"],
            timestamp=discord.utils.utcnow()
        )

        # Add fields based on kwargs
        if "yetkili" in kwargs:
            embed.add_field(name="👮 Yetkili", value=kwargs["yetkili"].mention, inline=True)
        if "kullanici" in kwargs:
            embed.add_field(name="👤 Kullanıcı", value=kwargs["kullanici"].mention, inline=True)
            embed.set_thumbnail(url=kwargs["kullanici"].avatar.url if kwargs["kullanici"].avatar else kwargs["kullanici"].default_avatar.url)
        if "sebep" in kwargs:
            embed.add_field(name="📝 Sebep", value=kwargs["sebep"], inline=False)
        if "sure" in kwargs and log_type == "timeout":
            embed.add_field(name="⏰ Süre", value=f"{kwargs['sure']} saniye", inline=True)

        await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logging(bot))
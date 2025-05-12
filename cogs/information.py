import discord
from discord.ext import commands
import platform
import time
from datetime import datetime
from utils.helpers import izin_kontrol, create_embed, send_log
from config.config import *  # Import constants


# İzin verilen kanal ID'leri
COMMAND_CHANNELS = [
    1357419585678086195,
    1267939573976268930,
    1267940282947604531
]

class Information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="kullanici", aliases=["user", "userinfo"])
    @commands.check(izin_kontrol)
    async def kullanici(self, ctx, member: discord.Member = None):
        """Kullanıcı hakkında detaylı bilgi verir."""
        member = member or ctx.author

        embed = discord.Embed(
            title=f"🕵️ {member.name} Kullanıcı Bilgisi",
            color=0x9B59B6
        )

        # Temel Bilgiler
        basic_info = (
            f"**🏷️ Kullanıcı Adı:** {member.name}\n"
            f"**#️⃣ Etiket:** {member.discriminator}\n"
            f"**🆔 Kullanıcı ID:** `{member.id}`\n"
            f"**🤖 Bot mu?** {'Evet' if member.bot else 'Hayır'}\n"
        )
        embed.add_field(name="📌 Temel Bilgiler", value=basic_info, inline=False)

        # Tarihler
        dates_info = (
            f"**🗓️ Hesap Oluşturulma:** {member.created_at.strftime('%d.%m.%Y - %H:%M:%S')}\n"
            f"⏱️ **Oluşturulalı:** {(datetime.utcnow() - member.created_at.replace(tzinfo=None)).days} gün\n"
            f"**🤝 Sunucuya Katılma:** {member.joined_at.strftime('%d.%m.%Y - %H:%M:%S')}\n"
            f"⏱️ **Katılalı:** {(datetime.utcnow() - member.joined_at.replace(tzinfo=None)).days} gün"
        )
        embed.add_field(name="📅 Tarihler", value=dates_info, inline=False)

        # Roller
        roles = [role.mention for role in member.roles if role != ctx.guild.default_role]
        roles_info = f"{', '.join(roles)}" if roles else "🚫 Yok"
        embed.add_field(name=f"🎭 Roller ({len(roles)})", value=roles_info, inline=False)

        # Durum ve Aktivite
        status_info = f"**🌐 Durum:** {str(member.status).title()}"
        if member.activity:
            activity_types = {
                discord.ActivityType.playing: "Oynuyor",
                discord.ActivityType.streaming: "Yayın Yapıyor",
                discord.ActivityType.listening: "Dinliyor",
                discord.ActivityType.watching: "İzliyor",
                discord.ActivityType.custom: "Özel Durum",
                discord.ActivityType.competing: "Yarışıyor"
            }
            status_info += f"\n**🎮 Aktivite:** {member.activity.name}"
            status_info += f" ({activity_types.get(member.activity.type, 'Bilinmiyor')})"
        embed.add_field(name="🚦 Durum ve Aktivite", value=status_info, inline=False)

        # Avatar
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        else:
            embed.set_thumbnail(url=member.default_avatar.url)

        embed.set_footer(text=f"Talep Eden: {ctx.author.name}", 
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        await ctx.send(embed=embed)

    @commands.command(name="sunucu", aliases=["server", "serverinfo", "si"])
    @commands.check(izin_kontrol)
    async def sunucu(self, ctx):
        """Sunucu hakkında detaylı bilgi verir."""
        guild = ctx.guild

        # İstatistikler
        total_members = guild.member_count
        bot_count = len([m for m in guild.members if m.bot])
        human_count = total_members - bot_count
        online_count = len([m for m in guild.members if m.status != discord.Status.offline])

        # Kanal sayıları
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)

        # Diğer bilgiler
        emoji_count = len(guild.emojis)
        role_count = len(guild.roles)
        boost_count = guild.premium_subscription_count
        boost_tier = guild.premium_tier

        embed = discord.Embed(
            title=f"📊 {guild.name} - Sunucu Bilgileri",
            description=f"*{guild.description}*" if guild.description else "",
            color=0x8B008B
        )

        general_info = (
            f"📛 **ID:** `{guild.id}`\n"
            f"👑 **Sahip:** {guild.owner.mention}\n"
            f"🔒 **Doğrulama:** {guild.verification_level.name}\n"
            f"📆 **Oluşturulma:** {guild.created_at.strftime('%d.%m.%Y - %H:%M:%S')}\n"
            f"⏱️ **Oluşturulalı:** {(datetime.utcnow() - guild.created_at.replace(tzinfo=None)).days} gün"
        )
        embed.add_field(name="📌 Genel Bilgiler", value=general_info, inline=False)

        member_info = (
            f"👥 **Toplam Üye:** {total_members}\n"
            f"👤 **İnsan:** {human_count}\n"
            f"🤖 **Bot:** {bot_count}\n"
            f"🟢 **Çevrimiçi:** {online_count}"
        )
        embed.add_field(name="👥 Üye Bilgileri", value=member_info, inline=True)

        channel_info = (
            f"💬 **Metin:** {text_channels}\n"
            f"🔊 **Ses:** {voice_channels}\n"
            f"📂 **Kategori:** {categories}\n"
            f"📊 **Toplam:** {text_channels + voice_channels}"
        )
        embed.add_field(name="📊 Kanal Bilgileri", value=channel_info, inline=True)

        if guild.features:
            features = "\n".join([f"✅ {feature.replace('_', ' ').title()}" 
                                for feature in guild.features])
        else:
            features = "❌ Özel özellik yok"
        embed.add_field(name="✨ Sunucu Özellikleri", value=features, inline=False)

        boost_info = (
            f"🚀 **Boost Sayısı:** {boost_count}\n"
            f"⭐ **Boost Seviyesi:** {boost_tier}"
        )
        embed.add_field(name="🚀 Boost Bilgileri", value=boost_info, inline=True)

        other_info = (
            f"👑 **Rol Sayısı:** {role_count}\n"
            f"😀 **Emoji Sayısı:** {emoji_count}"
        )
        embed.add_field(name="🔢 Diğer İstatistikler", value=other_info, inline=True)

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(text=f"Talep Eden: {ctx.author.name}", 
                        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        await ctx.send(embed=embed)

    @commands.command(name="avatar", aliases=["av", "pfp"])
    async def avatar(self, ctx, member: discord.Member = None):
        """Kullanıcının profil resmini gösterir."""
        # Komut kanalı kontrolü
        if ctx.channel.id not in COMMAND_CHANNELS:
            await ctx.message.delete()
            await ctx.send("❌ Bu komutu sadece komut kanallarında kullanabilirsiniz!", delete_after=5)
            return
        
        member = member or ctx.author

        embed = discord.Embed(
            title=f"🖼️ {member.name} Profil Resmi",
            color=0x8B008B
        )

        avatar_formats = []
        if member.avatar:
            avatar_url = member.avatar.url
            for fmt in ["png", "jpg", "webp"]:
                avatar_formats.append(f"[{fmt.upper()}]({member.avatar.with_format(fmt).url})")
            if member.avatar.is_animated():
                avatar_formats.append(f"[GIF]({member.avatar.with_format('gif').url})")
        else:
            avatar_url = member.default_avatar.url
            avatar_formats.append(f"[PNG]({member.default_avatar.url})")

        embed.description = "**Format Bağlantıları:** " + " | ".join(avatar_formats)
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"Kullanıcı ID: {member.id}")

        await ctx.send(embed=embed)

    @commands.command(name="banner", aliases=["bn"])
    async def banner(self, ctx, user: discord.User = None):
        """Kullanıcının banner resmini gösterir."""
        # Komut kanalı kontrolü
        if ctx.channel.id not in COMMAND_CHANNELS:
            await ctx.message.delete()
            await ctx.send("❌ Bu komutu sadece komut kanallarında kullanabilirsiniz!", delete_after=5)
            return
        
        user = user or ctx.author
        
        # Fetch the user to get banner info
        try:
            fetched_user = await self.bot.fetch_user(user.id)
            
            if not fetched_user.banner:
                await ctx.send(f"❌ **{user.name}** kullanıcısının banner resmi bulunmuyor.")
                return
                
            embed = discord.Embed(
                title=f"🏞️ {user.name} Banner Resmi",
                color=0x8B008B
            )
            
            banner_formats = []
            for fmt in ["png", "jpg", "webp"]:
                banner_formats.append(f"[{fmt.upper()}]({fetched_user.banner.with_format(fmt).url})")
            if fetched_user.banner.is_animated():
                banner_formats.append(f"[GIF]({fetched_user.banner.with_format('gif').url})")
                
            embed.description = "**Format Bağlantıları:** " + " | ".join(banner_formats)
            embed.set_image(url=fetched_user.banner.url)
            embed.set_footer(text=f"Kullanıcı ID: {user.id} • Talep Eden: {ctx.author.name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Banner alınırken bir hata oluştu: {str(e)}")
            print(f"Banner alınırken bir hata oluştu: {str(e)}")

async def setup(bot):
    await bot.add_cog(Information(bot))
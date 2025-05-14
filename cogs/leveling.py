import discord
from discord.ext import commands
import json
import math
import time
from discord.ext.commands import cooldown, BucketType
from utils.helpers import izin_kontrol, create_embed, send_log
from config.config import *  # Import constants
from config.config import LEVEL_ROLES
from utils.permissions import has_mod_role, has_admin

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.XP_PER_MESSAGE = 15
        self.XP_COOLDOWN = 60
        self.last_xp_gain = {}
        self.LEVELS_FILE = "seviyeler.json"
        self.user_levels = {}
        self.load_levels()

    def load_levels(self):
        try:
            with open(self.LEVELS_FILE, 'r', encoding='utf-8') as f:
                self.user_levels = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.user_levels = {}
            with open(self.LEVELS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.user_levels, f, indent=4, ensure_ascii=False)

    def save_levels(self):
        try:
            with open(self.LEVELS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.user_levels, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Seviye verileri kaydedilirken hata oluştu: {e}")

    def calculate_xp_for_level(self, level: int) -> int:
        return math.floor(100 * (level ** 1.5))

    def get_level_from_xp(self, xp: int) -> int:
        return math.floor((xp / 100) ** (1/1.5))

    async def update_level_roles(self, member: discord.Member, new_level: int, old_level: int = 0):
        """Kullanıcının seviye rollerini günceller"""
        roles_to_remove = []
        roles_to_add = []
        
        # Tüm seviye rollerini kontrol et
        sorted_levels = sorted(LEVEL_ROLES.items(), key=lambda x: x[0])  # Seviyeleri sırala
        
        current_role = None
        # En yüksek hak kazanılan rolü bul
        for level, role_id in sorted_levels:
            role = member.guild.get_role(role_id)
            if not role:
                continue
                
            if level <= new_level:
                if current_role:  # Eğer önceki bir rol varsa, onu kaldır
                    roles_to_remove.append(current_role)
                current_role = role
                if role not in member.roles:  # Sadece kullanıcıda olmayan rolü ekle
                    roles_to_add.append(role)
            else:
                if role in member.roles:  # Hak kazanılmayan rolleri kaldır
                    roles_to_remove.append(role)

        # Rolleri güncelle
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason="Seviye rolleri güncellendi")
        if roles_to_add:
            await member.add_roles(*roles_to_add, reason="Yeni seviye rolü kazanıldı")

        return roles_to_remove, roles_to_add

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        current_time = time.time()
        user_id = str(message.author.id)
        guild_id = str(message.guild.id)

        if guild_id not in self.user_levels:
            self.user_levels[guild_id] = {}
        
        if user_id not in self.user_levels[guild_id]:
            self.user_levels[guild_id][user_id] = {"xp": 0, "level": 0}

        last_gain = self.last_xp_gain.get(f"{guild_id}-{user_id}", 0)
        if current_time - last_gain >= self.XP_COOLDOWN:
            self.user_levels[guild_id][user_id]["xp"] += self.XP_PER_MESSAGE
            self.last_xp_gain[f"{guild_id}-{user_id}"] = current_time

            old_level = self.user_levels[guild_id][user_id]["level"]
            new_level = self.get_level_from_xp(self.user_levels[guild_id][user_id]["xp"])

            if new_level > old_level:
                self.user_levels[guild_id][user_id]["level"] = new_level
                
                removed_roles, added_roles = await self.update_level_roles(message.author, new_level, old_level)
                
                role_text = ""
                if added_roles:
                    role_mentions = [role.mention for role in added_roles]
                    role_text = f"\n🎭 Yeni rol(ler) kazandınız: {', '.join(role_mentions)}"
                
                embed = discord.Embed(
                    title="🎉 Seviye Atladınız!",
                    description=f"Tebrikler {message.author.mention}!\n"
                               f"**{old_level}** seviyesinden **{new_level}** seviyesine ulaştınız!{role_text}",
                    color=0xFFD700
                )
                embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
                await message.channel.send(embed=embed)

            self.save_levels()

    @commands.command(name="rank", aliases=["level", "seviye"])
    @cooldown(1, 10, BucketType.user)
    async def rank(self, ctx, member: discord.Member = None):
        """Kullanıcının seviye bilgilerini gösterir."""
        member = member or ctx.author
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id not in self.user_levels or user_id not in self.user_levels[guild_id]:
            embed = discord.Embed(
                title="❌ Seviye Bulunamadı",
                description=f"{member.mention} henüz hiç XP kazanmamış.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        user_data = self.user_levels[guild_id][user_id]
        current_xp = user_data["xp"]
        current_level = user_data["level"]
        xp_for_next = self.calculate_xp_for_level(current_level + 1)
        
        progress = (current_xp - self.calculate_xp_for_level(current_level)) / (xp_for_next - self.calculate_xp_for_level(current_level))
        progress_bar = "█" * int(progress * 10) + "░" * (10 - int(progress * 10))

        embed = discord.Embed(
            title=f"📊 {member.name}'in Seviye Bilgileri",
            color=0x00ff00
        )
        embed.add_field(
            name="📈 Seviye Detayları",
            value=f"**Seviye:** {current_level}\n"
                  f"**XP:** {current_xp}/{xp_for_next}\n"
                  f"**İlerleme:** {progress_bar} ({int(progress*100)}%)",
            inline=False
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Toplam XP: {current_xp}")

        await ctx.send(embed=embed)

    @commands.command(name="top", aliases=["leaderboard", "sıralama"])
    @cooldown(1, 10, BucketType.user)
    async def leaderboard(self, ctx, page: int = 1):
        """Sunucudaki XP sıralamasını gösterir."""
        guild_id = str(ctx.guild.id)
        if guild_id not in self.user_levels:
            await ctx.send("Bu sunucuda henüz hiç XP kazanan olmamış!")
            return

        sorted_users = sorted(
            self.user_levels[guild_id].items(),
            key=lambda x: x[1]["xp"],
            reverse=True
        )

        items_per_page = 10
        pages = math.ceil(len(sorted_users) / items_per_page)
        page = max(1, min(page, pages))
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page

        embed = discord.Embed(
            title=f"🏆 XP Sıralaması - Sayfa {page}/{pages}",
            color=0xffd700
        )

        for idx, (user_id, data) in enumerate(sorted_users[start_idx:end_idx], start=start_idx + 1):
            member = ctx.guild.get_member(int(user_id))
            if member:
                medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "👤"
                embed.add_field(
                    name=f"{medal} #{idx}. {member.name}",
                    value=f"Seviye: {data['level']} | XP: {data['xp']}",
                    inline=False
                )

        embed.set_footer(text=f"Sayfa {page}/{pages} • !sıralama <sayfa> ile diğer sayfaları görüntüleyebilirsiniz")
        await ctx.send(embed=embed)

    @commands.command(name="xpekle")
    @has_admin()
    async def add_xp(self, ctx, member: discord.Member, xp: int):
        """Kullanıcıya XP ekler."""
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id not in self.user_levels:
            self.user_levels[guild_id] = {}
        if user_id not in self.user_levels[guild_id]:
            self.user_levels[guild_id][user_id] = {"xp": 0, "level": 0}

        old_level = self.user_levels[guild_id][user_id]["level"]
        self.user_levels[guild_id][user_id]["xp"] += xp
        new_level = self.get_level_from_xp(self.user_levels[guild_id][user_id]["xp"])
        self.user_levels[guild_id][user_id]["level"] = new_level
        
        removed_roles, added_roles = await self.update_level_roles(member, new_level, old_level)
        
        role_text = ""
        if added_roles:
            role_mentions = [role.mention for role in added_roles]
            role_text = f"\n🎭 Yeni rol(ler): {', '.join(role_mentions)}"
        elif removed_roles:
            role_mentions = [role.mention for role in removed_roles]
            role_text = f"\n🎭 Kaybedilen rol(ler): {', '.join(role_mentions)}"

        embed = discord.Embed(
            title="✅ XP Eklendi",
            description=f"{member.mention} kullanıcısına **{xp}** XP eklendi.\n"
                       f"Eski seviye: **{old_level}**\n"
                       f"Yeni seviye: **{new_level}**{role_text}",
            color=0x00ff00
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        await ctx.send(embed=embed)
        self.save_levels()

    @commands.command(name="xpsıfırla")
    @has_admin()
    async def reset_xp(self, ctx, member: discord.Member):
        """Kullanıcının XP'sini sıfırlar."""
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        if guild_id in self.user_levels and user_id in self.user_levels[guild_id]:
            old_level = self.user_levels[guild_id][user_id]["level"]
            self.user_levels[guild_id][user_id] = {"xp": 0, "level": 0}
            
            removed_roles, _ = await self.update_level_roles(member, 0, old_level)
            
            role_text = ""
            if removed_roles:
                role_mentions = [role.mention for role in removed_roles]
                role_text = f"\n🎭 Kaldırılan roller: {', '.join(role_mentions)}"
            
            embed = discord.Embed(
                title="🔄 XP Sıfırlandı",
                description=f"{member.mention} kullanıcısının XP'si sıfırlandı.\n"
                           f"Eski seviye: **{old_level}**\n"
                           f"Yeni seviye: **0**{role_text}",
                color=0xff0000
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            await ctx.send(embed=embed)
            self.save_levels()
        else:
            await ctx.send(f"{member.mention} kullanıcısının zaten hiç XP'si yok.")

async def setup(bot):
    await bot.add_cog(Leveling(bot))
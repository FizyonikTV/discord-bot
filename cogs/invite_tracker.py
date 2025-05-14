import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime
import typing
from collections import defaultdict
import io
from utils.permissions import has_admin, has_mod_role

class InviteTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = "config/invite_config.json"
        self.data_path = "data/invites.json"
        self.invites_cache = {}  # {guild_id: {invite_code: uses}}
        self.invite_data = {}  # {guild_id: {user_id: {invites: count, fake: count, left: count, invitees: [user_ids]}}}
        self.load_config()
        self.load_data()
        
        # Bot hazır olduğunda davetleri yükleme
        self.bot.loop.create_task(self.initialize_invites())
        
    def load_config(self):
        """Davet takip yapılandırmasını yükle"""
        default_config = {
            "enabled": True,
            "welcome_channel_id": None,  # Karşılama mesajlarının gönderileceği kanal
            "welcome_message": "{user.mention}, aramıza hoş geldin! {inviter.mention} tarafından davet edildin.",
            "welcome_with_unknown_inviter": "{user.mention}, aramıza hoş geldin!",
            "log_channel_id": None,  # İşlemlerin loglanacağı kanal
            "bonus_invites": {},  # Bonus davet sayıları {user_id: count}
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = default_config
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Davet takip yapılandırması yüklenirken hata: {e}")
            self.config = default_config
            
    def load_data(self):
        """Davet verilerini yükle"""
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    self.invite_data = json.load(f)
        except Exception as e:
            print(f"Davet verileri yüklenirken hata: {e}")
            self.invite_data = {}
            
    def save_data(self):
        """Davet verilerini kaydet"""
        try:
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.invite_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Davet verileri kaydedilirken hata: {e}")
            
    async def initialize_invites(self):
        """Bot başlangıcında tüm sunuculardaki davetleri yükle"""
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            try:
                # Botun davetleri görme izni olduğundan emin olun
                if guild.me.guild_permissions.manage_guild:
                    invites = await guild.invites()
                    self.invites_cache[guild.id] = {invite.code: invite.uses for invite in invites}
                    await self.log_invite_event(guild.id, f"🔄 Davet takibi başlatıldı. {len(invites)} davet takip edilecek.")
            except discord.Forbidden:
                await self.log_invite_event(guild.id, "❌ Davetleri görüntüleme iznim yok!")
            except Exception as e:
                await self.log_invite_event(guild.id, f"❌ Davetler yüklenirken hata: {e}")
                
    def ensure_user_data(self, guild_id, user_id):
        """Kullanıcı davet verilerini kontrol et ve yoksa oluştur"""
        guild_id = str(guild_id)
        user_id = str(user_id)
        
        if guild_id not in self.invite_data:
            self.invite_data[guild_id] = {}
            
        if user_id not in self.invite_data[guild_id]:
            self.invite_data[guild_id][user_id] = {
                "invites": 0,      # Başarılı davetler
                "fake": 0,         # Sahte/tekrar katılımlar
                "left": 0,         # Ayrılan davetler
                "invitees": [],    # Davet edilen kullanıcılar
                "joined_at": datetime.utcnow().isoformat(),  # Katılma zamanı
            }
            
        return self.invite_data[guild_id][user_id]
        
    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        """Yeni davet oluşturulduğunda tetiklenir"""
        guild_id = invite.guild.id
        if guild_id not in self.invites_cache:
            self.invites_cache[guild_id] = {}
        self.invites_cache[guild_id][invite.code] = invite.uses
        
    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        """Davet silindiğinde tetiklenir"""
        guild_id = invite.guild.id
        if guild_id in self.invites_cache and invite.code in self.invites_cache[guild_id]:
            del self.invites_cache[guild_id][invite.code]
            
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Kullanıcı katıldığında tetiklenir"""
        if not self.config["enabled"] or member.bot:
            return
            
        guild = member.guild
        guild_id = guild.id
        inviter = None
        invite_code = None
        
        if guild.me.guild_permissions.manage_guild:
            try:
                # Davet kullanım durumunu kontrol et
                new_invites = await guild.invites()
                old_invites = self.invites_cache.get(guild_id, {})
                
                # Önbelleği güncelle
                self.invites_cache[guild_id] = {invite.code: invite.uses for invite in new_invites}
                
                # Kullanım sayısı artmış davetleri bul
                for invite in new_invites:
                    if invite.code in old_invites and invite.uses > old_invites[invite.code]:
                        inviter = invite.inviter
                        invite_code = invite.code
                        break
                        
                # Özel URL veya bilinmeyen bir davet
                if not inviter and guild.vanity_url_code:
                    invite_code = "vanity"
            except discord.Forbidden:
                await self.log_invite_event(guild_id, "❌ Davetleri görüntüleme iznim yok!")
            except Exception as e:
                await self.log_invite_event(guild_id, f"❌ Davet kontrolü sırasında hata: {e}")
                
        # Davetçiyi bulabildik mi?
        if inviter:
            # Kullanıcı zaten sunucudan ayrılıp tekrar katıldı mı kontrol et
            is_rejoining = False
            for user_id, data in self.invite_data.get(str(guild_id), {}).items():
                if str(member.id) in data.get("invitees", []):
                    is_rejoining = True
                    # Kullanıcı tekrar katıldığında eski davetçinin sahte davetini artırma
                    old_inviter_data = self.ensure_user_data(guild_id, user_id)
                    old_inviter_data["fake"] += 1
                    break
                    
            # Davet verilerini güncelle
            inviter_data = self.ensure_user_data(guild_id, inviter.id)
            
            if is_rejoining:
                inviter_data["fake"] += 1
            else:
                inviter_data["invites"] += 1
                inviter_data["invitees"].append(str(member.id))
                
            self.save_data()
            
            # Karşılama mesajı gönder
            await self.send_welcome_message(member, inviter, invite_code, is_rejoining)
            
            # Log
            if is_rejoining:
                await self.log_invite_event(guild_id, 
                    f"♻️ {member.mention} ({member.id}) tekrar katıldı. " 
                    f"Davetçi: {inviter.mention} ({inviter.id}) - Kod: {invite_code}")
            else:
                await self.log_invite_event(guild_id, 
                    f"✅ {member.mention} ({member.id}) katıldı. " 
                    f"Davetçi: {inviter.mention} ({inviter.id}) - Kod: {invite_code}")
            
            # Davet dolandırıcılığını kontrol et
            await self.check_invite_fraud(member, inviter)
        else:
            # Davetçi bulunamadı (özel URL, gizli, direkt bağlantı vb.)
            await self.send_welcome_message(member, None, invite_code, False)
            await self.log_invite_event(guild_id, 
                f"⚠️ {member.mention} ({member.id}) katıldı, " 
                f"fakat davetçi tespit edilemedi. (Muhtemel URL: {invite_code or 'Bilinmiyor'})")
                
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Kullanıcı ayrıldığında tetiklenir"""
        if not self.config["enabled"] or member.bot:
            return
            
        guild_id = str(member.guild.id)
        member_id = str(member.id)
        
        # Bu kullanıcıyı davet eden kişiyi bul
        inviter_id = None
        for user_id, data in self.invite_data.get(guild_id, {}).items():
            if member_id in data.get("invitees", []):
                inviter_id = user_id
                break
                
        # Davetçinin left sayısını artır
        if inviter_id:
            inviter_data = self.ensure_user_data(guild_id, inviter_id)
            inviter_data["left"] += 1
            self.save_data()
            
            # Log
            try:
                inviter = await self.bot.fetch_user(int(inviter_id))
                inviter_mention = inviter.mention
            except:
                inviter_mention = f"<@{inviter_id}>"
                
            await self.log_invite_event(member.guild.id, 
                f"🚪 {member.name}#{member.discriminator} ({member.id}) ayrıldı. " 
                f"Davetçi: {inviter_mention} ({inviter_id})")
        else:
            await self.log_invite_event(member.guild.id, 
                f"🚪 {member.name}#{member.discriminator} ({member.id}) ayrıldı. " 
                f"Davetçi bilgisi bulunamadı.")
                
    async def send_welcome_message(self, member, inviter, invite_code, is_rejoining):
        """Karşılama mesajı gönder"""
        if not self.config.get("welcome_channel_id"):
            return
            
        channel_id = int(self.config["welcome_channel_id"])
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
            
        if inviter:
            message = self.config["welcome_message"].format(
                user=member,
                inviter=inviter,
                guild=member.guild,
                code=invite_code,
                invite_count=self.get_effective_invites(member.guild.id, inviter.id),
                rejoining="tekrar katıldı" if is_rejoining else "katıldı"
            )
        else:
            message = self.config["welcome_with_unknown_inviter"].format(
                user=member,
                guild=member.guild,
                code=invite_code or "bilinmiyor",
                rejoining="tekrar katıldı" if is_rejoining else "katıldı"
            )
            
        embed = discord.Embed(
            title="👋 Yeni Üye!",
            description=message,
            color=discord.Color.green()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"{member.guild.name} | {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        await channel.send(embed=embed)
        
    async def log_invite_event(self, guild_id, message):
        """Davet olaylarını logla"""
        if not self.config.get("log_channel_id"):
            return
            
        try:
            channel_id = int(self.config["log_channel_id"])
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(message)
        except Exception:
            pass
            
    def get_effective_invites(self, guild_id, user_id):
        """Bir kullanıcının gerçek davet sayısını hesapla"""
        guild_id = str(guild_id)
        user_id = str(user_id)
        
        if guild_id not in self.invite_data or user_id not in self.invite_data[guild_id]:
            bonus = self.config.get("bonus_invites", {}).get(user_id, 0)
            return bonus
            
        data = self.invite_data[guild_id][user_id]
        regular_invites = data.get("invites", 0) - data.get("fake", 0) - data.get("left", 0)
        bonus = self.config.get("bonus_invites", {}).get(user_id, 0)
        
        return regular_invites + bonus
    
    @commands.group(name="davet", aliases=["invite", "invites"], invoke_without_command=True)
    async def davet_cmd(self, ctx, member: discord.Member = None):
        """Davet istatistiklerini görüntüle"""
        member = member or ctx.author
        
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        
        # Kullanıcının davet verilerini al
        invite_stats = self.invite_data.get(guild_id, {}).get(user_id, {})
        invites = invite_stats.get("invites", 0)
        fake = invite_stats.get("fake", 0)
        left = invite_stats.get("left", 0)
        
        # Bonus davetleri al
        bonus = self.config.get("bonus_invites", {}).get(user_id, 0)
        
        # Toplam davet sayısını hesapla
        total = invites - fake - left + bonus
        
        embed = discord.Embed(
            title=f"📊 Davet İstatistikleri | {member.display_name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="👥 Toplam Davetler", value=f"**{total}** davet", inline=False)
        embed.add_field(name="✅ Başarılı", value=f"{invites}", inline=True)
        embed.add_field(name="🔄 Tekrar Katılım", value=f"{fake}", inline=True)
        embed.add_field(name="🚪 Ayrılanlar", value=f"{left}", inline=True)
        
        if bonus > 0:
            embed.add_field(name="🎁 Bonus Davetler", value=f"{bonus}", inline=True)
            
        # Davet edilen kullanıcıları listeleme
        invitees = invite_stats.get("invitees", [])
        if invitees:
            # En son 5 daveti göster
            recent_invites = []
            for i, invitee_id in enumerate(invitees[-5:]):
                try:
                    user = await self.bot.fetch_user(int(invitee_id))
                    recent_invites.append(f"{user.mention}")
                except:
                    recent_invites.append(f"<@{invitee_id}>")
            
            if recent_invites:
                embed.add_field(
                    name=f"🔍 Son Davet Ettiği Kullanıcılar ({len(invitees)} toplam)",
                    value=", ".join(recent_invites),
                    inline=False
                )
                
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"{ctx.guild.name} | {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        await ctx.send(embed=embed)
    
    @davet_cmd.command(name="sıralama", aliases=["top", "leaderboard"])
    async def davet_siralama(self, ctx, limit: int = 10):
        """Davet sıralamasını görüntüle"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.invite_data:
            await ctx.send("❌ Bu sunucuda henüz davet verisi bulunmuyor.")
            return
            
        # Davet sıralamasını hesapla
        leaderboard = []
        for user_id, data in self.invite_data[guild_id].items():
            invites = data.get("invites", 0)
            fake = data.get("fake", 0)
            left = data.get("left", 0)
            bonus = self.config.get("bonus_invites", {}).get(user_id, 0)
            
            total = invites - fake - left + bonus
            if total > 0:  # Sadece pozitif davetleri göster
                leaderboard.append((user_id, total, invites, fake, left, bonus))
                
        # Toplam davet sayısına göre sırala
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        leaderboard = leaderboard[:limit]  # Limit uygula
        
        if not leaderboard:
            await ctx.send("❌ Şu anda görüntülenecek davet verisi bulunmuyor.")
            return
            
        embed = discord.Embed(
            title=f"🏆 Davet Sıralaması | Top {len(leaderboard)}",
            description="Bu sunucudaki en fazla davete sahip kullanıcılar:",
            color=discord.Color.gold()
        )
        
        # Sıralamayı embed'e ekle
        for i, (user_id, total, invites, fake, left, bonus) in enumerate(leaderboard, 1):
            try:
                user = await self.bot.fetch_user(int(user_id))
                user_display = user.mention
            except:
                user_display = f"<@{user_id}>"
                
            value = f"**{total}** davet: ✅ {invites} başarılı"
            
            if fake > 0:
                value += f", 🔄 {fake} tekrar"
                
            if left > 0:
                value += f", 🚪 {left} ayrılan"
                
            if bonus > 0:
                value += f", 🎁 {bonus} bonus"
                
            embed.add_field(
                name=f"{i}. {user_display}",
                value=value,
                inline=False
            )
            
        embed.set_footer(text=f"{ctx.guild.name} | {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        await ctx.send(embed=embed)
        
    @davet_cmd.command(name="bonus")
    @has_admin()
    async def davet_bonus(self, ctx, member: discord.Member, amount: int = None):
        """Bir kullanıcıya bonus davet ver veya mevcut bonusu görüntüle"""
        user_id = str(member.id)
        
        if amount is None:
            # Mevcut bonus davet sayısını göster
            bonus = self.config.get("bonus_invites", {}).get(user_id, 0)
            await ctx.send(f"🎁 {member.mention} kullanıcısının **{bonus}** bonus daveti bulunuyor.")
            return
            
        # Bonus davet ver
        if "bonus_invites" not in self.config:
            self.config["bonus_invites"] = {}
            
        self.config["bonus_invites"][user_id] = amount
        
        # Config dosyasını güncelle
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
            
        await ctx.send(f"✅ {member.mention} kullanıcısının bonus davet sayısı **{amount}** olarak ayarlandı.")
        
    @davet_cmd.command(name="sıfırla", aliases=["reset"])
    @has_admin()
    async def davet_sifirla(self, ctx, member: typing.Optional[discord.Member] = None):
        """Bir kullanıcının veya sunucunun tüm davet istatistiklerini sıfırla"""
        guild_id = str(ctx.guild.id)
        
        if member:
            # Belirtilen kullanıcının davetlerini sıfırla
            user_id = str(member.id)
            if guild_id in self.invite_data and user_id in self.invite_data[guild_id]:
                del self.invite_data[guild_id][user_id]
                self.save_data()
                await ctx.send(f"✅ {member.mention} kullanıcısının davet istatistikleri sıfırlandı.")
            else:
                await ctx.send("❌ Bu kullanıcı için davet verisi bulunamadı.")
        else:
            # Tüm sunucunun davetlerini sıfırla
            confirm_msg = await ctx.send("⚠️ Bu işlem sunucudaki TÜM davet istatistiklerini silecek. Emin misiniz? (evet/hayır)")
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["evet", "hayır", "e", "h"]
            
            try:
                response = await self.bot.wait_for('message', check=check, timeout=30)
                
                if response.content.lower() in ["evet", "e"]:
                    if guild_id in self.invite_data:
                        del self.invite_data[guild_id]
                        self.save_data()
                    await ctx.send("✅ Sunucunun tüm davet istatistikleri sıfırlandı.")
                else:
                    await ctx.send("❌ İşlem iptal edildi.")
            except asyncio.TimeoutError:
                await ctx.send("❌ Zaman aşımı, işlem iptal edildi.")
                
    @davet_cmd.command(name="ayarlar", aliases=["config"])
    @has_admin()
    async def davet_ayarlar(self, ctx, setting: str = None, *, value = None):
        """Davet takip ayarlarını görüntüle veya değiştir"""
        if setting is None:
            # Ayarları görüntüle
            embed = discord.Embed(
                title="⚙️ Davet Takip Ayarları",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="🔄 Durum",
                value="✅ Aktif" if self.config["enabled"] else "❌ Devre dışı",
                inline=False
            )
            
            welcome_channel = "Ayarlanmamış"
            if self.config.get("welcome_channel_id"):
                channel = self.bot.get_channel(int(self.config["welcome_channel_id"]))
                welcome_channel = channel.mention if channel else f"ID: {self.config['welcome_channel_id']} (Bulunamadı)"
                
            log_channel = "Ayarlanmamış"
            if self.config.get("log_channel_id"):
                channel = self.bot.get_channel(int(self.config["log_channel_id"]))
                log_channel = channel.mention if channel else f"ID: {self.config['log_channel_id']} (Bulunamadı)"
                
            embed.add_field(name="👋 Karşılama Kanalı", value=welcome_channel, inline=True)
            embed.add_field(name="📝 Log Kanalı", value=log_channel, inline=True)
            
            welcome_msg = self.config.get("welcome_message", "Ayarlanmamış")
            welcome_unknown = self.config.get("welcome_with_unknown_inviter", "Ayarlanmamış")
            
            embed.add_field(name="💬 Karşılama Mesajı", value=f"```{welcome_msg}```", inline=False)
            embed.add_field(name="🔍 Bilinmeyen Davetçi Mesajı", value=f"```{welcome_unknown}```", inline=False)
            
            bonus_count = len(self.config.get("bonus_invites", {}))
            embed.add_field(name="🎁 Bonus Davetler", value=f"{bonus_count} kullanıcı için tanımlanmış", inline=False)
            
            embed.set_footer(text=f"{ctx.guild.name} | Değiştirmek için: !davet ayarlar <ayar> <değer>")
            
            await ctx.send(embed=embed)
            return
            
        # Ayarları değiştir
        setting = setting.lower()
        valid_settings = ["enabled", "welcome_channel_id", "log_channel_id", "welcome_message", "welcome_with_unknown_inviter"]
        
        if setting not in valid_settings:
            await ctx.send(f"❌ Geçersiz ayar. Geçerli ayarlar: {', '.join(valid_settings)}")
            return
            
        if value is None:
            await ctx.send(f"❌ Lütfen bir değer belirtin: `!davet ayarlar {setting} <değer>`")
            return
            
        try:
            if setting == "enabled":
                if value.lower() in ["true", "yes", "1", "on", "açık", "aktif"]:
                    self.config[setting] = True
                elif value.lower() in ["false", "no", "0", "off", "kapalı", "devre dışı"]:
                    self.config[setting] = False
                else:
                    await ctx.send("❌ Geçersiz değer. `true/false`, `yes/no`, `1/0` değerlerinden birini kullanın.")
                    return
            elif setting in ["welcome_channel_id", "log_channel_id"]:
                # Kanal ID veya etiket
                if value.startswith("<#") and value.endswith(">"):
                    channel_id = int(value[2:-1])
                else:
                    channel = await commands.TextChannelConverter().convert(ctx, value)
                    channel_id = channel.id
                self.config[setting] = channel_id
            else:
                # Diğer string ayarlar
                self.config[setting] = value
                
            # Config dosyasını güncelle
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
                
            await ctx.send(f"✅ `{setting}` ayarı güncellendi.")
            
        except (commands.BadArgument, ValueError):
            await ctx.send(f"❌ Geçersiz değer. Lütfen tekrar deneyin.")
        except Exception as e:
            await ctx.send(f"❌ Ayar güncellenirken hata: {e}")
    
    @davet_cmd.command(name="görüntüle", aliases=["view"])
    async def davet_goruntule(self, ctx, member: discord.Member = None):
        """Davet istatistiklerini etkileşimli olarak görüntüle"""
        member = member or ctx.author
        
        def create_invite_embed(self, member):
            guild_id = str(member.guild.id)
            user_id = str(member.id)
            
            # Kullanıcının davet verilerini al
            invite_stats = self.invite_data.get(guild_id, {}).get(user_id, {})
            invites = invite_stats.get("invites", 0)
            fake = invite_stats.get("fake", 0)
            left = invite_stats.get("left", 0)
            bonus = self.config.get("bonus_invites", {}).get(user_id, 0)
            total = invites - fake - left + bonus
            
            embed = discord.Embed(
                title=f"📊 Davet Profili | {member.display_name}",
                description=f"{member.mention} kullanıcısının detaylı davet istatistikleri:",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="👥 Toplam Davetler", value=f"**{total}** davet", inline=False)
            embed.add_field(name="✅ Başarılı", value=f"{invites}", inline=True)
            embed.add_field(name="🔄 Tekrar Katılım", value=f"{fake}", inline=True)
            embed.add_field(name="🚪 Ayrılanlar", value=f"{left}", inline=True)
            
            if bonus > 0:
                embed.add_field(name="🎁 Bonus Davetler", value=f"{bonus}", inline=True)
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"{member.guild.name} | {datetime.now().strftime('%d.%m.%Y %H:%M')}")
            
            return embed
            
        # Temel embed içeriğini oluştur
        embed = create_invite_embed(self, member)
        
        # Butonları ekle
        view = discord.ui.View(timeout=60)
        view.add_item(discord.ui.Button(label="Davet Edenler", custom_id="inviter_list", style=discord.ButtonStyle.primary))
        view.add_item(discord.ui.Button(label="Grafikler", custom_id="invite_graph", style=discord.ButtonStyle.success))
        
        await ctx.send(embed=embed, view=view)

    @davet_cmd.command(name="istatistik", aliases=["stats"])
    async def davet_istatistik(self, ctx):
        """Sunucu davet istatistiklerini göster"""
        guild_id = str(ctx.guild.id)
        
        # Temel veriler
        total_users = 0
        total_invites = 0
        active_inviters = 0
        
        if guild_id in self.invite_data:
            total_users = len(self.invite_data[guild_id])
            
            for user_id, data in self.invite_data[guild_id].items():
                invites = data.get("invites", 0)
                fake = data.get("fake", 0)
                left = data.get("left", 0)
                bonus = self.config.get("bonus_invites", {}).get(user_id, 0)
                
                total = invites - fake - left + bonus
                total_invites += total
                
                if total > 0:
                    active_inviters += 1
        
        embed = discord.Embed(
            title="📊 Sunucu Davet İstatistikleri",
            description="Bu sunucunun genel davet istatistikleri:",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="👥 Toplam Davetler", value=f"{total_invites}", inline=True)
        embed.add_field(name="👤 Aktif Davetçiler", value=f"{active_inviters}", inline=True)
        embed.add_field(name="📈 Takip Edilen Kullanıcılar", value=f"{total_users}", inline=True)
        
        embed.set_footer(text=f"{ctx.guild.name} | {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        await ctx.send(embed=embed)

    @davet_cmd.command(name="oluştur", aliases=["create"])
    @commands.has_permissions(create_instant_invite=True)
    async def davet_olustur(self, ctx, max_uses: int = 0, duration: int = 0, reason: str = "Davet Takip Sistemi"):
        """Özel davet bağlantısı oluştur ve takip et"""
        invite = await ctx.channel.create_invite(
            max_uses=max_uses, 
            max_age=duration, 
            reason=f"{ctx.author} tarafından oluşturuldu: {reason}"
        )
        
        embed = discord.Embed(
            title="🔗 Davet Bağlantısı Oluşturuldu",
            description=f"**Bağlantı:** {invite.url}\n"
                       f"**Maksimum Kullanım:** {max_uses if max_uses > 0 else 'Sınırsız'}\n"
                       f"**Süre:** {duration if duration > 0 else 'Sınırsız'} saniye\n"
                       f"**Sebep:** {reason}",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Bot yeni bir sunucuya eklendiğinde tetiklenir"""
        await self.initialize_invites()
        
    def cog_unload(self):
        """Cog kapatılırken çalışır"""
        self.save_data()

    async def check_invite_fraud(self, member, inviter):
        """Davet dolandırıcılığını tespit etme"""
        fraud_detected = False  # Dolandırıcılık kontrolü yapılmalı
        
        if fraud_detected:
            await self.log_invite_event(member.guild.id, 
                f"⚠️ **UYARI**: {inviter.mention} ({inviter.id}) için şüpheli davet davranışı tespit edildi!")

    def optimize_invite_data(self):
        """Davet verilerini optimize et"""
        for guild_id in list(self.invite_data.keys()):
            try:
                guild = self.bot.get_guild(int(guild_id))
                if not guild:  # Sunucuda değilsek verileri temizle
                    del self.invite_data[guild_id]
                    continue
                    
                # Artık sunucuda olmayan kullanıcıların verilerini temizle
                for user_id in list(self.invite_data[guild_id].keys()):
                    if len(self.invite_data[guild_id][user_id]["invitees"]) == 0:
                        if (self.invite_data[guild_id][user_id]["invites"] == 0 and
                            self.invite_data[guild_id][user_id]["fake"] == 0 and
                            self.invite_data[guild_id][user_id]["left"] == 0):
                            del self.invite_data[guild_id][user_id]
            except Exception as e:
                print(f"Davet verisi optimize edilirken hata: {e}")

async def setup(bot):
    await bot.add_cog(InviteTracker(bot))
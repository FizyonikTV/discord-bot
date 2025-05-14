import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
from collections import deque
import json
import os
import random
from utils.permissions import has_mod_role, has_admin

class RaidProtection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = "config/raid_config.json"
        self.recent_joins = deque(maxlen=50)  # Son katılımları sakla
        self.raid_mode = False
        self.raid_end_time = None
        self.verified_users = set()
        self.load_config()
        self.raid_check.start()
    
    def load_config(self):
        """Raid koruma yapılandırmasını yükle"""
        default_config = {
            "enabled": True,
            "threshold": 10,  # Kaç kullanıcı
            "time_window": 30,  # Kaç saniyede
            "raid_action": "verification",  # "verification" veya "lockdown"
            "raid_timeout": 10,  # Raid modu kaç dakika sürsün
            "exempt_roles": [],
            "verification_message": "Sunucumuz şu anda raid koruması altındadır. Lütfen bir emoji ile tepki vererek insan olduğunuzu doğrulayın.",
            "log_channel_id": None,  # Raid log kanalı ID
            "verification_channel_id": None,  # Doğrulama kanalı ID
            "verified_role_id": None  # Doğrulanan kullanıcılara verilecek rol ID
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
            print(f"Raid koruma yapılandırması yüklenirken hata: {e}")
            self.config = default_config
    
    @tasks.loop(seconds=5.0)
    async def raid_check(self):
        """Periyodik olarak raid kontrolü yap"""
        if not self.config["enabled"]:
            return
            
        now = datetime.utcnow()
        
        # Raid modu zaten aktifse, süreyi kontrol et
        if self.raid_mode and self.raid_end_time and now > self.raid_end_time:
            await self.end_raid_mode()
            return
        
        # Son katılımları kontrol et
        threshold_time = now - timedelta(seconds=self.config["time_window"])
        recent_count = sum(1 for join_time in self.recent_joins if join_time > threshold_time)
        
        # Eşik değerini aştıysa raid modu başlat
        if recent_count >= self.config["threshold"] and not self.raid_mode:
            await self.start_raid_mode()
    
    @raid_check.before_loop
    async def before_raid_check(self):
        await self.bot.wait_until_ready()
    
    async def start_raid_mode(self):
        """Raid modunu başlat"""
        self.raid_mode = True
        self.raid_end_time = datetime.utcnow() + timedelta(minutes=self.config["raid_timeout"])
        
        # Log kanalına bildirim gönder
        await self.log_raid_event(f"⚠️ **RAID ALARMI** ⚠️\n"
                                 f"{self.config['time_window']} saniyede {len(self.recent_joins)} yeni üye katıldı.\n"
                                 f"Raid koruması aktifleştirildi. Koruma modu: **{self.config['raid_action']}**\n"
                                 f"Koruma {self.config['raid_timeout']} dakika boyunca aktif kalacak.")
        
        # Raid koruma tipine göre işlem yap
        if self.config["raid_action"] == "lockdown":
            await self.activate_lockdown()
        elif self.config["raid_action"] == "verification":
            await self.activate_verification()
    
    async def end_raid_mode(self):
        """Raid modunu sonlandır"""
        self.raid_mode = False
        self.raid_end_time = None
        
        # Log kanalına bildirim gönder
        await self.log_raid_event("✅ **Raid koruması sona erdi**\n"
                                 "Sunucu normal moduna döndü.")
        
        # Raid koruma tipine göre temizleme işlemi yap
        if self.config["raid_action"] == "lockdown":
            await self.deactivate_lockdown()
        self.verified_users.clear()
    
    async def activate_lockdown(self):
        """Sunucuyu kilitle"""
        for guild in self.bot.guilds:
            try:
                # Tüm kanalları kilitle
                for channel in guild.text_channels:
                    default_role = guild.default_role
                    await channel.set_permissions(default_role, send_messages=False)
            except discord.Forbidden:
                await self.log_raid_event("❌ Sunucuyu kilitleme iznim yok!")
            except Exception as e:
                await self.log_raid_event(f"❌ Sunucu kilitlenirken hata: {e}")
    
    async def deactivate_lockdown(self):
        """Sunucu kilidini kaldır"""
        for guild in self.bot.guilds:
            try:
                # Tüm kanalların kilidini kaldır
                for channel in guild.text_channels:
                    default_role = guild.default_role
                    await channel.set_permissions(default_role, send_messages=None)
            except discord.Forbidden:
                await self.log_raid_event("❌ Sunucu kilidini kaldırma iznim yok!")
            except Exception as e:
                await self.log_raid_event(f"❌ Sunucu kilidi kaldırılırken hata: {e}")
    
    async def activate_verification(self):
        """Doğrulama sistemini aktifleştir"""
        # Doğrulama kanalı belirlenmişse
        if self.config.get("verification_channel_id"):
            try:
                channel_id = int(self.config["verification_channel_id"])
                channel = self.bot.get_channel(channel_id)
                if channel:
                    emojis = ["✅", "🔒", "🛡️", "🤖", "🔐"]
                    selected_emoji = random.choice(emojis)
                    
                    embed = discord.Embed(
                        title="🔐 Sunucu Güvenlik Doğrulaması",
                        description=f"**{channel.guild.name}** sunucusu şu anda raid koruması altındadır.",
                        color=0xFF5733  # Turuncu/kırmızı tonlarında bir renk
                    )
                    
                    # Görsel olarak dikkat çeken bir mesaj
                    embed.add_field(
                        name="❓ Ne Yapmalıyım?", 
                        value=f"Aşağıdaki **{selected_emoji}** emojisine tıklayarak insan olduğunuzu doğrulayın.\n"
                              f"Doğrulama başarılı olursa sunucuya erişiminiz sağlanacaktır.", 
                        inline=False
                    )
                    
                    # Kalan süreyi gösterelim
                    raid_end = datetime.utcnow() + timedelta(minutes=self.config["raid_timeout"])
                    minutes_left = self.config["raid_timeout"]
                    embed.add_field(
                        name="⏰ Süre", 
                        value=f"Bu önlem yaklaşık **{minutes_left} dakika** süreyle aktif olacaktır.", 
                        inline=False
                    )
                    
                    # Açıklama ve görselleştirme
                    embed.set_thumbnail(url="https://www.freeiconspng.com/thumbs/lock-icon/lock-icon-11.png")  # Kilit/güvenlik ikonu
                    embed.set_image(url="https://i.ibb.co/6RQcJQVX/Lunaris-Banner-Ekstra-Orijinal.webp")  # Dikkat çeken bir banner
                    embed.set_footer(text=f"LunarisBot Raid Koruması | {channel.guild.name}", icon_url=channel.guild.icon.url if channel.guild.icon else None)
                    embed.timestamp = datetime.utcnow()
                    
                    message = await channel.send(embed=embed)
                    await message.add_reaction(selected_emoji)
                    
                    # Tepki bekleyen mesajı sakla
                    self.verification_message_id = message.id
                    self.verification_emoji = selected_emoji
            except Exception as e:
                await self.log_raid_event(f"❌ Doğrulama sistemi başlatılırken hata: {e}")
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Reaksiyon eklendiğinde kontrol et"""
        if user.bot or not self.raid_mode or self.config["raid_action"] != "verification":
            return
            
        if not hasattr(self, 'verification_message_id') or reaction.message.id != self.verification_message_id:
            return
            
        if str(reaction.emoji) == self.verification_emoji:
            self.verified_users.add(user.id)
            
            # Doğrulanmış rol atama
            if self.config.get("verified_role_id"):
                try:
                    guild = reaction.message.guild
                    member = guild.get_member(user.id)
                    role = guild.get_role(int(self.config["verified_role_id"]))
                    if role and member:
                        await member.add_roles(role)
                        await self.log_raid_event(f"✅ {user.mention} ({user.id}) doğrulandı ve {role.name} rolü verildi.")
                except Exception as e:
                    await self.log_raid_event(f"❌ Rol verme hatası: {e}")
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Kullanıcı katıldığında tetiklenir"""
        # Katılım zamanını kaydet
        join_time = datetime.utcnow()
        self.recent_joins.append(join_time)
        
        # Raid modu aktifse ve doğrulama gerektiriyorsa
        if self.raid_mode and self.config["raid_action"] == "verification":
            if self.config.get("verification_channel_id"):
                try:
                    channel_id = int(self.config["verification_channel_id"])
                    channel = member.guild.get_channel(channel_id)
                    if channel:
                        await channel.send(f"{member.mention}, sunucumuz şu anda raid koruması altındadır. "
                                           f"Lütfen yukarıdaki mesajdaki emojiyi kullanarak insan olduğunuzu doğrulayın.")
                except Exception:
                    pass
        
        # Log
        if self.raid_mode:
            await self.log_raid_event(f"👤 {member.mention} ({member.id}) raid modu sırasında katıldı.")
    
    async def log_raid_event(self, message):
        """Raid olaylarını loglama"""
        if not self.config.get("log_channel_id"):
            return
            
        try:
            channel_id = int(self.config["log_channel_id"])
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(message)
        except Exception:
            pass
    
    @commands.group(name="raid", invoke_without_command=True)
    @has_admin()
    async def raid_commands(self, ctx):
        """Raid koruma komutları"""
        embed = discord.Embed(
            title="🛡️ Raid Koruma Komutları",
            description="Sunucunuzu raid saldırılarına karşı korumak için aşağıdaki komutları kullanabilirsiniz:",
            color=discord.Color.blue()
        )
        
        # Komutların daha görsel olması için emoji ekleyelim
        embed.add_field(name="📊 `!raid status`", value="Raid koruma sisteminin durumunu gösterir", inline=False)
        embed.add_field(name="🔄 `!raid toggle`", value="Raid korumayı açar/kapatır", inline=False)
        embed.add_field(name="⚙️ `!raid settings`", value="Raid koruma ayarlarını gösterir", inline=False)
        embed.add_field(name="🔧 `!raid set <ayar> <değer>`", value="Raid ayarlarını değiştirir", inline=False)
        
        # Görsel iyileştirmeler
        embed.set_thumbnail(url="https://e7.pngegg.com/pngimages/599/185/png-clipart-logo-shield-black-shield-white-and-black-shield-logo-emblem-monochrome-thumbnail.png")  # Kalkan/koruma ikonu
        embed.set_footer(text=f"LunarisBot Raid Koruması | {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed.timestamp = datetime.utcnow()
        
        await ctx.send(embed=embed)
    
    @raid_commands.command(name="status")
    @has_admin()
    async def raid_status(self, ctx):
        """Raid koruması durum bilgisi"""
        embed = discord.Embed(
            title="🛡️ Raid Koruma Durumu",
            description="Sunucunuzun şu anki raid koruma durumu aşağıda detaylı olarak gösterilmiştir.",
            color=discord.Color.green() if self.config["enabled"] else discord.Color.red()
        )
        
        # Durum göstergesi
        status = "✅ Aktif" if self.config["enabled"] else "❌ Devre dışı"
        raid_mode = "🔴 Aktif" if self.raid_mode else "🟢 Pasif"
        
        # İnline fields kullanarak daha kompakt görünüm
        embed.add_field(name="🔐 Koruma", value=status, inline=True)
        embed.add_field(name="🚨 Raid Modu", value=raid_mode, inline=True)
        embed.add_field(name="🛠️ Koruma Tipi", value=f"`{self.config['raid_action']}`", inline=True)
        
        # Eşik değerleri için progress bar benzeri görsel iyileştirme
        threshold_display = f"```{self.config['threshold']} kullanıcı / {self.config['time_window']} saniye```"
        embed.add_field(name="📈 Eşik Değeri", value=threshold_display, inline=False)
        
        # Eğer raid modu aktifse kalan süreyi göster
        if self.raid_mode and self.raid_end_time:
            remaining = self.raid_end_time - datetime.utcnow()
            minutes, seconds = divmod(int(remaining.total_seconds()), 60)
            time_bar = self.generate_time_bar(remaining.total_seconds(), self.config["raid_timeout"] * 60)
            embed.add_field(name="⏱️ Kalan Süre", 
                           value=f"```{minutes} dakika, {seconds} saniye\n{time_bar}```", 
                           inline=False)
        
        # Son katılım istatistiği
        recent_joins_count = len([t for t in self.recent_joins if t > datetime.utcnow() - timedelta(minutes=5)])
        embed.add_field(name="👥 Son Katılımlar (5 dk)", value=f"```{recent_joins_count} kullanıcı```", inline=False)
        
        # Görsel iyileştirmeler
        embed.set_thumbnail(url="https://e7.pngegg.com/pngimages/290/256/png-clipart-blades-in-the-dark-radar-computer-icons-management-radar-miscellaneous-game.png")  # Radar/alarm ikonu
        embed.set_footer(text=f"LunarisBot Raid Koruması | {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed.timestamp = datetime.utcnow()
        
        await ctx.send(embed=embed)
    
    @raid_commands.command(name="toggle")
    @has_admin()
    async def raid_toggle(self, ctx):
        """Raid korumasını açıp kapatma"""
        self.config["enabled"] = not self.config["enabled"]
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        
        status = "aktifleştirildi ✅" if self.config["enabled"] else "devre dışı bırakıldı ❌"
        await ctx.send(f"Raid koruma {status}")
    
    @raid_commands.command(name="settings")
    @has_admin()
    async def raid_settings(self, ctx):
        """Raid koruma ayarlarını göster"""
        embed = discord.Embed(
            title="⚙️ Raid Koruma Ayarları",
            description="Aşağıda sunucunuzun raid koruması için yapılandırılmış tüm ayarlar bulunmaktadır.",
            color=discord.Color.gold()
        )
        
        # Temel Ayarlar
        basic_settings = (
            f"**Koruma Durumu:** {'✅ Aktif' if self.config['enabled'] else '❌ Devre dışı'}\n"
            f"**Koruma Tipi:** `{self.config['raid_action']}`\n"
            f"**Raid Süresi:** `{self.config['raid_timeout']}` dakika\n"
        )
        embed.add_field(name="🔧 Temel Ayarlar", value=basic_settings, inline=False)
        
        # Eşik Değerleri - Bu kritik bir ayar, detaylı açıklayalım
        threshold_info = (
            f"**Eşik:** `{self.config['threshold']}` kullanıcı / `{self.config['time_window']}` saniye\n\n"
            f"👉 Bu, raid alarmının tetiklenmesi için:\n"
            f"   *{self.config['time_window']} saniye* içinde *{self.config['threshold']} kullanıcı* sunucuya katılmalıdır."
        )
        embed.add_field(name="📊 Raid Algılama Eşiği", value=threshold_info, inline=False)
        
        # Kanal ve Rol Ayarları
        channel_settings = []
        
        # Log kanalı
        log_channel = "Ayarlanmamış ⚠️"
        if self.config.get("log_channel_id"):
            channel = self.bot.get_channel(int(self.config["log_channel_id"]))
            log_channel = f"{channel.mention}" if channel else f"ID: {self.config['log_channel_id']} (Bulunamadı ⚠️)"
        channel_settings.append(f"**Log Kanalı:** {log_channel}")
        
        # Doğrulama kanalı
        verification_channel = "Ayarlanmamış ⚠️"
        if self.config.get("verification_channel_id"):
            channel = self.bot.get_channel(int(self.config["verification_channel_id"]))
            verification_channel = f"{channel.mention}" if channel else f"ID: {self.config['verification_channel_id']} (Bulunamadı ⚠️)"
        channel_settings.append(f"**Doğrulama Kanalı:** {verification_channel}")
        
        # Doğrulanmış rol
        verified_role = "Ayarlanmamış ⚠️"
        if self.config.get("verified_role_id") and ctx.guild:
            role = ctx.guild.get_role(int(self.config["verified_role_id"]))
            verified_role = f"@{role.name}" if role else f"ID: {self.config['verified_role_id']} (Bulunamadı ⚠️)"
        channel_settings.append(f"**Doğrulama Rolü:** {verified_role}")
        
        embed.add_field(name="📌 Kanal ve Rol Ayarları", value="\n".join(channel_settings), inline=False)
        
        # Açıklamalar ve Bilgiler
        descriptions = {
            "verification": "Kullanıcıların emoji ile tepki vererek insan olduklarını doğrulamaları gerekir.",
            "lockdown": "Sunucudaki tüm kanallarda mesaj gönderme izni geçici olarak kaldırılır."
        }
        
        action_desc = descriptions.get(self.config["raid_action"], "Belirtilmemiş koruma tipi")
        embed.add_field(
            name="ℹ️ Koruma Tipi Açıklaması", 
            value=f"`{self.config['raid_action']}`: {action_desc}",
            inline=False
        )
        
        # Ayarları Değiştirme Talimatları
        embed.add_field(
            name="🔧 Ayarları Değiştirmek İçin",
            value="Herhangi bir ayarı değiştirmek için şu komutu kullanabilirsiniz:\n"
                  "`!raid set <ayar> <değer>`\n\n"
                  "**Örnek:**\n"
                  "`!raid set threshold 15` - Eşik değerini 15 kullanıcıya ayarlar\n"
                  "`!raid set time_window 60` - Zaman penceresini 60 saniyeye ayarlar\n"
                  "`!raid set log_channel_id #raid-log` - Log kanalını ayarlar\n"
                  "`!raid set verification_channel_id #dogrulama` - Doğrulama kanalını ayarlar\n"
                  "`!raid set verified_role_id @Doğrulanmış` - Doğrulama rolünü ayarlar\n"
                  "`!raid set raid_action lockdown` - Koruma tipini değiştirir (verification veya lockdown)",
            inline=False
        )
        
        # Görsel iyileştirmeler
        embed.set_thumbnail(url="https://i.imgur.com/xG2zJ8o.png")  # Ayarlar ikonu
        embed.set_footer(text=f"LunarisBot Raid Koruması | {ctx.guild.name}", icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed.timestamp = datetime.utcnow()
        
        await ctx.send(embed=embed)

    @raid_commands.command(name="set")
    @has_admin()
    async def raid_set(self, ctx, setting: str = None, *, value = None):
        """Raid koruma ayarlarını değiştir"""
        if setting is None or value is None:
            await ctx.send("⚠️ Lütfen bir ayar ve değer belirtin: `!raid set <ayar> <değer>`")
            return
        
        setting = setting.lower()
        valid_settings = {
            "enabled": bool,
            "threshold": int,
            "time_window": int,
            "raid_action": str,
            "raid_timeout": int,
            "log_channel_id": discord.TextChannel,
            "verification_channel_id": discord.TextChannel,
            "verified_role_id": discord.Role
        }
        
        if setting not in valid_settings:
            valid_settings_list = ", ".join(f"`{s}`" for s in valid_settings.keys())
            await ctx.send(f"⚠️ Geçersiz ayar. Geçerli ayarlar: {valid_settings_list}")
            return
        
        # Özel durumlar için değeri dönüştür
        try:
            if setting in ["log_channel_id", "verification_channel_id"]:
                # Kanal ID'sini al
                if value.startswith("<#") and value.endswith(">"):
                    channel_id = value[2:-1]
                else:
                    channel = await commands.TextChannelConverter().convert(ctx, value)
                    channel_id = channel.id
                self.config[setting] = channel_id
            
            elif setting == "verified_role_id":
                # Rol ID'sini al
                if value.startswith("<@&") and value.endswith(">"):
                    role_id = value[3:-1]
                else:
                    role = await commands.RoleConverter().convert(ctx, value)
                    role_id = role.id
                self.config[setting] = role_id
            
            elif setting == "enabled":
                # Boolean değere dönüştür
                if value.lower() in ["true", "yes", "1", "on", "açık", "aktif"]:
                    self.config[setting] = True
                elif value.lower() in ["false", "no", "0", "off", "kapalı", "devre dışı"]:
                    self.config[setting] = False
                else:
                    await ctx.send("⚠️ Geçersiz değer. `enabled` ayarı için: true/false, yes/no, 1/0, on/off değerlerini kullanabilirsiniz.")
                    return
            
            elif setting == "raid_action":
                # Raid action tipini kontrol et
                if value.lower() not in ["verification", "lockdown"]:
                    await ctx.send("⚠️ Geçersiz değer. `raid_action` ayarı için: `verification` veya `lockdown` kullanabilirsiniz.")
                    return
                self.config[setting] = value.lower()
            
            else:
                # Diğer ayarlar için tür dönüşümü yap
                if valid_settings[setting] == int:
                    self.config[setting] = int(value)
                else:
                    self.config[setting] = value
        except (commands.BadArgument, ValueError):
            await ctx.send(f"⚠️ Geçersiz değer. `{setting}` ayarı için uygun bir değer giriniz.")
            return
        
        # Ayarları kaydet
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            # Başarı mesajı
            embed = discord.Embed(
                title="✅ Ayar Güncellendi",
                description=f"`{setting}` ayarı güncellendi.",
                color=discord.Color.green()
            )
            embed.add_field(name="Yeni Değer", value=f"`{self.config[setting]}`", inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Ayar kaydedilirken hata oluştu: {e}")
    
    def cog_unload(self):
        self.raid_check.cancel()

    def generate_time_bar(self, current_seconds, total_seconds, bar_length=20):
        """Kalan süreyi görsel olarak gösteren bir bar oluşturur"""
        progress = 1 - (current_seconds / total_seconds)  # Terse çevir (kalan zaman değil ilerleme)
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        percent = int(progress * 100)
        return f"{bar} {percent}%"

async def setup(bot):
    await bot.add_cog(RaidProtection(bot))
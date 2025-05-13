import discord
from discord.ext import commands
import re
import json
import os
import asyncio
from datetime import datetime, timedelta
from config.config import BAN_LOG_KANAL_ID, WARN_LOG_KANAL_ID, TIMEOUT_LOG_KANAL_ID, YASAKLI

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_check = {}  # Kullanıcı mesaj geçmişini izlemek için
        self.violation_counts = {}  # Yasaklı kelime ihlallerini izlemek için
        self.config_path = "config/automod_config.json"
        self.notes_file = "data/notes.json"
        self.regex_patterns = []
        self.load_config()
        self.load_notes()
        self.load_regex_patterns()
        
    def load_config(self):
        """Yapılandırma dosyasını yükler veya oluşturur"""
        default_config = {
            "enabled": True,
            "blacklisted_words": [
                # Türkçe yasaklı kelimeler
                "amcık", "amk", "ananı", "ananızı", "orospu", "piç", "siktiğimin", "sikeyim",
                "götveren", "yarak", "yarrak", "aq", "sikerim", "sikim", "sikik", "amına",
                "pezevenk", "ibne", "oç", "orspu", "gavat", "amına koyayım", "amına koyim",
                
                # İngilizce yasaklı kelimeler
                "fuck", "fucking", "shit", "bitch", "asshole", "cunt", "dick", "pussy", 
                "nigga", "nigger", "faggot", "retard", "whore", "slut", "motherfucker",
                "cocksucker", "bastard", "twat"
            ],
            "blacklisted_domains": [
                "discord.gg/", 
                "discordapp.com/invite/", 
                "discord.com/invite/",
                "pornhub.com", 
                "xvideos.com", 
                "xnxx.com",
                "onlyfans.com"
            ],
            "max_mentions": 5,
            "max_messages": 5,
            "time_window": 5,  # saniye cinsinden
            "violation_reset_time": 7,  # gün cinsinden - ihlaller kaç gün sonra sıfırlanacak
            "exempted_roles": [],
            "exempted_channels": [],
            "log_channel": BAN_LOG_KANAL_ID
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                    # Yeni değerler eklenmiş olabilir, mevcut yapılandırmayı default ile birleştir
                    for key, value in default_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                            
                    self.config = loaded_config
            else:
                self.config = default_config
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Otomatik moderasyon yapılandırma yüklenirken hata: {e}")
            self.config = default_config
    
    def save_config(self):
        """Yapılandırma dosyasını kaydeder"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Otomatik moderasyon yapılandırma kaydedilirken hata: {e}")
            return False
    
    def load_notes(self):
        """Moderasyon notlarını yükler"""
        try:
            with open(self.notes_file, "r", encoding="utf-8") as f:
                self.notes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.notes = {}
            self.save_notes()
            
    def save_notes(self):
        """Moderasyon notlarını kaydeder"""
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Moderasyon notları kaydedilirken hata: {e}")
            return False

    def reload_notes_from_file(self):
        """notes.json dosyasını yeniden yükle"""
        try:
            with open("data/notes.json", "r", encoding="utf-8") as f:
                self.notes = json.load(f)
            print("AutoMod: Notes dosyadan yeniden yüklendi")
            return True
        except Exception as e:
            print(f"AutoMod: Notes yükleme hatası: {e}")
            return False

    def load_regex_patterns(self):
        """Regex kalıplarını yükle"""
        try:
            pattern_file = "config/regex_patterns.json"
            if os.path.exists(pattern_file):
                with open(pattern_file, 'r', encoding='utf-8') as f:
                    self.regex_patterns = json.load(f)
            else:
                self.regex_patterns = []
                with open(pattern_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
        except Exception as e:
            print(f"Regex desenleri yüklenirken hata: {e}")
            self.regex_patterns = []

    def save_regex_patterns(self):
        """Regex kalıplarını kaydet"""
        try:
            with open("config/regex_patterns.json", 'w', encoding='utf-8') as f:
                json.dump(self.regex_patterns, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Regex desenleri kaydedilirken hata: {e}")
            return False
            
    async def add_mod_note(self, user_id: int, mod_type: str, reason: str, duration: str = None):
        """Kullanıcıya moderasyon notu ekler"""
        user_id_str = str(user_id)
        if user_id_str not in self.notes:
            self.notes[user_id_str] = {"UYARILAR": [], "TIMEOUTLAR": [], "BANLAR": []}

        note_data = {
            "sebep": reason,
            "moderator": "AutoMod",
            "moderator_id": self.bot.user.id,
            "tarih": datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        
        if mod_type == "TIMEOUTLAR" and duration:
            note_data["süre"] = duration

        self.notes[user_id_str][mod_type].append(note_data)
        self.save_notes()

    async def add_timeout_note(self, user_id, reason, moderator, moderator_id):
        """Timeout notları için yardımcı metod"""
        user_id_str = str(user_id)
        if user_id_str not in self.notes:
            self.notes[user_id_str] = {"UYARILAR": [], "TIMEOUTLAR": [], "BANLAR": []}

        note_data = {
            "sebep": reason,
            "moderator": moderator,
            "moderator_id": moderator_id,
            "tarih": datetime.now().strftime("%d.%m.%Y %H:%M")
        }

        # Süre bilgisini çıkarma (varsa)
        duration_match = re.search(r"(\d+) saniye", reason)
        if duration_match:
            note_data["süre"] = f"{duration_match.group(1)} saniye"

        self.notes[user_id_str]["TIMEOUTLAR"].append(note_data)
        self.save_notes()
        
        # Notes cog'una haber ver
        notes_cog = self.bot.get_cog("Notes")
        if notes_cog:
            await notes_cog.refresh_notes()
    
    async def log_moderation_action(self, guild, user, action, reason, duration=None, log_channel_id=None):
        """Moderasyon işlemlerini log kanalına kaydeder"""
        if not log_channel_id:
            return
            
        channel = guild.get_channel(log_channel_id)
        if not channel:
            return
            
        embed = discord.Embed(
            title="⚠️ Otomatik Moderasyon İşlemi",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="👤 Kullanıcı", value=f"{user.mention} ({user.id})", inline=False)
        embed.add_field(name="🛑 İşlem", value=action, inline=False)
        embed.add_field(name="📝 Sebep", value=reason, inline=False)
        
        if duration:
            embed.add_field(name="⏱️ Süre", value=duration, inline=False)
        
        embed.set_thumbnail(url=user.display_avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"Kullanıcı ID: {user.id} • {datetime.utcnow().strftime('%H:%M:%S')}")
        
        await channel.send(embed=embed)

    def get_violation_count(self, user_id: int) -> int:
        """Kullanıcının toplam ihlal sayısını getirir"""
        user_id_str = str(user_id)
        if user_id_str not in self.violation_counts:
            return 0
            
        # Eski ihlalleri temizle (config'deki gün sayısına göre)
        current_time = datetime.utcnow()
        reset_days = self.config.get("violation_reset_time", 7)  # Varsayılan 7 gün
        
        # Süresi geçmemiş ihlalleri filtrele
        current_violations = [
            v for v in self.violation_counts[user_id_str]["violations"]
            if (current_time - v["timestamp"]).days < reset_days
        ]
        
        # Güncel ihlalleri kaydet
        self.violation_counts[user_id_str]["violations"] = current_violations
        return len(current_violations)
        
    def add_violation(self, user_id: int, reason: str, word: str = None):
        """Kullanıcıya yeni bir ihlal ekler"""
        user_id_str = str(user_id)
        if user_id_str not in self.violation_counts:
            self.violation_counts[user_id_str] = {
                "violations": [],
                "last_punished_level": 0
            }
            
        violation = {
            "timestamp": datetime.utcnow(),
            "reason": reason,
            "word": word
        }
        
        self.violation_counts[user_id_str]["violations"].append(violation)
    
    async def handle_word_violation(self, message, word):
        """Yasaklı kelime ihlalini işler ve uygun cezayı uygular"""
        user_id = message.author.id
        reason = f"Yasaklı kelime kullanımı: *{word}*"
        
        # Mesajı sil
        try:
            await message.delete()
        except discord.NotFound:
            pass  # Mesaj zaten silinmiş
            
        # İhlal ekle
        self.add_violation(user_id, reason, word)
        
        # Toplam ihlal sayısını kontrol et
        violation_count = self.get_violation_count(user_id)
        user_id_str = str(user_id)
        
        # Ceza seviyesini kontrol et
        punishment_level = (violation_count - 1) // 5
        last_punished_level = 0
        
        if user_id_str in self.violation_counts:
            last_punished_level = self.violation_counts[user_id_str].get("last_punished_level", 0)
        
        # Eğer bu ceza seviyesi için ceza uygulandıysa tekrar uygulama
        if punishment_level <= last_punished_level:
            # İhlali kaydet ve DM ile uyarı gönder
            await self.send_warning_message(message.author, word, violation_count, message.guild)
            return
            
        # Ceza seviyesine göre işlem yap
        if punishment_level == 0:  # 1-5 ihlal: Uyarı
            await self.send_warning_message(message.author, word, violation_count, message.guild)
            
        elif punishment_level == 1:  # 6-10 ihlal: Notes.json'a kayıt
            await self.add_mod_note(user_id, "UYARILAR", reason)
            await self.log_moderation_action(message.guild, message.author, "Resmi Uyarı", reason, None, WARN_LOG_KANAL_ID)
            await self.send_warning_message(
                message.author, 
                word, 
                violation_count,
                message.guild,
                "Bu ihlal kayıtlarınıza eklendi."
            )
            
        elif punishment_level == 2:  # 11-15 ihlal: 1 saatlik timeout
            duration = timedelta(hours=1)
            await message.author.timeout(duration, reason=reason)
            await self.add_mod_note(user_id, "TIMEOUTLAR", reason, "1 saat")
            await self.log_moderation_action(message.guild, message.author, "1 Saatlik Timeout", reason, "1 saat", TIMEOUT_LOG_KANAL_ID)
            await self.send_timeout_message(message.author, word, "1 saat", message.guild)
            
        elif punishment_level == 3:  # 16-20 ihlal: 1 günlük timeout
            duration = timedelta(days=1)
            await message.author.timeout(duration, reason=reason)
            await self.add_mod_note(user_id, "TIMEOUTLAR", reason, "1 gün")
            await self.log_moderation_action(message.guild, message.author, "1 Günlük Timeout", reason, "1 gün", TIMEOUT_LOG_KANAL_ID)
            await self.send_timeout_message(message.author, word, "1 gün", message.guild)
            
        elif punishment_level == 4:  # 21-25 ihlal: 1 haftalık timeout
            duration = timedelta(weeks=1)
            await message.author.timeout(duration, reason=reason)
            await self.add_mod_note(user_id, "TIMEOUTLAR", reason, "1 hafta")
            await self.log_moderation_action(message.guild, message.author, "1 Haftalık Timeout", reason, "1 hafta", TIMEOUT_LOG_KANAL_ID)
            await self.send_timeout_message(message.author, word, "1 hafta", message.guild)
            
        elif punishment_level == 5:  # 26-30 ihlal: 28 günlük timeout (Discord'un maksimum süresi)
            duration = timedelta(days=28)  # Discord'un izin verdiği maksimum süre
            await message.author.timeout(duration, reason=reason)
            await self.add_mod_note(user_id, "TIMEOUTLAR", reason, "28 gün")
            await self.log_moderation_action(message.guild, message.author, "28 Günlük Timeout", reason, "28 gün", TIMEOUT_LOG_KANAL_ID)
            await self.send_timeout_message(message.author, word, "28 gün", message.guild)
            
        elif punishment_level >= 6:  # 31+ ihlal: Yasaklı rolü
            yasakli_rol = message.guild.get_role(YASAKLI)
            if yasakli_rol:
                await message.author.add_roles(yasakli_rol, reason=reason)
                await self.add_mod_note(user_id, "BANLAR", reason)
                await self.log_moderation_action(message.guild, message.author, "Yasaklı Rolü Verildi", reason, None, BAN_LOG_KANAL_ID)
                await self.send_ban_message(message.author, word, message.guild)
        
        # Son uygulanan ceza seviyesini güncelle
        if user_id_str in self.violation_counts:
            self.violation_counts[user_id_str]["last_punished_level"] = punishment_level
    
    async def send_warning_message(self, user, word, violation_count, guild, additional_info=None):
        """Kullanıcıya uyarı mesajı gönderir"""
        embed = discord.Embed(
            title="⚠️ Yasaklı Kelime Uyarısı",
            description=f"**{guild.name}** sunucusunda yasaklı bir kelime kullandınız.",
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📝 Sebep", value=f"Yasaklı kelime kullanımı: *{word}*", inline=False)
        embed.add_field(
            name="⚠️ İhlal Durumu", 
            value=(
                f"Bu sizin **{violation_count}.** ihlaliniz.\n"
                f"5 ihlal: Uyarı\n"
                f"10 ihlal: Kayıt\n"
                f"15 ihlal: 1 saat timeout\n"
                f"20 ihlal: 1 gün timeout\n"
                f"25 ihlal: 1 hafta timeout\n"
                f"30 ihlal: 28 gün timeout\n"
                f"35 ihlal: Yasaklı rolü\n"
            ),
            inline=False
        )
        
        if additional_info:
            embed.add_field(name="📌 Ek Bilgi", value=additional_info, inline=False)
            
        embed.set_footer(text=f"Lütfen sunucu kurallarına uyunuz • {datetime.utcnow().strftime('%H:%M:%S')}")
        
        try:
            await user.send(embed=embed)
        except:
            pass  # DM kapalıysa geç
    
    async def send_timeout_message(self, user, word, duration, guild):
        """Kullanıcıya timeout mesajı gönderir"""
        embed = discord.Embed(
            title="⏳ Zaman Aşımı Aldınız",
            description=f"**{guild.name}** sunucusunda yasaklı kelime kullanımı nedeniyle zaman aşımı (timeout) aldınız.",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📝 Sebep", value=f"Yasaklı kelime kullanımı: *{word}*", inline=False)
        embed.add_field(name="⏱️ Süre", value=f"**{duration}** süreyle susturuldunuz.", inline=False)
        embed.set_footer(text="Otomatik moderasyon sistemi tarafından uygulanmıştır")
        
        try:
            await user.send(embed=embed)
        except:
            pass
    
    async def send_ban_message(self, user, word, guild):
        """Kullanıcıya yasaklı rolü verildiğine dair mesaj gönderir"""
        embed = discord.Embed(
            title="🚫 Yasaklandınız",
            description=f"**{guild.name}** sunucusunda yasaklı kelime kullanımını sürdürdüğünüz için yasaklı rolü aldınız.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📝 Sebep", value=f"Sürekli yasaklı kelime kullanımı: *{word}*", inline=False)
        embed.add_field(
            name="⚠️ Bilgi", 
            value="Yasaklı rolü ile sunucuda sınırlı erişiminiz olacaktır. Yetkililere başvurarak durumunuzu görüşebilirsiniz.", 
            inline=False
        )
        embed.set_footer(text="Otomatik moderasyon sistemi tarafından uygulanmıştır")
        
        try:
            await user.send(embed=embed)
        except:
            pass
    
    async def check_spam(self, message):
        """Kullanıcı spam yapıyor mu kontrol eder"""
        user_id = message.author.id
        now = datetime.utcnow()
        
        if user_id not in self.spam_check:
            self.spam_check[user_id] = {"messages": [now], "last_checked": now}
            return False
            
        # Eski mesajları temizle
        time_window = timedelta(seconds=self.config["time_window"])
        self.spam_check[user_id]["messages"] = [
            msg_time for msg_time in self.spam_check[user_id]["messages"]
            if now - msg_time < time_window
        ]
        
        # Yeni mesajı ekle
        self.spam_check[user_id]["messages"].append(now)
        
        # Spam kontrolü
        if len(self.spam_check[user_id]["messages"]) >= self.config["max_messages"]:
            return True
            
        return False
    
    def is_exempt(self, message):
        """Bu mesaj veya kullanıcı otomatik moderasyondan muaf mı?"""
        # Bot mesajları hariç
        if message.author.bot:
            return True
            
        # Muaf roller
        if any(role.id in self.config["exempted_roles"] for role in message.author.roles):
            return True
            
        # Muaf kanallar
        if message.channel.id in self.config["exempted_channels"]:
            return True
            
        # Sunucu sahibi muaf
        if message.guild.owner_id == message.author.id:
            return True
            
        return False
        
    @commands.Cog.listener()
    async def on_message(self, message):
        """Her mesaj gönderildiğinde çalışır"""
        if not message.guild or not self.config["enabled"] or self.is_exempt(message):
            return
            
        content = message.content.lower()
        
        # 1. Spam kontrolü
        if await self.check_spam(message):
            await message.delete()
            self.add_violation(message.author.id, "Spam yapılmaya çalışıldı")
            violation_count = self.get_violation_count(message.author.id)
            await self.send_warning_message(message.author, "spam", violation_count, message.guild)
            return
            
        # 2. Karaliste kelime kontrolü
        for word in self.config["blacklisted_words"]:
            if re.search(rf"\b{re.escape(word.lower())}\b", content):
                await self.handle_word_violation(message, word)
                return
                
        # 3. Link kontrolü
        for domain in self.config["blacklisted_domains"]:
            if domain.lower() in content:
                await self.handle_word_violation(message, domain)
                return

        # 4. Regex kalıp kontrolü
        for pattern in self.regex_patterns:
            try:
                if re.search(pattern["pattern"], content, re.IGNORECASE):
                    await self.handle_word_violation(message, pattern["name"])
                    return
            except re.error:
                # Hatalı regex desenini atla
                continue
                
        # 5. Etiket spam kontrolü
        if len(message.mentions) > self.config["max_mentions"]:
            await message.delete()
            self.add_violation(message.author.id, f"Çok fazla kullanıcı etiketleme ({len(message.mentions)} kişi)")
            violation_count = self.get_violation_count(message.author.id)
            await self.send_warning_message(message.author, "etiket spamı", violation_count, message.guild)
            return
    
    @commands.group(name="automod", aliases=["otomatikmod"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def automod(self, ctx):
        """Otomatik moderasyon ayarları"""
        embed = discord.Embed(
            title="🛡️ Otomatik Moderasyon Ayarları",
            description="Otomatik moderasyon sistemi ayarları için alt komutları kullanın:",
            color=discord.Color.blue()
        )
        embed.add_field(name="Durum", value=f"`{'✅ Aktif' if self.config['enabled'] else '❌ Devre Dışı'}`", inline=False)
        embed.add_field(name="Komutlar", value=(
            "`!automod toggle` - Otomatik moderasyonu açar/kapatır\n"
            "`!automod blacklist add/remove <kelime>` - Yasaklı kelime ekler/kaldırır\n"
            "`!automod domain add/remove <alan_adı>` - Yasaklı alan adı ekler/kaldırır\n"
            "`!automod settings` - Tüm ayarları görüntüler\n"
            "`!automod exempt role/channel add/remove <id>` - Muaf rol/kanal ekler/kaldırır\n"
            "`!automod setlog <kanal>` - Log kanalı ayarlar\n"
            "`!automod setresettime <gün>` - İhlal sıfırlama süresini ayarlar\n"
            "`!automod regex add/remove/test` - Regex kalıpları ekler/kaldırır/test eder"
        ), inline=False)
        
        await ctx.send(embed=embed)
    
    @automod.command(name="toggle")
    @commands.has_permissions(administrator=True)
    async def automod_toggle(self, ctx):
        """Otomatik moderasyonu açar/kapatır"""
        self.config["enabled"] = not self.config["enabled"]
        self.save_config()
        
        status = "✅ Aktif" if self.config["enabled"] else "❌ Devre Dışı"
        await ctx.send(f"Otomatik moderasyon: {status}")
    
    @automod.group(name="blacklist", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def automod_blacklist(self, ctx):
        """Yasaklı kelime listesini gösterir"""
        words = self.config["blacklisted_words"]
        
        if not words:
            await ctx.send("❌ Yasaklı kelime listesi boş.")
            return
            
        # Sayfalar halinde gönder
        pages = []
        items_per_page = 15
        
        for i in range(0, len(words), items_per_page):
            page_words = words[i:i + items_per_page]
            embed = discord.Embed(
                title="⛔ Yasaklı Kelimeler",
                description="\n".join([f"• `{word}`" for word in page_words]),
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Sayfa {i//items_per_page + 1}/{(len(words)-1)//items_per_page + 1} • Toplam {len(words)} kelime")
            pages.append(embed)
        
        # İlk sayfayı gönder
        current_page = 0
        message = await ctx.send(embed=pages[current_page])
        
        # 10+ kelime varsa navigasyon butonları ekle
        if len(pages) > 1:
            await message.add_reaction("◀️")
            await message.add_reaction("▶️")
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"] and reaction.message.id == message.id
                
            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                    
                    if str(reaction.emoji) == "▶️" and current_page < len(pages) - 1:
                        current_page += 1
                        await message.edit(embed=pages[current_page])
                        await message.remove_reaction(reaction, user)
                        
                    elif str(reaction.emoji) == "◀️" and current_page > 0:
                        current_page -= 1
                        await message.edit(embed=pages[current_page])
                        await message.remove_reaction(reaction, user)
                        
                    else:
                        await message.remove_reaction(reaction, user)
                        
                except asyncio.TimeoutError:
                    break
    
    @automod_blacklist.command(name="add")
    @commands.has_permissions(administrator=True)
    async def blacklist_add(self, ctx, *, word):
        """Yasaklı kelime ekler"""
        if word.lower() not in map(str.lower, self.config["blacklisted_words"]):
            self.config["blacklisted_words"].append(word.lower())
            self.save_config()
            await ctx.send(f"✅ `{word}` yasaklı kelime listesine eklendi.")
        else:
            await ctx.send("❌ Bu kelime zaten yasaklı listede.")
    
    @automod_blacklist.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def blacklist_remove(self, ctx, *, word):
        """Yasaklı kelime kaldırır"""
        word_lower = word.lower()
        for i, blacklisted in enumerate(self.config["blacklisted_words"]):
            if blacklisted.lower() == word_lower:
                self.config["blacklisted_words"].pop(i)
                self.save_config()
                await ctx.send(f"✅ `{word}` yasaklı kelime listesinden kaldırıldı.")
                return
        
        await ctx.send("❌ Bu kelime yasaklı listede bulunamadı.")
    
    @automod.command(name="setlog")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        """Log kanalını ayarlar"""
        self.config["log_channel"] = channel.id
        self.save_config()
        await ctx.send(f"✅ Log kanalı {channel.mention} olarak ayarlandı.")
    
    @automod.command(name="setresettime")
    @commands.has_permissions(administrator=True)
    async def set_reset_time(self, ctx, days: int):
        """İhlal sıfırlama süresini gün cinsinden ayarlar"""
        if days < 1:
            return await ctx.send("❌ Sıfırlama süresi en az 1 gün olmalıdır.")
            
        self.config["violation_reset_time"] = days
        self.save_config()
        await ctx.send(f"✅ İhlaller artık {days} gün sonra sıfırlanacak.")
    
    @automod.command(name="settings")
    @commands.has_permissions(administrator=True)
    async def show_settings(self, ctx):
        """Tüm ayarları gösterir"""
        embed = discord.Embed(
            title="🛡️ Otomatik Moderasyon Ayarları",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Durum", value=f"`{'Aktif' if self.config['enabled'] else 'Devre Dışı'}`", inline=True)
        embed.add_field(name="Maksimum Etiket", value=f"`{self.config['max_mentions']}`", inline=True)
        embed.add_field(name="Spam Sınırı", value=f"`{self.config['max_messages']} mesaj / {self.config['time_window']} saniye`", inline=True)
        
        # Ceza sistemi bilgileri
        embed.add_field(
            name="⚠️ Ceza Sistemi",
            value=(
                f"• İhlal sıfırlama: `{self.config.get('violation_reset_time', 7)} gün`\n"
                f"• 5 ihlal: Uyarı\n"
                f"• 10 ihlal: Kayıt\n"
                f"• 15 ihlal: 1 saat timeout\n"
                f"• 20 ihlal: 1 gün timeout\n"
                f"• 25 ihlal: 1 hafta timeout\n"
                f"• 30 ihlal: 28 gün timeout\n"
                f"• 35 ihlal: Yasaklı rolü"
            ),
            inline=False
        )
        
        # Yasaklı kelime ve domain sayısı
        embed.add_field(
            name="🚫 Yasaklı İçerikler", 
            value=(
                f"Yasaklı Kelime Sayısı: `{len(self.config['blacklisted_words'])}`\n"
                f"Yasaklı Domain Sayısı: `{len(self.config['blacklisted_domains'])}`"
            ), 
            inline=False
        )
        
        log_channel = "Ayarlanmamış"
        if self.config["log_channel"]:
            channel = self.bot.get_channel(self.config["log_channel"])
            log_channel = channel.mention if channel else f"`{self.config['log_channel']}` (Kanal bulunamadı)"
            
        embed.add_field(name="📝 Log Kanalı", value=log_channel, inline=False)
        
        await ctx.send(embed=embed)
    
    @automod.group(name="exempt", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def automod_exempt(self, ctx):
        """Muafiyet ayarlarını gösterir"""
        embed = discord.Embed(
            title="🛡️ Muafiyet Ayarları",
            description="Otomatik moderasyondan muaf olan roller ve kanallar:",
            color=discord.Color.blue()
        )
        
        # Muaf roller
        exempt_roles = []
        for role_id in self.config["exempted_roles"]:
            role = ctx.guild.get_role(role_id)
            if role:
                exempt_roles.append(f"• {role.mention} (`{role_id}`)")
        
        embed.add_field(
            name=f"🎭 Muaf Roller ({len(self.config['exempted_roles'])})",
            value="\n".join(exempt_roles) if exempt_roles else "Muaf rol yok",
            inline=False
        )
        
        # Muaf kanallar
        exempt_channels = []
        for channel_id in self.config["exempted_channels"]:
            channel = ctx.guild.get_channel(channel_id)
            if channel:
                exempt_channels.append(f"• {channel.mention} (`{channel_id}`)")
        
        embed.add_field(
            name=f"📢 Muaf Kanallar ({len(self.config['exempted_channels'])})",
            value="\n".join(exempt_channels) if exempt_channels else "Muaf kanal yok",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Komutlar",
            value=(
                "`!automod exempt role add <role_id/mention>` - Muaf rol ekler\n"
                "`!automod exempt role remove <role_id/mention>` - Muaf rol kaldırır\n"
                "`!automod exempt channel add <channel_id/mention>` - Muaf kanal ekler\n"
                "`!automod exempt channel remove <channel_id/mention>` - Muaf kanal kaldırır"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @automod_exempt.group(name="role", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def exempt_role(self, ctx):
        """Muaf rol komutlarını gösterir"""
        await ctx.send("❌ Lütfen bir alt komut belirtin: `add` veya `remove`")
    
    @exempt_role.command(name="add")
    @commands.has_permissions(administrator=True)
    async def exempt_role_add(self, ctx, role: discord.Role):
        """Muaf rol ekler"""
        if role.id in self.config["exempted_roles"]:
            return await ctx.send(f"❌ {role.mention} zaten muaf listesinde.")
            
        self.config["exempted_roles"].append(role.id)
        self.save_config()
        await ctx.send(f"✅ {role.mention} artık otomatik moderasyondan muaf.")
    
    @exempt_role.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def exempt_role_remove(self, ctx, role: discord.Role):
        """Muaf rolü kaldırır"""
        if role.id not in self.config["exempted_roles"]:
            return await ctx.send(f"❌ {role.mention} muaf listesinde değil.")
            
        self.config["exempted_roles"].remove(role.id)
        self.save_config()
        await ctx.send(f"✅ {role.mention} artık otomatik moderasyona tabi.")
    
    @automod_exempt.group(name="channel", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def exempt_channel(self, ctx):
        """Muaf kanal komutlarını gösterir"""
        await ctx.send("❌ Lütfen bir alt komut belirtin: `add` veya `remove`")
    
    @exempt_channel.command(name="add")
    @commands.has_permissions(administrator=True)
    async def exempt_channel_add(self, ctx, channel: discord.TextChannel):
        """Muaf kanal ekler"""
        if channel.id in self.config["exempted_channels"]:
            return await ctx.send(f"❌ {channel.mention} zaten muaf listesinde.")
            
        self.config["exempted_channels"].append(channel.id)
        self.save_config()
        await ctx.send(f"✅ {channel.mention} artık otomatik moderasyondan muaf.")
    
    @exempt_channel.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def exempt_channel_remove(self, ctx, channel: discord.TextChannel):
        """Muaf kanalı kaldırır"""
        if channel.id not in self.config["exempted_channels"]:
            return await ctx.send(f"❌ {channel.mention} muaf listesinde değil.")
            
        self.config["exempted_channels"].remove(channel.id)
        self.save_config()
        await ctx.send(f"✅ {channel.mention} artık otomatik moderasyona tabi.")
    
    @automod.command(name="ihlallar")
    @commands.has_permissions(administrator=True)
    async def view_violations(self, ctx, user: discord.Member):
        """Belirli bir kullanıcının ihlallerini gösterir"""
        user_id_str = str(user.id)
        
        if user_id_str not in self.violation_counts:
            return await ctx.send(f"✅ {user.mention} kullanıcısının hiç ihlali bulunmuyor.")
        
        current_time = datetime.utcnow()
        reset_days = self.config.get("violation_reset_time", 7)
        
        # Son ihlalleri getir
        violations = self.violation_counts[user_id_str]["violations"]
        valid_violations = [
            v for v in violations 
            if (current_time - v["timestamp"]).days < reset_days
        ]
        
        if not valid_violations:
            return await ctx.send(f"✅ {user.mention} kullanıcısının son {reset_days} gün içinde ihlali bulunmuyor.")
        
        embed = discord.Embed(
            title=f"⚠️ {user.name} Kullanıcısının İhlalleri",
            description=f"Son {reset_days} gün içinde toplam **{len(valid_violations)}** ihlal",
            color=discord.Color.orange()
        )
        
        # İhlalleri grupla
        violation_counts = {}
        for v in valid_violations:
            reason = v["reason"]
            if reason not in violation_counts:
                violation_counts[reason] = 0
            violation_counts[reason] += 1
        
        # İhlalleri listele
        for reason, count in violation_counts.items():
            embed.add_field(name=f"🔹 {reason}", value=f"**{count}** kez", inline=False)
        
        # Son ihlal zamanı
        if valid_violations:
            last_violation = max(valid_violations, key=lambda v: v["timestamp"])
            time_diff = current_time - last_violation["timestamp"]
            days = time_diff.days
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            time_str = ""
            if days > 0:
                time_str += f"{days} gün "
            if hours > 0:
                time_str += f"{hours} saat "
            if minutes > 0:
                time_str += f"{minutes} dakika"
            
            if not time_str:
                time_str = "1 dakikadan az"
                
            embed.add_field(
                name="⏱️ Son İhlal",
                value=f"{time_str} önce",
                inline=False
            )
        
        embed.set_thumbnail(url=user.display_avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"Kullanıcı ID: {user.id} • İhlaller {reset_days} gün sonra sıfırlanır")
        
        await ctx.send(embed=embed)

    @automod.command(name="ihlalsifirla")
    @commands.has_permissions(administrator=True)
    async def reset_violations(self, ctx, user: discord.Member = None):
        """Bir kullanıcının veya tüm kullanıcıların ihlallerini sıfırlar"""
        if user:
            user_id_str = str(user.id)
            if user_id_str in self.violation_counts:
                del self.violation_counts[user_id_str]
                await ctx.send(f"✅ {user.mention} kullanıcısının tüm ihlalleri sıfırlandı.")
            else:
                await ctx.send(f"❌ {user.mention} kullanıcısının zaten hiç ihlali yok.")
        else:
            count = len(self.violation_counts)
            self.violation_counts = {}
            await ctx.send(f"✅ Tüm kullanıcıların ({count} kullanıcı) ihlalleri sıfırlandı.")

    @automod.group(name="regex", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def automod_regex(self, ctx):
        """Regex kalıp listesini gösterir"""
        if not self.regex_patterns:
            await ctx.send("❌ Henüz tanımlanmış regex kalıbı yok.")
            return
            
        # Sayfalar halinde gönder
        pages = []
        items_per_page = 5
        
        for i in range(0, len(self.regex_patterns), items_per_page):
            page_patterns = self.regex_patterns[i:i + items_per_page]
            embed = discord.Embed(
                title="⚙️ Regex Kalıpları",
                description="Düzenli ifadelerle tespit edilen içerikler:",
                color=discord.Color.purple()
            )
            
            for idx, pattern in enumerate(page_patterns, 1):
                embed.add_field(
                    name=f"{idx+i}. {pattern['name']}",
                    value=f"```{pattern['pattern']}```",
                    inline=False
                )
            
            embed.set_footer(text=f"Sayfa {i//items_per_page + 1}/{(len(self.regex_patterns)-1)//items_per_page + 1}")
            pages.append(embed)
        
        # İlk sayfayı gönder
        current_page = 0
        message = await ctx.send(embed=pages[current_page])
        
        # Birden fazla sayfa varsa navigasyon ekle
        if len(pages) > 1:
            await message.add_reaction("◀️")
            await message.add_reaction("▶️")
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"] and reaction.message.id == message.id
                
            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                    
                    if str(reaction.emoji) == "▶️" and current_page < len(pages) - 1:
                        current_page += 1
                        await message.edit(embed=pages[current_page])
                        await message.remove_reaction(reaction, user)
                        
                    elif str(reaction.emoji) == "◀️" and current_page > 0:
                        current_page -= 1
                        await message.edit(embed=pages[current_page])
                        await message.remove_reaction(reaction, user)
                        
                    else:
                        await message.remove_reaction(reaction, user)
                        
                except asyncio.TimeoutError:
                    break
                    
                except Exception:
                    break

    @automod_regex.command(name="add")
    @commands.has_permissions(administrator=True)
    async def regex_add(self, ctx, name: str, *, pattern: str):
        """Regex kalıbı ekler"""
        # Regex'i test et
        try:
            re.compile(pattern)
        except re.error:
            return await ctx.send("❌ Geçersiz regex kalıbı. Lütfen geçerli bir regex deseni girin.")
        
        # Aynı isimde kalıp var mı kontrol et
        if any(p["name"] == name for p in self.regex_patterns):
            return await ctx.send(f"❌ `{name}` isimli bir kalıp zaten mevcut.")
        
        self.regex_patterns.append({
            "name": name,
            "pattern": pattern
        })
        self.save_regex_patterns()
        
        await ctx.send(f"✅ `{name}` isimli regex kalıbı eklendi.")

    @automod_regex.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def regex_remove(self, ctx, *, name: str):
        """Regex kalıbı kaldırır"""
        for i, pattern in enumerate(self.regex_patterns):
            if pattern["name"] == name:
                self.regex_patterns.pop(i)
                self.save_regex_patterns()
                return await ctx.send(f"✅ `{name}` isimli regex kalıbı kaldırıldı.")
        
        await ctx.send("❌ Bu isimde bir regex kalıbı bulunamadı.")

    @automod_regex.command(name="test")
    @commands.has_permissions(administrator=True)
    async def regex_test(self, ctx, *, text: str):
        """Metni regex kalıplarına karşı test eder"""
        matches = []
        
        for pattern in self.regex_patterns:
            try:
                if re.search(pattern["pattern"], text, re.IGNORECASE):
                    matches.append(pattern["name"])
            except re.error:
                continue
        
        if matches:
            await ctx.send(f"⚠️ Metin şu kalıplarla eşleşti: `{', '.join(matches)}`")
        else:
            await ctx.send("✅ Metin hiçbir kalıpla eşleşmedi.")

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
import discord
from discord.ext import commands
import datetime
import json
import asyncio
from config.config import *

class Notes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.moderation = None
        self.custom_notes = {}
        # Not yenileme görevini başlat
        self.bot.loop.create_task(self.auto_refresh_task())

    async def auto_refresh_task(self):
        """Her 5 saniyede bir notları otomatik yenile"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            # Notları yenileme işlemini kaldırıyoruz
            # Bunun yerine sadece AutoMod yoksa ve dosya değiştiyse yenileyelim
            if not self.moderation:
                try:
                    # Son yenileme tarihini kontrol et
                    if not hasattr(self, 'last_file_check'):
                        self.last_file_check = 0
                    
                    # Dosyanın son değiştirilme zamanını kontrol et
                    import os
                    if os.path.exists("data/notes.json"):
                        current_mtime = os.path.getmtime("data/notes.json")
                        
                        # Eğer dosya değiştiyse ve bu bizim yaptığımız bir değişiklik değilse
                        if current_mtime > self.last_file_check and not hasattr(self, 'is_saving'):
                            self.last_file_check = current_mtime
                            await self.refresh_notes()
                except Exception as e:
                    print(f"Notes oto-yenileme hatası: {e}")
            
            # 5 saniye bekle
            await asyncio.sleep(5)

    async def cog_load(self):
        """Moderation cog'una erişim sağla"""
        try:
            # Bir süre bekleyerek moderation cog'unun yüklenmesini garantile
            await asyncio.sleep(1)
            
            # AutoMod sınıfını bulmaya çalış
            self.moderation = self.bot.get_cog("AutoMod")
            
            # Eğer moderation varsa events metodu ekle
            if self.moderation and hasattr(self.moderation, "save_notes"):
                # Orijinal save_notes metodunu sakla
                original_save = self.moderation.save_notes
                
                # Yeni metodu tanımla
                def new_save_notes():
                    # Son değişim zamanını güncelle
                    self.is_saving = True
                    result = original_save()
                    self.last_file_check = os.path.getmtime("data/notes.json") if os.path.exists("data/notes.json") else 0
                    self.is_saving = False
                    return result
                
                # Metodu değiştir
                self.moderation.save_notes = new_save_notes
            
            # AutoMod yoksa konsola bilgi yazdır
            if not self.moderation:
                print("❌ Notes cog: AutoMod bulunamadı, direkt dosyadan okuma yapılacak")
                
                # Notları doğrudan dosyadan yükle
                try:
                    with open("data/notes.json", "r", encoding="utf-8") as f:
                        self.custom_notes = json.load(f)
                    self.last_file_check = os.path.getmtime("data/notes.json")
                except Exception as e:
                    self.custom_notes = {}
                    print(f"Notları yüklerken hata: {e}")
            
        except Exception as e:
            print(f"Notes cog load hatası: {e}")

    def cog_unload(self):
        pass

    async def refresh_notes(self):
        """Notes verilerini dosyadan tekrar yükler"""
        try:
            with open("data/notes.json", "r", encoding="utf-8") as f:
                self.custom_notes = json.load(f)
                print("📝 Notes verileri yenilendi!")
            return True
        except Exception as e:
            print(f"❌ Notes yenileme hatası: {e}")
            return False

    async def refresh_from_file(self):
        """JSON dosyasından tüm notları yeniden yükle"""
        try:
            with open("data/notes.json", "r", encoding="utf-8") as f:
                notes_data = json.load(f)
                
            # Verileri güncelle
            if self.moderation:
                self.moderation.notes = notes_data
            else:
                self.custom_notes = notes_data
                
            print("Notes cog: Notlar dosyadan yeniden yüklendi")
            return True
        except Exception as e:
            print(f"Notes yenileme hatası: {e}")
            return False

    async def add_note(self, user_id: int, note_type: str, reason: str, moderator: str, moderator_id: int):
        """Not ekler ve diğer cog'a haber verir"""
        user_id_str = str(user_id)
        
        # Eğer AutoMod yüklüyse, ona yönlendir
        if self.moderation:
            # AutoMod'un kendi not ekleme fonksiyonunu çağır
            if note_type == "UYARILAR":
                await self.moderation.add_warning(user_id, reason, moderator, moderator_id)
            elif note_type == "TIMEOUTLAR":
                await self.moderation.add_timeout_note(user_id, reason, moderator, moderator_id)
            elif note_type == "BANLAR":
                await self.moderation.add_ban_note(user_id, reason, moderator, moderator_id)
        else:
            # Kendi notlarımıza ekle
            if user_id_str not in self.custom_notes:
                self.custom_notes[user_id_str] = {
                    "UYARILAR": [],
                    "TIMEOUTLAR": [],
                    "BANLAR": []
                }
            
            # Notun içeriğini hazırla
            note_data = {
                "sebep": reason,
                "moderator": moderator,
                "moderator_id": moderator_id,
                "tarih": datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
            }
            
            self.custom_notes[user_id_str][note_type].append(note_data)
            
            # JSON dosyasına kaydet
            try:
                # Kayıt işlemi yapıldığını belirt (bayrak)
                self.is_saving = True
                with open("data/notes.json", "w", encoding="utf-8") as f:
                    json.dump(self.custom_notes, f, ensure_ascii=False, indent=4)
                self.last_file_check = os.path.getmtime("data/notes.json")
            finally:
                # Bayrağı kaldır
                self.is_saving = False

    @commands.command(name="notlar", aliases=["geçmiş", "gecmis", "logs"])
    @commands.has_permissions(kick_members=True)
    async def view_notes(self, ctx, user_id: int):
        """Kullanıcının tüm moderasyon geçmişini gösterir"""
        if not self.moderation and not self.custom_notes:
            return await ctx.send("❌ Moderasyon sistemi yüklenemedi!")

        user_id_str = str(user_id)
        
        # Her zaman önce dosyadan en güncel verileri yükleyelim
        await self.refresh_from_file()
        
        # Güncel verileri al
        notes = self.moderation.notes.get(user_id_str) if self.moderation else self.custom_notes.get(user_id_str)
        
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
        if "UYARILAR" in notes and notes["UYARILAR"]:
            uyari_text = ""
            for idx, note in enumerate(notes["UYARILAR"], 1):
                moderator_name = note.get('moderator', 'Bilinmiyor')
                if moderator_name == "AutoMod":
                    moderator_name = "🤖 AutoMod"
                    
                uyari_text += f"**#{idx}** | {note.get('tarih', 'Tarih yok')}\n"
                uyari_text += f"➜ Sebep: {note.get('sebep', 'Sebep belirtilmedi')}\n"
                uyari_text += f"➜ Moderatör: {moderator_name}\n\n"
            
            embed.add_field(
                name=f"⚠️ Uyarılar [{len(notes['UYARILAR'])}]",
                value=uyari_text or "Bulunmuyor",
                inline=False
            )

        # Timeoutları listele
        if "TIMEOUTLAR" in notes and notes["TIMEOUTLAR"]:
            timeout_text = ""
            for idx, note in enumerate(notes["TIMEOUTLAR"], 1):
                moderator_name = note.get('moderator', 'Bilinmiyor')
                if moderator_name == "AutoMod":
                    moderator_name = "🤖 AutoMod"
                    
                timeout_text += f"**#{idx}** | {note.get('tarih', 'Tarih yok')}\n"
                timeout_text += f"➜ Sebep: {note.get('sebep', 'Sebep belirtilmedi')}\n"
                timeout_text += f"➜ Süre: {note.get('süre', 'Belirtilmedi')}\n"
                timeout_text += f"➜ Moderatör: {moderator_name}\n\n"
            
            embed.add_field(
                name=f"⏳ Timeout Geçmişi [{len(notes['TIMEOUTLAR'])}]",
                value=timeout_text or "Bulunmuyor",
                inline=False
            )

        # Banları listele
        if "BANLAR" in notes and notes["BANLAR"]:
            ban_text = ""
            for idx, note in enumerate(notes["BANLAR"], 1):
                moderator_name = note.get('moderator', 'Bilinmiyor')
                if moderator_name == "AutoMod":
                    moderator_name = "🤖 AutoMod"
                    
                ban_text += f"**#{idx}** | {note.get('tarih', 'Tarih yok')}\n"
                ban_text += f"➜ Sebep: {note.get('sebep', 'Sebep belirtilmedi')}\n"
                ban_text += f"➜ Moderatör: {moderator_name}\n\n"
            
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
        """Belirtilen moderasyon kaydını siler"""
        if not self.moderation and not self.custom_notes:
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

        user_id_str = str(user_id)

        try:
            # İlk olarak notes.json dosyasını güncelle (dosya güncel verileri yansıtacak)
            try:
                with open("data/notes.json", "r", encoding="utf-8") as f:
                    all_notes = json.load(f)
            except Exception as e:
                print(f"Notes dosyası okuma hatası: {e}")
                all_notes = {}

            # Dosyadaki notu sil
            if user_id_str in all_notes and type in all_notes[user_id_str] and len(all_notes[user_id_str][type]) >= index:
                # Silme işlemlerini gerçekleştir
                deleted_note = all_notes[user_id_str][type].pop(index - 1)
                
                # Kullanıcının tüm kayıtları boşsa, kullanıcıyı tamamen kaldır
                if not all_notes[user_id_str][type] and not all_notes[user_id_str]["UYARILAR"] and not all_notes[user_id_str]["TIMEOUTLAR"] and not all_notes[user_id_str]["BANLAR"]:
                    del all_notes[user_id_str]
                    
                # Dosyaya geri yaz
                try:
                    # Kayıt işlemi yapıldığını belirt
                    self.is_saving = True
                    with open("data/notes.json", "w", encoding="utf-8") as f:
                        json.dump(all_notes, f, ensure_ascii=False, indent=4)
                    self.last_file_check = os.path.getmtime("data/notes.json")
                    
                    # Veriyi güncelle
                    if self.moderation:
                        self.moderation.notes = all_notes
                    else:
                        self.custom_notes = all_notes
                finally:
                    # Bayrağı kaldır
                    self.is_saving = False
                
                # Başarı mesajı
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
            else:
                return await ctx.send("❌ Belirtilen kayıt bulunamadı!")

        except Exception as e:
            await ctx.send(f"❌ Bir hata oluştu: {e}")

    @commands.command(name="nottemizle")
    @commands.has_permissions(administrator=True)
    async def clear_notes(self, ctx, user_id: int):
        """Kullanıcının tüm moderasyon geçmişini temizler"""
        if not self.moderation and not self.custom_notes:
            return await ctx.send("❌ Moderasyon sistemi yüklenemedi!")

        if str(user_id) not in (self.moderation.notes if self.moderation else self.custom_notes):
            return await ctx.send("❌ Bu kullanıcı için kayıt bulunmuyor!")

        try:
            user = await self.bot.fetch_user(user_id)
            user_name = user.name
        except:
            user_name = str(user_id)

        if self.moderation:
            del self.moderation.notes[str(user_id)]
            self.moderation.save_notes()
        else:
            del self.custom_notes[str(user_id)]
            try:
                # Kayıt işlemi yapıldığını belirt
                self.is_saving = True
                with open("data/notes.json", "w", encoding="utf-8") as f:
                    json.dump(self.custom_notes, f, ensure_ascii=False, indent=4)
                self.last_file_check = os.path.getmtime("data/notes.json")
            finally:
                # Bayrağı kaldır
                self.is_saving = False

        embed = discord.Embed(
            title="🧹 Moderasyon Geçmişi Temizlendi",
            description=f"**{user_name}** kullanıcısının tüm moderasyon kayıtları silindi.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        """Komut tamamlandığında notları yenile"""
        # Sadece moderasyon komutlarından sonra yenile
        if ctx.command.name in ["uyar", "warn", "timeout", "mute", "sustur", "ban", "kick", "notsil"]:
            await self.refresh_from_file()

async def setup(bot):
    await bot.add_cog(Notes(bot))
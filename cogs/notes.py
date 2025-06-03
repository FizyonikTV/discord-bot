import discord
from discord.ext import commands
import json
import os
from datetime import datetime
from config.config import IZIN_VERILEN_ROLLER
from utils.json_handler import JsonHandler
from utils.permissions import has_mod_role, has_admin

class Notes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notes_path = "data/notes.json"
        self.notes = {}
        self.load_notes()
        print(f"[📝] Notes cog yüklendi.")

    def load_notes(self):
        """Not dosyasını yükler"""
        try:
            # JSON Handler kullanarak güvenli yükleme
            self.notes = JsonHandler.load_json(self.notes_path, default={})
            print(f"[📝] {len(self.notes)} kullanıcı kaydı yüklendi.")
        except Exception as e:
            print(f"[❌] Notlar yüklenirken hata oluştu: {e}")
            self.notes = {}
    
    async def save_notes(self):
        """Not dosyasını kaydeder"""
        try:
            # JSON Handler kullanarak güvenli kaydetme
            success = JsonHandler.save_json(self.notes_path, self.notes)
            if success:
                print(f"[📝] Notlar kaydedildi - {len(self.notes)} kullanıcı")
            return success
        except Exception as e:
            print(f"[❌] Notlar kaydedilirken hata oluştu: {e}")
            return False

    async def add_note(self, user_id, note_type, reason, moderator, moderator_id, **kwargs):
        """Kullanıcıya not ekler"""
        user_id_str = str(user_id)
        
        # Notes doğru yapıda değilse oluştur
        if user_id_str not in self.notes:
            self.notes[user_id_str] = {"UYARILAR": [], "TIMEOUTLAR": [], "BANLAR": []}
        
        if note_type not in self.notes[user_id_str]:
            self.notes[user_id_str][note_type] = []

        # Not ekle
        note_data = {
            "sebep": reason,
            "moderator": moderator,
            "moderator_id": moderator_id,
            "tarih": datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        
        # Ek bilgileri ekle (timeout süresi gibi)
        for key, value in kwargs.items():
            note_data[key] = value
        
        # TIMEOUTLAR için süre bilgisini ekle
        if note_type == "TIMEOUTLAR" and "duration" in kwargs:
            note_data["süre"] = kwargs["duration"]
        
        # Not ekle ve kaydet
        self.notes[user_id_str][note_type].append(note_data)
        success = await self.save_notes()
        
        if not success:
            print(f"[❌] Not {user_id} için kaydedilemedi! (Tip: {note_type})")
        else:
            print(f"[📝] Not eklendi: {user_id} - {note_type}")
        
        return success
    
    async def refresh_notes(self):
        """Notes dosyasını yeniden yükler"""
        self.load_notes()
        return True

    @commands.group(name="not", invoke_without_command=True)
    @has_mod_role()
    async def notes_cmd(self, ctx):
        """Not komutları"""
        await ctx.send("📝 Lütfen bir alt komut belirtin: `ekle`, `listele`, `sil`, `temizle`")

    @notes_cmd.command(name="ekle")
    @has_mod_role()
    async def add_note_cmd(self, ctx, user: discord.Member, note_type: str, *, reason: str):
        """Kullanıcıya not ekler"""
        note_type = note_type.upper()
        valid_types = ["UYARILAR", "TIMEOUTLAR", "BANLAR"]
        
        if note_type not in valid_types:
            return await ctx.send(f"❌ Geçersiz not tipi. Kullanılabilir tipler: {', '.join(valid_types)}")
        
        success = await self.add_note(
            user_id=user.id,
            note_type=note_type,
            reason=reason,
            moderator=str(ctx.author),
            moderator_id=ctx.author.id
        )
        
        if success:
            await ctx.send(f"✅ `{user}` kullanıcısına **{note_type}** tipinde not eklendi.")
        else:
            await ctx.send("❌ Not eklenirken bir hata oluştu.")

    @notes_cmd.command(name="listele", aliases=["liste", "list"])
    @has_mod_role()
    async def list_notes(self, ctx, user: discord.Member, note_type: str = None):
        """Kullanıcının notlarını listeler"""
        # Notes yükle - güncel olmalarını sağla
        self.load_notes()
        
        user_id_str = str(user.id)
        
        if user_id_str not in self.notes or not self.notes[user_id_str]:
            return await ctx.send(f"❌ `{user}` kullanıcısı için kayıtlı not bulunmuyor.")
        
        note_types = ["UYARILAR", "TIMEOUTLAR", "BANLAR"]
        if note_type:
            note_type = note_type.upper()
            if note_type not in note_types:
                return await ctx.send(f"❌ Geçersiz not tipi. Kullanılabilir tipler: {', '.join(note_types)}")
            note_types = [note_type]
        
        embed = discord.Embed(
            title=f"📝 {user} Kullanıcısının Notları",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        
        for note_type in note_types:
            if note_type in self.notes[user_id_str] and self.notes[user_id_str][note_type]:
                notes = self.notes[user_id_str][note_type]
                notes_txt = ""
                
                for i, note in enumerate(notes, start=1):
                    notes_txt += f"**{i}.** {note.get('tarih', 'Tarih yok')} - {note.get('sebep', 'Sebep yok')}\n"
                    notes_txt += f"└ Moderatör: {note.get('moderator', 'Bilinmiyor')}\n"
                    
                    if "süre" in note and note_type == "TIMEOUTLAR":
                        notes_txt += f"└ Süre: {note['süre']}\n"
                    
                    notes_txt += "\n"
                
                if notes_txt:
                    embed.add_field(name=f"{note_type} ({len(notes)})", value=notes_txt, inline=False)
            
        await ctx.send(embed=embed)

    @notes_cmd.command(name="sil", aliases=["delete", "remove"])
    @has_mod_role()
    async def delete_note(self, ctx, user: discord.Member, note_type: str, note_index: int):
        """Belirtilen notu siler"""
        # Notes yükle - güncel olmalarını sağla
        self.load_notes()
        
        user_id_str = str(user.id)
        note_type = note_type.upper()
        
        if user_id_str not in self.notes:
            return await ctx.send(f"❌ `{user}` kullanıcısı için kayıtlı not bulunmuyor.")
        
        if note_type not in self.notes[user_id_str]:
            return await ctx.send(f"❌ `{user}` kullanıcısı için `{note_type}` tipinde not bulunmuyor.")
        
        notes = self.notes[user_id_str][note_type]
        
        if not (1 <= note_index <= len(notes)):
            return await ctx.send(f"❌ Geçersiz not indeksi. 1-{len(notes)} arasında bir değer girin.")
        
        # Notu sil (1-tabanlı indeks olduğu için -1 yapıyoruz)
        removed_note = notes.pop(note_index - 1)
        await self.save_notes()
        
        # Silinen not hakkında bilgi ver
        embed = discord.Embed(
            title="🗑️ Not Silindi",
            description=f"`{user}` kullanıcısının `{note_type}` kategorisindeki **{note_index}.** notu silindi.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Silinen Not Bilgileri",
            value=(
                f"**Sebep:** {removed_note.get('sebep', 'Belirtilmemiş')}\n"
                f"**Eklenme Tarihi:** {removed_note.get('tarih', 'Belirtilmemiş')}\n"
                f"**Ekleyen:** {removed_note.get('moderator', 'Belirtilmemiş')}"
            ),
            inline=False
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @notes_cmd.command(name="temizle", aliases=["clear"])
    @has_admin()
    async def clear_notes(self, ctx, user: discord.Member, note_type: str = None):
        """Kullanıcının belirtilen tip notlarını veya tüm notlarını temizler"""
        # Notes yükle - güncel olmalarını sağla
        self.load_notes()
        
        user_id_str = str(user.id)
        
        if user_id_str not in self.notes or not self.notes[user_id_str]:
            return await ctx.send(f"❌ `{user}` kullanıcısı için kayıtlı not bulunmuyor.")
        
        if note_type:
            # Belirli bir not türünü temizle
            note_type = note_type.upper()
            valid_types = ["UYARILAR", "TIMEOUTLAR", "BANLAR"]
            
            if note_type not in valid_types:
                return await ctx.send(f"❌ Geçersiz not tipi. Kullanılabilir tipler: {', '.join(valid_types)}")
            
            if note_type not in self.notes[user_id_str] or not self.notes[user_id_str][note_type]:
                return await ctx.send(f"❌ `{user}` kullanıcısı için `{note_type}` tipinde not bulunmuyor.")
            
            # Not sayısını al ve notları temizle
            note_count = len(self.notes[user_id_str][note_type])
            self.notes[user_id_str][note_type] = []
            await self.save_notes()
            
            await ctx.send(f"✅ `{user}` kullanıcısının **{note_count}** adet `{note_type}` notu temizlendi.")
        else:
            # Tüm notları temizle
            self.notes.pop(user_id_str, None)
            await self.save_notes()
            
            await ctx.send(f"✅ `{user}` kullanıcısının tüm notları temizlendi.")

    # Dışa açık komutlar (not alt komutları dışında)
    @commands.command(name="notlar", aliases=["notes", "geçmiş", "gecmis"])
    @has_mod_role()
    async def view_notes(self, ctx, user: discord.Member = None):
        """Kullanıcının moderasyon geçmişini gösterir"""
        if not user:
            return await ctx.send("❌ Lütfen bir kullanıcı belirtin! Örnek: `!notlar @kullanıcı`")
        await self.list_notes(ctx, user)
    
    @commands.command(name="notsil", aliases=["delnote"])
    @has_mod_role()
    async def remove_note(self, ctx, user: discord.Member, note_type: str, note_index: int):
        """Kullanıcının belirtilen notunu siler"""
        await self.delete_note(ctx, user, note_type, note_index)
    
    @commands.command(name="nottemizle", aliases=["clearnotes"])
    @has_admin()
    async def clear_user_notes(self, ctx, user: discord.Member, note_type: str = None):
        """Kullanıcının tüm notlarını veya belirli kategori notlarını temizler"""
        await self.clear_notes(ctx, user, note_type)

    # ID tabanlı not komutları - string veya ID ile
    @commands.command(name="nid")
    @has_mod_role()
    async def notes_by_id(self, ctx, user_id):
        """ID ile kullanıcının moderasyon geçmişini gösterir"""
        try:
            # String ID'yi int'e çevir
            user_id = str(user_id).strip("<@!>")
            user = None

            try:
                # Kullanıcıyı bul
                user = await self.bot.fetch_user(int(user_id))
            except:
                # Kullanıcı bulunamazsa bile devam et
                pass

            # Notes yükle
            self.load_notes()
            
            # Not var mı kontrol et
            if user_id not in self.notes or not self.notes[user_id]:
                return await ctx.send(f"❌ ID: `{user_id}` için kayıtlı not bulunmuyor.")
            
            # Embed oluştur
            embed = discord.Embed(
                title=f"📝 Kullanıcı Notları",
                description=f"ID: {user_id}" + (f" ({user})" if user else ""),
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            if user:
                embed.set_thumbnail(url=user.display_avatar.url)
            
            # Tüm not tiplerini kontrol et
            for note_type in ["UYARILAR", "TIMEOUTLAR", "BANLAR"]:
                if note_type in self.notes[user_id] and self.notes[user_id][note_type]:
                    notes = self.notes[user_id][note_type]
                    notes_txt = ""
                    
                    for i, note in enumerate(notes, start=1):
                        notes_txt += f"**{i}.** {note.get('tarih', 'Tarih yok')} - {note.get('sebep', 'Sebep yok')}\n"
                        notes_txt += f"└ Moderatör: {note.get('moderator', 'Bilinmiyor')}\n"
                        
                        if "süre" in note and note_type == "TIMEOUTLAR":
                            notes_txt += f"└ Süre: {note['süre']}\n"
                        
                        notes_txt += "\n"
                    
                    if notes_txt:
                        embed.add_field(name=f"{note_type} ({len(notes)})", value=notes_txt, inline=False)
            
            await ctx.send(embed=embed)
                
        except Exception as e:
            await ctx.send(f"❌ Hata: {e}")
            import traceback
            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(Notes(bot))
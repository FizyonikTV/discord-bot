from discord.ext.commands import BucketType
import discord
from discord.ext import commands
from discord.ui import View, Select, Button
import asyncio
import time
from utils.helpers import izin_kontrol, command_check
from config.config import TIMEOUT_LOG_KANAL_ID, BAN_LOG_KANAL_ID, WARN_LOG_KANAL_ID
from utils.permissions import has_mod_role, has_admin

def create_home_embed():
    """Ana yardım embed'ini oluşturur - geliştirilmiş tasarım"""
    embed = discord.Embed(
        title="",
        color=0x9932CC  # Daha parlak mor
    )

    # Modern başlık ve açıklama
    embed.description = (
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "🌙 **LUNARIS BOT**  |  📚 Yardım Merkezi\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "*Gelişmiş Discord moderasyon ve eğlence botu*\n"
    )

    embed.add_field(
        name="🛡️ **Moderasyon**",
        value="""
```diff
+ Güçlü moderasyon araçları
+ AutoMod sistemi
+ Detaylı log tutma
```
        """,
        inline=True
    )

    embed.add_field(
        name="🎉 **Eğlence**",
        value="""
```yaml
+ Anime etkileşimleri (2 sayfa!)
+ Çekiliş sistemi
+ Oyun komutları
```
        """,
        inline=True
    )

    embed.add_field(
        name="⭐ **Sistemler**",
        value="""
```fix
+ Seviye sistemi
+ Davet takibi
+ Web dashboard
```
        """,
        inline=True
    )

    embed.add_field(
        name="💡 **Özellikler**",
        value="""
• **Akıllı Sistem:** Komutlar sadece belirlenen kanallarda çalışır
• **Çoklu Sayfa:** Eğlence komutları artık 2 sayfada!
• **Zengin İçerik:** 100+ komut ve özellik
• **7/24 Aktif:** Sürekli güncellenen sistemler
        """,
        inline=False
    )

    embed.set_thumbnail(url="https://i.ibb.co/wvQCt9C/lunaris-pp.png")
    embed.set_footer(text="🌟 LunarisBot v2.0 | Aşağıdaki menüden kategori seçin")
    
    return embed

def create_moderation_embed():
    embed = discord.Embed(
        title="",
        description="",
        color=0xFF6B6B  # Moderasyon için kırmızı ton
    )
    
    # Başlık
    embed.add_field(
        name="",
        value="""
🛡️ **MODERASYON KOMENDERLİĞİ**
─────────────────────────────
*Sunucunuzu güvende tutun*
        """,
        inline=False
    )

    embed.add_field(
        name="⚠️ **Uyarı & Ceza Sistemi**",
        value="""
```diff
+ !uyar @kullanıcı <sebep>
  Kullanıcıyı uyarır ve kayıt tutar

+ !zaman @kullanıcı <süre> [sebep]
  Geçici susturma (1m, 1h, 1d)

+ !zamankaldir @kullanıcı
  Timeout'u kaldırır

+ !yasakla @kullanıcı [sebep]
  Sunucudan kalıcı yasak

+ !yasakkaldir @kullanıcı
  Yasağı kaldırır
```
        """,
        inline=False
    )

    embed.add_field(
        name="📋 **Kayıt Yönetimi**",
        value="""
```yaml
📖 Görüntüle:
  !notlar <kullanıcı_id>

🗑️ Sil:
  !notsil <kullanıcı_id> <tür> <index>

🧹 Temizle:
  !nottemizle <kullanıcı_id>
```
        """,
        inline=True
    )

    embed.add_field(
        name="🤖 **AutoMod Kontrol**",
        value="""
```ini
[Yönetim]
!automod = Ayarları göster
!automod toggle = Aç/kapat

[Kelime Filtresi]
!automod blacklist add <kelime>
!automod blacklist remove <kelime>

[İhlaller]
!automod ihlallar @kullanıcı
!automod ihlalsifirla [@kullanıcı]
```
        """,
        inline=True
    )

    embed.add_field(
        name="🧹 **Temizlik**",
        value="""
```css
!temizle <miktar>
/* Max 100 mesaj silebilir */
```
        """,
        inline=False
    )

    embed.set_footer(
        text="🔒 Bu komutlar yönetici/moderatör yetkisi gerektirir",
        icon_url="https://cdn.discordapp.com/emojis/936297844127703080.png"
    )
    
    return embed

def create_level_embed():
    embed = discord.Embed(
        title="",
        color=0xFFD700  # Altın rengi
    )
    
    embed.add_field(
        name="",
        value="""
⭐ **SEVİYE SİSTEMİ**
─────────────────────
*Aktifliğiniz ödüllendirilir*

🏆 **Nasıl XP Kazanırsınız?**
```diff
+ Sohbet etmek     → 15-25 XP
+ Sesli kanal      → 20-30 XP/dakika  
+ Günlük bonus     → 100-200 XP
- Spam yapmak      → XP kaybı
```
        """,
        inline=False
    )

    embed.add_field(
        name="📊 **Seviye Komutları**",
        value="""
```autohotkey
!seviye [@kullanıcı]
; Seviye kartını gösterir

!sıralama [sayfa]
; Top 10 listesi

!xpekle @kullanıcı <miktar>
; Yönetici: XP ekle

!xpsıfırla @kullanıcı
; Yönetici: XP sıfırla
```
        """,
        inline=True
    )

    embed.add_field(
        name="🎁 **Seviye Ödülleri**",
        value="""
```yaml
Seviye 5:  🥉 Bronz Üye
Seviye 10: 🥈 Gümüş Üye  
Seviye 20: 🥇 Altın Üye
Seviye 35: 💎 Elmas Üye
Seviye 50: 👑 Efsane Üye

Bonus: Her seviye → Hız artışı!
```
        """,
        inline=True
    )

    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/874750808388395008.gif")
    embed.set_footer(text="💫 Seviye atladığınızda otomatik bildirim alırsınız!")
    
    return embed

def create_fun_embed():
    """Eğlence ana sayfa - Navigasyon ile"""
    embed = discord.Embed(
        title="",
        color=0xFF69B4  # Pembe ton
    )
    
    embed.add_field(
        name="",
        value="""
🎭 **EĞLENCE MERKEZİ**
─────────────────────────────
*Anime karakterleriyle etkileşim dünyası*

🎮 **2 Sayfa Dolu Komut!**
        """,
        inline=False
    )

    embed.add_field(
        name="📖 **Sayfa 1: Etkileşim**",
        value="""
```yaml
💝 Romantik:
  - !sarıl, !kucakla, !öp, !el-tut

🤗 Dostluk:  
  - !okşa, !beşlik-çak, !boop, !selamla

🎮 Şakacı:
  - !dürt, !gıdıkla, !yala, !kokla
```
        """,
        inline=True
    )
    
    embed.add_field(
        name="📖 **Sayfa 2: Aksiyon & Duygular**",
        value="""
```yaml
⚔️ Savaşçı:
  - !tokatlat, !yumrukla, !ısır, !öldür

😊 Duygular:
  - !gülümse, !dans, !mutlu, !utanç

😔 Üzgün Anlar:
  - !ağla, !somurt, !uykulu, !sinirli
```
        """,
        inline=True
    )

    embed.add_field(
        name="🌟 **Nasıl Kullanılır?**",
        value="""
> **Birini hedef al:** `!sarıl @arkadaş` 
> **Tek başına:** `!dans` (kendin dans edersin)
> **Combo yap:** `!sarıl @kişi` → `!gülümse`

📱 **Detaylar için sayfa butonlarını kullan!**
        """,
        inline=False
    )

    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/947141230345195530.gif")
    embed.set_footer(text="🎭 Sayfa butonlarıyla detaylı komutları keşfedin!")
    
    return embed

def create_fun_embed_page1():
    """Eğlence komutları sayfa 1 - Etkileşim komutları"""
    embed = discord.Embed(
        title="",
        color=0xFF69B4  # Pembe ton
    )
    
    embed.add_field(
        name="",
        value="""
🎭 **EĞLENCE MERKEZİ** | Sayfa 1/2
─────────────────────────────
*💕 Etkileşim ve Sevgi Komutları*
        """,
        inline=False
    )

    embed.add_field(
        name="💝 **Romantik**",
        value="""
```fix
+ !sarıl <@user>    → Sarılma
+ !kucakla <@user>  → Kucaklama  
+ !öp <@user>       → Öpücük
+ !el-tut <@user>   → El tutma
```
        """,
        inline=True
    )
    
    embed.add_field(
        name="🤗 **Dostluk**",
        value="""
```yaml
+ !okşa <@user>     → Okşama
+ !beşlik-çak <@user> → Beşlik çakma
+ !boop <@user>     → Burun dokunma
+ !selamla <@user>  → Selamlama
```
        """,
        inline=True
    )

    embed.add_field(
        name="🎮 **Şakacı**",
        value="""
```css
+ !dürt <@user>     → Dürtme
+ !gıdıkla <@user>  → Gıdıklama
+ !yala <@user>     → Yalama
+ !kokla <@user>    → Koklama
```
        """,
        inline=True
    )
    
    embed.add_field(
        name="💫 **Kullanım Örnekleri**",
        value="""
> `!sarıl @Luna` → Luna'yı sarılar ❤️
> `!okşa @Mavi` → Mavi'yi okşar 🥰
> `!beşlik-çak @Kırmızı` → Beşlik çakarsınız! ✋
        """,
        inline=False
    )

    embed.set_footer(text="🌟 Sayfa 1/2 • Anime karakterli etkileşim komutları")
    
    return embed

def create_fun_embed_page2():
    """Eğlence komutları sayfa 2 - Aksiyon ve duygular"""
    embed = discord.Embed(
        title="",
        color=0xFF1493  # Daha koyu pembe
    )
    
    embed.add_field(
        name="",
        value="""
🎭 **EĞLENCE MERKEZİ** | Sayfa 2/2
─────────────────────────────
*⚔️ Aksiyon ve Duygusal İfadeler*
        """,
        inline=False
    )

    embed.add_field(
        name="⚔️ **Savaşçı**",
        value="""
```diff
- !tokatlat <@user> → Tokatlama
- !yumrukla <@user> → Yumruklama
- !ısır <@user>     → Isırma
- !öldür <@user>    → Öldürme (şaka)
- !tut <@user>      → Tutma
```
        """,
        inline=True
    )
    
    embed.add_field(
        name="😊 **Duygular**",
        value="""
```yaml
+ !gülümse   → Gülümseme
+ !dans      → Dans etme
+ !mutlu     → Mutluluk
+ !utanç     → Utanma
+ !kibirli   → Kibirlenmek
```
        """,
        inline=True
    )

    embed.add_field(
        name="😔 **Üzgün Anlar**",
        value="""
```bash
# Üzgün ifadeler
!ağla      → Ağlama
!somurt    → Somurtma  
!uykulu    → Uykulu olma
!sinirli   → Sinirlenmek
```
        """,
        inline=True
    )
    
    embed.add_field(
        name="🤔 **Diğer**",
        value="""
```ini
[Hareketler]
!düşün     = Düşünme pozu
!omuz-silk = Omuz silkme
!sallan    = Sallanma
!sırıt     = Sırıtma
```
        """,
        inline=False
    )

    embed.add_field(
        name="⚡ **Pro İpucu**",
        value="""
> **Tek başına:** `!dans` → Sen dans edersin 💃
> **Birine karşı:** `!tokatlat @kişi` → O kişiyi tokatlarsın 👋
> **Kombo:** `!sarıl @arkadaş` sonra `!gülümse` 😄
        """,
        inline=False
    )

    embed.set_footer(text="🌟 Sayfa 2/2 • Tüm komutlar anime gif'leri kullanır!")
    
    return embed

def create_cekilis_embed():
    embed = discord.Embed(
        title="",
        color=0x9B59B6  # Mor ton
    )
    
    embed.add_field(
        name="",
        value="""
🎉 **ÇEKİLİŞ DÜNYASI**
─────────────────────
*Heyecan dolu çekilişler*
        """,
        inline=False
    )

    embed.add_field(
        name="🚀 **Çekiliş Başlat**",
        value="""
```bash
# Basit çekiliş
!çekiliş 1h 1 Discord Nitro

# Rol şartlı çekiliş  
!çekiliş 2d 3 @Üye 100TL Steam

# Süre formatları
1s = 1 saniye    1m = 1 dakika
1h = 1 saat      1d = 1 gün
```
        """,
        inline=False
    )

    embed.add_field(
        name="⚙️ **Yönetim**",
        value="""
```ini
[Kontrol]
!çekilişler = Aktif listesi
!çekilişbilgi <id> = Detaylar

[İşlemler] 
!çekilişbitir <id> = Erkenden bitir
!yenidençek <id> = Yeniden çek
```
        """,
        inline=True
    )

    embed.add_field(
        name="🎯 **İpuçları**",
        value="""
```markdown
• Çekilişe katılmak için 🎉 tıklayın
• Minimum rol gereksinimi koyabilirsiniz
• Birden fazla kazanan seçebilirsiniz
• Çekiliş bittikten sonra yeniden çekilebilir
```
        """,
        inline=True
    )

    embed.set_footer(text="🍀 Şansınızı deneyin ve kazanın!")
    
    return embed

def create_invite_embed():
    embed = discord.Embed(
        title="",
        color=0x3498DB  # Mavi ton
    )
    
    embed.add_field(
        name="",
        value="""
🔗 **DAVET TRAKİNG SİSTEMİ**
─────────────────────────────
*Her davet sayılır ve ödüllendirilir*
        """,
        inline=False
    )

    embed.add_field(
        name="📊 **İstatistikler**",
        value="""
```yaml
!davet [@kullanıcı]
├─ Toplam Davet
├─ Geçerli Davet  
├─ Sahte Davet
└─ Ayrılan Davet

!davet sıralama [limit]
└─ Top davetçiler listesi
```
        """,
        inline=True
    )

    embed.add_field(
        name="🛠️ **Yönetim**",
        value="""
```diff
+ !davet bonus @user 10
  Bonus davet ekler

+ !davet oluştur [limit] [süre]
  Özel davet linki

- !davet sıfırla [@user]
  İstatistikleri sıfırlar
```
        """,
        inline=True
    )

    embed.add_field(
        name="🏆 **Davet Ödülleri**",
        value="""
```markdown
 5 Davet → 🥉 Davet Uzmanı
15 Davet → 🥈 Davet Ustası  
30 Davet → 🥇 Davet Efsanesi
50 Davet → 👑 Davet Kralı

Bonus: Her 10 davet → Özel perk!
```
        """,
        inline=False
    )

    embed.set_footer(text="📈 Sunucuyu büyütün, ödüllerinizi kazanın!")
    
    return embed

def create_info_embed():
    embed = discord.Embed(
        title="",
        color=0x17A2B8  # Info mavi
    )
    
    embed.add_field(
        name="",
        value="""
ℹ️ **BİLGİ MERKEZİ**
─────────────────
*Her şeyi öğrenin*
        """,
        inline=False
    )

    embed.add_field(
        name="🖥️ **Sunucu**",
        value="""
```css
!sunucu
/* Detaylı sunucu istatistikleri */

!ping  
/* Bot performans ölçümü */
```
        """,
        inline=True
    )

    embed.add_field(
        name="👤 **Kullanıcı**",
        value="""
```css
!kullanici [@user]
/* Profil bilgileri */

!avatar [@user]
/* Avatar gösterici */

!banner [@user]  
/* Banner gösterici */
```
        """,
        inline=True
    )

    embed.add_field(
        name="🤖 **Bot Bilgisi**",
        value="""
```yaml
!botinfo:
  - Uptime
  - Memory Usage  
  - Server Count
  - Command Stats
```
        """,
        inline=False
    )

    embed.set_footer(text="💡 Bilgi komutları herkese açıktır")
    
    return embed

def create_user_info_embed():
    return create_info_embed()  # Birleştirdik

class FunNavigationView(View):
    """Eğlence komutları için özel navigation sistemi"""
    def __init__(self, ctx):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.current_fun_page = 0  # 0=ana, 1=sayfa1, 2=sayfa2
        
        # Sayfa butonları
        self.add_item(FunHomeButton())
        self.add_item(FunPage1Button())
        self.add_item(FunPage2Button())
        self.add_item(BackToMainButton())
        self.add_item(CloseButton())
    
    async def update_embed(self, interaction):
        if self.current_fun_page == 0:
            embed = create_fun_embed()
        elif self.current_fun_page == 1:
            embed = create_fun_embed_page1()
        elif self.current_fun_page == 2:
            embed = create_fun_embed_page2()
        else:
            embed = create_fun_embed()
        
        await interaction.message.edit(embed=embed, view=self)

class FunHomeButton(Button):
    def __init__(self):
        super().__init__(emoji="🎭", style=discord.ButtonStyle.secondary, label="Ana Sayfa")
    
    async def callback(self, interaction):
        if interaction.user != self.view.ctx.author:
            return await interaction.response.send_message("❌ Bu menüyü sadece komutu kullanan kişi kullanabilir!", ephemeral=True)
        
        await interaction.response.defer()
        self.view.current_fun_page = 0
        await self.view.update_embed(interaction)

class FunPage1Button(Button):
    def __init__(self):
        super().__init__(emoji="💕", style=discord.ButtonStyle.primary, label="Etkileşim")
    
    async def callback(self, interaction):
        if interaction.user != self.view.ctx.author:
            return await interaction.response.send_message("❌ Bu menüyü sadece komutu kullanan kişi kullanabilir!", ephemeral=True)
        
        await interaction.response.defer()
        self.view.current_fun_page = 1
        await self.view.update_embed(interaction)

class FunPage2Button(Button):
    def __init__(self):
        super().__init__(emoji="⚔️", style=discord.ButtonStyle.primary, label="Aksiyon")
    
    async def callback(self, interaction):
        if interaction.user != self.view.ctx.author:
            return await interaction.response.send_message("❌ Bu menüyü sadece komutu kullanan kişi kullanabilir!", ephemeral=True)
        
        await interaction.response.defer()
        self.view.current_fun_page = 2
        await self.view.update_embed(interaction)

class BackToMainButton(Button):
    def __init__(self):
        super().__init__(emoji="↩️", style=discord.ButtonStyle.secondary, label="Ana Menü")
    
    async def callback(self, interaction):
        if interaction.user != self.view.ctx.author:
            return await interaction.response.send_message("❌ Bu menüyü sadece komutu kullanan kişi kullanabilir!", ephemeral=True)
        
        await interaction.response.defer()
        # Ana yardım menüsüne dön
        view = NavigationView(self.view.ctx)
        embed = create_home_embed()
        message = await interaction.message.edit(embed=embed, view=view)
        view.message = message

class NavigationView(View):
    def __init__(self, ctx):
        super().__init__(timeout=180)  # 3 dakika timeout
        self.ctx = ctx
        self.current_page = "home"
        self.page_order = ["home", "moderation", "level", "fun", "cekilis", "invite", "info"]
        self.current_index = 0
        
        # Ana kategori seçimi
        self.category_select = Select(
            placeholder="🔍 Kategori seçin...",
            options=[
                discord.SelectOption(
                    label="Ana Sayfa", 
                    description="Bot genel bilgileri", 
                    emoji="🏠", 
                    value="home"
                ),
                discord.SelectOption(
                    label="Moderasyon", 
                    description="Sunucu yönetim araçları", 
                    emoji="🛡️", 
                    value="moderation"
                ),
                discord.SelectOption(
                    label="Seviye Sistemi", 
                    description="XP ve seviye komutları", 
                    emoji="⭐", 
                    value="level"
                ),
                discord.SelectOption(
                    label="Eğlence", 
                    description="Anime etkileşim komutları", 
                    emoji="🎭", 
                    value="fun"
                ),
                discord.SelectOption(
                    label="Çekiliş", 
                    description="Çekiliş yönetimi", 
                    emoji="🎉", 
                    value="cekilis"
                ),
                discord.SelectOption(
                    label="Davet Takip", 
                    description="Davet istatistikleri", 
                    emoji="🔗", 
                    value="invite"
                ),
                discord.SelectOption(
                    label="Bilgi Komutları", 
                    description="Sunucu ve kullanıcı bilgileri", 
                    emoji="ℹ️", 
                    value="info"
                )
            ]
        )
        self.category_select.callback = self.select_callback
        self.add_item(self.category_select)
          # Navigasyon butonları
        self.add_item(HomeButton())
        self.add_item(PrevButton())
        self.add_item(NextButton())
        self.add_item(CloseButton())
    
    async def select_callback(self, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "❌ Bu menüyü sadece komutu kullanan kişi kullanabilir!", 
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        selected = self.category_select.values[0]
        self.current_page = selected
        self.current_index = self.page_order.index(selected) if selected in self.page_order else 0
        
        # Eğlence seçilirse özel navigation ile aç
        if selected == "fun":
            view = FunNavigationView(self.ctx)
            embed = create_fun_embed()
            message = await interaction.message.edit(embed=embed, view=view)
            view.message = message
            return
        
        embed = self.get_embed_for_category(selected)
        await interaction.message.edit(embed=embed, view=self)
    
    def get_embed_for_category(self, category):
        embeds = {
            "home": create_home_embed(),
            "moderation": create_moderation_embed(),
            "level": create_level_embed(),
            "fun": create_fun_embed(),
            "cekilis": create_cekilis_embed(),
            "invite": create_invite_embed(),
            "info": create_info_embed()
        }
        return embeds.get(category, create_home_embed())
    
    async def on_timeout(self):
        try:
            # Timeout olduğunda butonları devre dışı bırak
            for item in self.children:
                item.disabled = True
            
            # Embed'e timeout mesajı ekle
            embed = discord.Embed(
                title="⏰ Zaman Aşımı",
                description="Bu yardım menüsünün süresi doldu. Yeni bir tane açmak için `!yardım` komutunu tekrar kullanın.",
                color=0x95A5A6
            )
            
            # Mesajı güncelle (eğer hala erişilebilirse)
            message = await self.ctx.fetch_message(self.message.id)
            await message.edit(embed=embed, view=self)
        except:
            pass  # Mesaj silinmişse veya erişilemiyorsa sessizce geç

class HomeButton(Button):
    def __init__(self):
        super().__init__(emoji="🏠", style=discord.ButtonStyle.secondary, label="Ana Sayfa")
    
    async def callback(self, interaction):
        if interaction.user != self.view.ctx.author:
            return await interaction.response.send_message("❌ Bu menüyü sadece komutu kullanan kişi kullanabilir!", ephemeral=True)
        
        await interaction.response.defer()
        self.view.current_page = "home"
        self.view.current_index = 0
        embed = create_home_embed()
        await interaction.message.edit(embed=embed, view=self.view)

class PrevButton(Button):
    def __init__(self):
        super().__init__(emoji="⬅️", style=discord.ButtonStyle.primary, label="Önceki")
    
    async def callback(self, interaction):
        if interaction.user != self.view.ctx.author:
            return await interaction.response.send_message("❌ Bu menüyü sadece komutu kullanan kişi kullanabilir!", ephemeral=True)
        
        await interaction.response.defer()
        
        # Önceki sayfaya git
        if self.view.current_index > 0:
            self.view.current_index -= 1
            self.view.current_page = self.view.page_order[self.view.current_index]
            
            if self.view.current_page == "fun":
                # Eğlence sayfası için özel navigasyon
                view = FunNavigationView(self.view.ctx)
                embed = create_fun_embed()
                message = await interaction.message.edit(embed=embed, view=view)
                view.message = message
            else:
                embed = self.view.get_embed_for_category(self.view.current_page)
                await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.followup.send("⚠️ Bu zaten ilk sayfa!", ephemeral=True)

class NextButton(Button):
    def __init__(self):
        super().__init__(emoji="➡️", style=discord.ButtonStyle.primary, label="Sonraki")
    
    async def callback(self, interaction):
        if interaction.user != self.view.ctx.author:
            return await interaction.response.send_message("❌ Bu menüyü sadece komutu kullanan kişi kullanabilir!", ephemeral=True)
        
        await interaction.response.defer()
        
        # Sonraki sayfaya git
        if self.view.current_index < len(self.view.page_order) - 1:
            self.view.current_index += 1
            self.view.current_page = self.view.page_order[self.view.current_index]
            
            if self.view.current_page == "fun":
                # Eğlence sayfası için özel navigasyon
                view = FunNavigationView(self.view.ctx)
                embed = create_fun_embed()
                message = await interaction.message.edit(embed=embed, view=view)
                view.message = message
            else:
                embed = self.view.get_embed_for_category(self.view.current_page)
                await interaction.message.edit(embed=embed, view=self.view)
        else:
            await interaction.followup.send("⚠️ Bu zaten son sayfa!", ephemeral=True)

class CloseButton(Button):
    def __init__(self):
        super().__init__(emoji="🗑️", style=discord.ButtonStyle.danger, label="Kapat")
    
    async def callback(self, interaction):
        if interaction.user != self.view.ctx.author:
            return await interaction.response.send_message("❌ Bu menüyü sadece komutu kullanan kişi kullanabilir!", ephemeral=True)
        
        await interaction.response.defer()
        await interaction.message.delete()

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')

    @commands.command(name="yardım", aliases=["yardim", "help", "h", "y"])
    @commands.cooldown(1, 3, BucketType.user)
    @commands.check(command_check())
    async def yardim(self, ctx, command_name=None):
        """🌟 İnteraktif yardım menüsü - Tüm komutları keşfedin!"""
        
        if command_name:
            # Belirli komut yardımı - daha şık tasarım
            command = self.bot.get_command(command_name)
            if not command:
                embed = discord.Embed(
                    title="❌ Komut Bulunamadı",
                    description=f"**`{command_name}`** adında bir komut bulunamadı.\n\n💡 Tüm komutları görmek için `!yardım` yazın.",
                    color=0xE74C3C
                )
                return await ctx.send(embed=embed)
                
            embed = discord.Embed(
                title="",
                color=0x8B008B
            )
            
            # Özel komut yardım formatı
            embed.add_field(
                name="",
                value=f"""
📖 **{command.name.upper()}** KOMUTU
─────────────────────────
*{command.help or "Açıklama bulunmuyor."}*
                """,
                inline=False
            )
            
            usage = f"!{command.name}"
            if command.signature:
                usage = f"!{command.name} {command.signature}"
                
            embed.add_field(
                name="📝 **Kullanım**", 
                value=f"```fix\n{usage}\n```", 
                inline=False
            )
            
            if command.aliases:
                embed.add_field(
                    name="🔄 **Alternatif Komutlar**", 
                    value="```yaml\n" + "\n".join([f"!{alias}" for alias in command.aliases]) + "\n```",
                    inline=False
                )
            
            embed.set_thumbnail(url="https://i.ibb.co/wvQCt9C/lunaris-pp.png")
            embed.set_footer(text="💡 Ana menüye dönmek için !yardım yazın")
                
            return await ctx.send(embed=embed)
        
        # Ana yardım menüsü
        view = NavigationView(ctx)
        embed = create_home_embed()
        message = await ctx.send(embed=embed, view=view)
        view.message = message  # Timeout için mesaj referansı

    @commands.command(name="ping")
    async def ping(self, ctx):
        """🏓 Bot performansını ve gecikme süresini ölçer"""
        
        # Websocket gecikmesi
        ws_latency = round(self.bot.latency * 1000)
        
        # Mesaj gecikmesi için başlangıç zamanı
        start_time = time.time()
        message = await ctx.send("📡 Ölçüm yapılıyor...")
        end_time = time.time()
        msg_latency = round((end_time - start_time) * 1000)

        # Renk belirleme
        if ws_latency < 100:
            color = 0x00FF00  # Yeşil - Mükemmel
            status = "🟢 Mükemmel"
        elif ws_latency < 200:
            color = 0x90EE90  # Açık yeşil - İyi  
            status = "🟡 İyi"
        elif ws_latency < 400:
            color = 0xFFD700  # Sarı - Orta
            status = "🟠 Orta"
        else:
            color = 0xFF0000  # Kırmızı - Kötü
            status = "🔴 Kötü"

        embed = discord.Embed(
            title="",
            color=color
        )
        
        embed.add_field(
            name="",
            value=f"""
🏓 **PONG!** 
─────────────
**Bağlantı Durumu:** {status}
            """,
            inline=False
        )
        
        embed.add_field(
            name="📊 **Performans Metrikleri**",
            value=f"""
```yaml
Websocket Ping: {ws_latency}ms
Mesaj Gecikmesi: {msg_latency}ms
Ortalama Ping: {(ws_latency + msg_latency) // 2}ms
```
            """,
            inline=True
        )
        
        embed.add_field(
            name="📈 **Durum Göstergeleri**",
            value="""
```diff
+ 0-100ms   → Mükemmel
+ 100-200ms → İyi  
+ 200-400ms → Orta
- 400ms+    → Kötü
```
            """,
            inline=True
        )

        embed.set_footer(
            text=f"⚡ Bot Durumu: {status}",
            icon_url="https://i.ibb.co/wvQCt9C/lunaris-pp.png"
        )
        
        await message.edit(content=None, embed=embed)

    @commands.command(name="temizle", aliases=["clear", "sil"])
    @commands.cooldown(1, 5, BucketType.user)
    @has_mod_role()
    async def temizle(self, ctx, miktar: int):
        """🧹 Belirtilen sayıda mesajı temizler (Max: 100)"""
        
        if miktar <= 0:
            embed = discord.Embed(
                title="❌ Geçersiz Sayı",
                description="Silinecek mesaj sayısı **0**'dan büyük olmalıdır.",
                color=0xE74C3C
            )
            return await ctx.send(embed=embed)
            
        if miktar > 100:
            embed = discord.Embed(
                title="❌ Limit Aşımı", 
                description="En fazla **100** mesaj silebilirim.\n\n💡 Daha fazla mesaj silmek için komutu tekrar kullanın.",
                color=0xE74C3C
            )
            return await ctx.send(embed=embed)
        
        # Mesajları sil
        deleted = await ctx.channel.purge(limit=miktar + 1)
        deleted_count = len(deleted) - 1  # Komut mesajını sayma

        # Onay mesajı
        embed = discord.Embed(
            title="🧹 Temizlik Tamamlandı!",
            description=f"""
**{deleted_count}** mesaj başarıyla silindi.

📍 **Kanal:** {ctx.channel.mention}
👤 **Yetkili:** {ctx.author.mention}
            """,
            color=0x00FF00
        )
        
        embed.set_footer(text="Bu mesaj 5 saniye sonra silinecek")
        
        info_message = await ctx.send(embed=embed)
        
        # 5 saniye sonra bilgi mesajını sil
        await asyncio.sleep(5)
        try:
            await info_message.delete()
        except:
            pass  # Mesaj zaten silinmişse hata verme

async def setup(bot):
    await bot.add_cog(Utilities(bot))
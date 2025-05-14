# LunarisBot - Discord Moderasyon Botu

LunarisBot, gelişmiş moderasyon, çekiliş ve davet takibi özellikleriyle Discord sunucunuzu yönetmenize yardımcı olan bir Discord botudur.

## 🚀 Özellikler

- **Moderasyon Komutları**: Uyarı, timeout, yasaklama işlemleri
- **Çekiliş Sistemi**: Gelişmiş çekiliş yönetimi
- **Davet Takibi**: Kullanıcıların davetlerini izleme
- **Web Dashboard**: Kolay yönetim için web arayüzü
- **AutoMod**: Otomatik moderasyon ve içerik filtreleme
- **Etkinlik Logları**: Kapsamlı log sistemi

## 📋 Kurulum

1. Repoyu klonlayın:
   ```
   git clone https://github.com/kullaniciadi/lunaris-bot.git
   ```

2. Gerekli paketleri yükleyin:
   ```
   pip install -r requirements.txt
   ```

3. `.env` dosyası oluşturun:
   ```
   BOT_TOKEN=your_discord_bot_token
   DISCORD_CLIENT_ID=your_client_id
   DISCORD_CLIENT_SECRET=your_client_secret
   DISCORD_REDIRECT_URI=http://localhost:8080/callback
   DASHBOARD_BASE_URL=http://localhost
   DASHBOARD_PORT=8080
   ```

4. Bot'u başlatın:
   ```
   python main.py
   ```

## 🛠️ Komutlar

### Moderasyon Komutları
- `!uyar @kullanıcı [sebep]` - Kullanıcıyı uyarır
- `!zaman @kullanıcı [süre] [sebep]` - Kullanıcıya timeout verir
- `!yasakla @kullanıcı [sebep]` - Kullanıcıyı yasaklar

### Çekiliş Komutları
- `!çekiliş [süre] [kazanan sayısı] [ödül]` - Çekiliş başlatır
- `!çekilişbitir [mesaj_id]` - Çekilişi erken bitirir
- `!yenidençek [mesaj_id]` - Yeni kazanan seçer

### Not Sistemi Komutları
- `!notlar @kullanıcı` - Kullanıcının moderasyon geçmişini gösterir
- `!notsil @kullanıcı [tip] [index]` - Belirli bir notu siler
- `!nottemizle @kullanıcı [tip]` - Kullanıcının notlarını temizler

## 🧑‍💻 Geliştirme

### Yeni Cog Ekleme

1. `cogs` klasöründe yeni bir Python dosyası oluşturun
2. Aşağıdaki temel yapıyı kullanın:

```python
import discord
from discord.ext import commands
from utils.permissions import has_mod_role

class YeniCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="komut")
    @has_mod_role()
    async def ornek_komut(self, ctx):
        await ctx.send("Merhaba dünya!")
        
async def setup(bot):
    await bot.add_cog(YeniCog(bot))
```

## 📝 Lisans

Bu proje [MIT](LICENSE) lisansı altında lisanslanmıştır.
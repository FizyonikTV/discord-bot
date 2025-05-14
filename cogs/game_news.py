import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import json
import os
from datetime import datetime, timedelta
import logging
from config.config import GAME_WEBHOOK_URL

class GameNews(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = "config/game_news_config.json"
        self.last_news_path = "data/last_news.json"
        self.session = None
        self.load_config()
        self.check_news.start()
    
    def cog_unload(self):
        """Cog kapatıldığında çalışan görevleri temizler"""
        self.check_news.cancel()
        if self.session and not self.session.closed:
            asyncio.create_task(self.session.close())
            
    def load_config(self):
        """Webhook yapılandırmasını yükler"""
        default_config = {
            "enabled": True,
            "webhook_url": GAME_WEBHOOK_URL,  # WEBHOOK_URL yerine GAME_WEBHOOK_URL kullanılıyor
            "check_interval_minutes": 60,
            "news_sources": {
                "epic_games": True,
                "steam_deals": True
            },
            "min_discount_percent": 75,
            "webhook_name": "Lunaris - Oyun Habercisi",
            "webhook_avatar": "https://i.ibb.co/6RQcJQVX/Lunaris-Banner-Ekstra-Orijinal.webp",
            "news_channel_id": 1353317993060237322,  # Kanal ID'si zaten ayarlanmış
            "ping_role_id": 1353318526265331763  # Etiketlenecek rol ID'si eklendi
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
            logging.error(f"Oyun haberleri yapılandırması yüklenirken hata: {e}")
            self.config = default_config
            
    def save_config(self):
        """Webhook yapılandırmasını kaydeder"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Oyun haberleri yapılandırması kaydedilirken hata: {e}")
            return False
            
    def load_last_news(self):
        """Son gönderilen haberleri yükler"""
        try:
            if os.path.exists(self.last_news_path):
                with open(self.last_news_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"epic_free": [], "steam_deals": []}
        except Exception as e:
            logging.error(f"Son haberler yüklenirken hata: {e}")
            return {"epic_free": [], "steam_deals": []}
            
    def save_last_news(self, data):
        """Son gönderilen haberleri kaydeder"""
        try:
            os.makedirs(os.path.dirname(self.last_news_path), exist_ok=True)
            with open(self.last_news_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Son haberler kaydedilirken hata: {e}")
            return False
            
    async def get_session(self):
        """HTTP isteği için oturum alır"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)  # 30 saniye timeout
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def fetch_with_retry(self, url, max_retries=3, delay=5):
        """Belirtilen URL'den veri çeker, başarısız olursa yeniden dener"""
        session = await self.get_session()
        for attempt in range(max_retries):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logging.warning(f"API yanıt kodu: {response.status}, {url}")
            except Exception as e:
                logging.warning(f"Bağlantı denemesi {attempt+1}/{max_retries} başarısız: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)  # Bir süre bekle ve tekrar dene
        
        # Tüm denemeler başarısız oldu
        logging.error(f"URL'ye erişilemedi (maksimum yeniden deneme sayısı aşıldı): {url}")
        return None
        
    async def fetch_epic_free_games(self):
        """Epic Games'teki ücretsiz oyunları alır"""
        try:
            url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
            data = await self.fetch_with_retry(url)
            
            if not data:
                return []
                
            games = []
            if 'data' in data and 'Catalog' in data['data'] and 'searchStore' in data['data']['Catalog']:
                elements = data['data']['Catalog']['searchStore']['elements']
                
                for game in elements:
                    # Ücretsiz oyunları filtrele
                    if game.get('promotions') and game['promotions'].get('promotionalOffers'):
                        promotional_offers = game['promotions']['promotionalOffers']
                        if promotional_offers and len(promotional_offers) > 0:
                            offer = promotional_offers[0]
                            if 'promotionalOffers' in offer and len(offer['promotionalOffers']) > 0:
                                price_info = offer['promotionalOffers'][0]
                                if price_info.get('discountSetting', {}).get('discountPercentage') == 0:
                                    # Bu bir ücretsiz oyun
                                    game_info = {
                                        "title": game['title'],
                                        "description": game.get('description', 'Açıklama yok'),
                                        "image": game.get('keyImages', [{}])[0].get('url', '') if game.get('keyImages') else '',
                                        "url": f"https://www.epicgames.com/store/product/{game.get('urlSlug', game['title'])}",
                                        "start_date": price_info.get('startDate', ''),
                                        "end_date": price_info.get('endDate', ''),
                                        "original_price": game.get('price', {}).get('totalPrice', {}).get('fmtPrice', {}).get('originalPrice', 'Bilinmiyor'),
                                        "id": game.get('id', '')
                                    }
                                    games.append(game_info)
                
                return games
        except Exception as e:
            logging.error(f"Epic Games ücretsiz oyunları alırken hata: {e}")
            return []
            
    async def fetch_steam_deals(self):
        """Steam'deki büyük indirimleri alır"""
        try:
            url = f"https://www.cheapshark.com/api/1.0/deals?storeID=1&upperPrice=15&pageSize=10&sortBy=discount"
            data = await self.fetch_with_retry(url)
            
            if not data:
                return []
                
            # Threshold'dan büyük indirimleri filtrele
            min_discount = self.config.get('min_discount_percent', 75)
            deals = []
            
            for deal in data:
                discount = float(deal.get('savings', '0'))
                if discount >= min_discount:
                    deal_info = {
                        "title": deal.get('title', 'İsimsiz Oyun'),
                        "discount_percent": int(discount),
                        "sale_price": deal.get('salePrice', 'Bilinmiyor'),
                        "normal_price": deal.get('normalPrice', 'Bilinmiyor'),
                        "steam_rating": deal.get('steamRatingText', 'Değerlendirme yok'),
                        "steam_rating_count": deal.get('steamRatingCount', '0'),
                        "image": f"https://cdn.cloudflare.steamstatic.com/steam/apps/{deal.get('steamAppID', '')}/header.jpg",
                        "url": f"https://store.steampowered.com/app/{deal.get('steamAppID', '')}",
                        "deal_id": deal.get('dealID', '')
                    }
                    deals.append(deal_info)
                    
            return deals
        except Exception as e:
            logging.error(f"Steam indirimlerini alırken hata: {e}")
            return []
    
    @tasks.loop(minutes=60)  # Kontrol aralığını config'den alacak
    async def check_news(self):
        """Periyodik olarak oyun fırsatlarını kontrol eder"""
        if not self.config.get('enabled', False):
            return
            
        # Kontrol aralığını yapılandırmadan al
        self.check_news.change_interval(minutes=self.config.get('check_interval_minutes', 60))
        
        # Son gönderilen haberleri kontrol et
        last_news = self.load_last_news()
        new_updates = {"epic_free": [], "steam_deals": []}
        should_send = False
        
        # Epic Games Store ücretsiz oyunları
        if self.config.get('news_sources', {}).get('epic_games', True):
            epic_games = await self.fetch_epic_free_games()
            
            # Son gönderilen oyunlarla karşılaştır
            for game in epic_games:
                if game['id'] not in [g.get('id') for g in last_news.get('epic_free', [])]:
                    new_updates['epic_free'].append(game)
                    should_send = True
        
        # Steam indirimleri
        if self.config.get('news_sources', {}).get('steam_deals', True):
            steam_deals = await self.fetch_steam_deals()
            
            # Son gönderilen indirimlerle karşılaştır
            for deal in steam_deals:
                if deal['deal_id'] not in [d.get('deal_id') for d in last_news.get('steam_deals', [])]:
                    new_updates['steam_deals'].append(deal)
                    should_send = True
        
        # Yeni haberler varsa webhook gönder
        if should_send:
            await self.send_news_webhook(new_updates)
            
            # Son gönderilen haberleri güncelle
            last_news['epic_free'].extend(new_updates['epic_free'])
            last_news['steam_deals'].extend(new_updates['steam_deals'])
            
            # Son 20 haberi tut (her kategoride)
            last_news['epic_free'] = last_news['epic_free'][-20:]
            last_news['steam_deals'] = last_news['steam_deals'][-20:]
            
            # Kaydedilen son haberleri güncelle
            self.save_last_news(last_news)
    
    @check_news.before_loop
    async def before_check_news(self):
        """Haber kontrol döngüsü başlamadan önce botu bekle"""
        await self.bot.wait_until_ready()
    
    async def send_news_webhook(self, updates):
        """Yeni haberleri webhook ile gönderir"""
        webhook_url = self.config.get('webhook_url')
        news_channel_id = self.config.get('news_channel_id')
        
        # Webhook veya kanal kontrolü
        if not webhook_url and not news_channel_id:
            logging.error("Oyun haberleri göndermek için webhook URL veya kanal ID gerekli.")
            return
            
        # Epic Games ücretsiz oyunları
        for game in updates['epic_free']:
            embed = discord.Embed(
                title=f"🎮 ÜCRETSİZ OYUN: {game['title']}",
                description=game['description'][:200] + "..." if len(game['description']) > 200 else game['description'],
                color=0x0074e4,  # Epic Games mavisi
                url=game['url']
            )
            
            # Tarihleri düzenle
            if game['start_date'] and game['end_date']:
                try:
                    start = datetime.fromisoformat(game['start_date'].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(game['end_date'].replace('Z', '+00:00'))
                    date_str = f"{start.strftime('%d %b')} - {end.strftime('%d %b %Y')}"
                    embed.add_field(name="Süre", value=date_str, inline=True)
                except:
                    embed.add_field(name="Süre", value="Sınırlı süre", inline=True)
            
            embed.add_field(name="Normal Fiyat", value=game['original_price'], inline=True)
            embed.add_field(name="Platform", value="Epic Games Store", inline=True)
            
            if game['image']:
                embed.set_image(url=game['image'])
                
            embed.set_footer(text="Epic Games Store | Ücretsiz Oyun", icon_url="https://cdn2.unrealengine.com/Unreal+Engine%2Feg-logo-filled-1255x1272-0eb9d144a0f981d1cbaaa1eb957de7a3207b31bb.png")
            
            await self.send_embed(webhook_url, news_channel_id, embed)
        
        # Steam indirimleri
        for deal in updates['steam_deals']:
            embed = discord.Embed(
                title=f"💰 BÜYÜK İNDİRİM: {deal['title']}",
                description=f"**%{deal['discount_percent']}** indirimle satın alın!",
                color=0x1b2838,  # Steam lacivert
                url=deal['url']
            )
            
            embed.add_field(name="İndirimli Fiyat", value=f"${deal['sale_price']}", inline=True)
            embed.add_field(name="Normal Fiyat", value=f"${deal['normal_price']}", inline=True)
            
            if deal['steam_rating'] != "Değerlendirme yok":
                embed.add_field(
                    name="Değerlendirme", 
                    value=f"{deal['steam_rating']} ({deal['steam_rating_count']} değerlendirme)", 
                    inline=True
                )
                
            embed.set_image(url=deal['image'])
            embed.set_footer(text="Steam | Büyük İndirim", icon_url="https://store.steampowered.com/favicon.ico")
            
            await self.send_embed(webhook_url, news_channel_id, embed)
    
    async def send_embed(self, webhook_url, channel_id, embed):
        """Embedı webhook veya kanal üzerinden gönderir"""
        try:
            # Rol etiketi oluştur
            role_mention = f"<@&{self.config.get('ping_role_id', 1353318526265331763)}>"
            
            # Webhook ile gönderme
            if webhook_url:
                session = await self.get_session()
                webhook_data = {
                    "content": role_mention,  # Rol etiketini içerik olarak ekle
                    "embeds": [embed.to_dict()],
                    "username": self.config.get('webhook_name', "Lunaris - Oyun Habercisi"),
                    "avatar_url": self.config.get('webhook_avatar', "https://i.ibb.co/6RQcJQVX/Lunaris-Banner-Ekstra-Orijinal.webp")
                }
                
                async with session.post(webhook_url, json=webhook_data) as response:
                    if response.status not in [200, 201, 204]:
                        logging.error(f"Webhook gönderilirken hata: {response.status}")
                        
            # Kanal ile gönderme
            elif channel_id:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    # Rol etiketi ile birlikte mesajı gönder
                    await channel.send(content=role_mention, embed=embed)
                else:
                    logging.error(f"Belirtilen kanal bulunamadı: {channel_id}")
        
        except Exception as e:
            logging.error(f"Embed gönderilirken hata: {e}")
    
    # Komutlar
    @commands.group(name="oyunhaber", aliases=["gameinfo", "ogn"], invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def game_news(self, ctx):
        """Oyun haberleri webhook ayarlarını gösterir"""
        embed = discord.Embed(
            title="🎮 Oyun Haberleri Ayarları",
            description="Oyun haberleri webhook'u yapılandırmasını görüntüleyin",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Durum", value=f"`{'✅ Aktif' if self.config['enabled'] else '❌ Devre Dışı'}`", inline=True)
        embed.add_field(name="Kontrol Sıklığı", value=f"`{self.config['check_interval_minutes']} dakika`", inline=True)
        embed.add_field(name="Min. İndirim", value=f"`%{self.config['min_discount_percent']}`", inline=True)
        
        # İzlenen kaynaklar
        sources = self.config.get('news_sources', {})
        sources_text = []
        if sources.get('epic_games', True):
            sources_text.append("✅ Epic Games Ücretsiz Oyunlar")
        else:
            sources_text.append("❌ Epic Games Ücretsiz Oyunlar")
            
        if sources.get('steam_deals', True):
            sources_text.append("✅ Steam İndirimleri")
        else:
            sources_text.append("❌ Steam İndirimleri")
            
        embed.add_field(name="İzlenen Kaynaklar", value="\n".join(sources_text), inline=False)
        
        # Webhook veya kanal bilgisi
        if self.config.get('webhook_url'):
            embed.add_field(name="Webhook", value="`✅ Ayarlanmış`", inline=True)
        else:
            embed.add_field(name="Webhook", value="`❌ Ayarlanmamış`", inline=True)
            
        if self.config.get('news_channel_id'):
            channel = self.bot.get_channel(self.config['news_channel_id'])
            channel_name = channel.mention if channel else f"(ID: {self.config['news_channel_id']})"
            embed.add_field(name="Bildirim Kanalı", value=channel_name, inline=True)
        else:
            embed.add_field(name="Bildirim Kanalı", value="`❌ Ayarlanmamış`", inline=True)
        
        embed.add_field(
            name="Komutlar",
            value=(
                "`!oyunhaber durum` - Haberleri açar/kapatır\n"
                "`!oyunhaber aralık <dakika>` - Kontrol sıklığını ayarlar\n"
                "`!oyunhaber indirim <yüzde>` - Minimum indirim oranını ayarlar\n"
                "`!oyunhaber kanal <#kanal>` - Bildirim kanalını ayarlar\n"
                "`!oyunhaber test` - Test mesajı gönderir\n"
                "`!oyunhaber kaynak <epic/steam> <aç/kapa>` - Haber kaynaklarını yönet\n"
                "`!oyunhaber rol <@rol>` - Etiketlenecek rolü ayarlar"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @game_news.command(name="durum")
    @commands.has_permissions(manage_guild=True)
    async def toggle_status(self, ctx):
        """Oyun haberlerini açıp kapatır"""
        self.config['enabled'] = not self.config.get('enabled', True)
        self.save_config()
        
        status = "✅ aktif" if self.config['enabled'] else "❌ devre dışı"
        await ctx.send(f"Oyun haberleri webhook'u {status} olarak ayarlandı.")
        
        if self.config['enabled']:
            # Etkinleştirildiyse, zamanlamayı yeniden başlat
            if self.check_news.is_running():
                self.check_news.restart()
            else:
                self.check_news.start()
        elif self.check_news.is_running():
            # Devre dışı bırakıldıysa, zamanlamayı durdur
            self.check_news.cancel()
    
    @game_news.command(name="aralık", aliases=["aralik"])
    @commands.has_permissions(manage_guild=True)
    async def set_interval(self, ctx, minutes: int):
        """Kontrol aralığını ayarlar"""
        if minutes < 15:
            return await ctx.send("⚠️ En düşük kontrol aralığı 15 dakika olmalıdır.")
            
        self.config['check_interval_minutes'] = minutes
        self.save_config()
        
        # Zamanlamayı güncelle
        if self.check_news.is_running():
            self.check_news.change_interval(minutes=minutes)
        
        await ctx.send(f"✅ Oyun haberleri kontrol aralığı **{minutes} dakika** olarak ayarlandı.")
    
    @game_news.command(name="indirim")
    @commands.has_permissions(manage_guild=True)
    async def set_discount(self, ctx, percent: int):
        """Minimum indirim yüzdesini ayarlar"""
        if percent < 1 or percent > 100:
            return await ctx.send("⚠️ İndirim yüzdesi 1-100 arasında olmalıdır.")
            
        self.config['min_discount_percent'] = percent
        self.save_config()
        
        await ctx.send(f"✅ Steam indirimleri için minimum indirim oranı **%{percent}** olarak ayarlandı.")
    
    @game_news.command(name="kanal")
    @commands.has_permissions(manage_guild=True)
    async def set_channel(self, ctx, channel: discord.TextChannel = None):
        """Bildirim kanalını ayarlar"""
        if channel:
            self.config['news_channel_id'] = channel.id
            await ctx.send(f"✅ Oyun haberleri bildirim kanalı {channel.mention} olarak ayarlandı.")
        else:
            self.config['news_channel_id'] = None
            await ctx.send("❌ Oyun haberleri bildirim kanalı kaldırıldı. Webhook kullanılacak.")
            
        self.save_config()
    
    @game_news.command(name="kaynak")
    @commands.has_permissions(manage_guild=True)
    async def toggle_source(self, ctx, source_type: str, status: str):
        """Haber kaynaklarını açar/kapatır"""
        source_map = {
            "epic": "epic_games",
            "steam": "steam_deals"
        }
        
        status_map = {
            "aç": True,
            "ac": True,
            "on": True,
            "aktif": True,
            "kapa": False,
            "kapat": False,
            "off": False,
            "devre": False
        }
        
        if source_type.lower() not in source_map:
            return await ctx.send("⚠️ Geçersiz kaynak türü! Kullanılabilir değerler: `epic`, `steam`")
            
        if status.lower() not in status_map:
            return await ctx.send("⚠️ Geçersiz durum! Kullanılabilir değerler: `aç` veya `kapa`")
            
        source_key = source_map[source_type.lower()]
        new_status = status_map[status.lower()]
        
        if 'news_sources' not in self.config:
            self.config['news_sources'] = {}
            
        self.config['news_sources'][source_key] = new_status
        self.save_config()
        
        source_display = {
            "epic_games": "Epic Games Ücretsiz Oyunlar",
            "steam_deals": "Steam İndirimleri"
        }
        
        status_text = "✅ açık" if new_status else "❌ kapalı"
        await ctx.send(f"{source_display[source_key]} kaynağı {status_text} olarak ayarlandı.")
    
    @game_news.command(name="test")
    @commands.has_permissions(manage_guild=True)
    async def test_webhook(self, ctx):
        """Test mesajı gönderir"""
        # Epic Games test
        epic_test = {
            "title": "Test Oyunu",
            "description": "Bu bir Epic Games ücretsiz oyun test mesajıdır.",
            "image": "https://cdn2.unrealengine.com/egs-social-social-share-1200x630-128054837.jpg",
            "url": "https://store.epicgames.com",
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "original_price": "₺129.99",
            "id": "test-game-1"
        }
        
        # Steam test
        steam_test = {
            "title": "Test Oyunu 2",
            "discount_percent": 85,
            "sale_price": "19.99",
            "normal_price": "129.99",
            "steam_rating": "Çok Olumlu",
            "steam_rating_count": "12,345",
            "image": "https://cdn.cloudflare.steamstatic.com/steam/apps/1091500/header.jpg",
            "url": "https://store.steampowered.com",
            "deal_id": "test-deal-1"
        }
        
        test_updates = {
            "epic_free": [epic_test],
            "steam_deals": [steam_test]
        }
        
        await ctx.send("🔍 Test webhook mesajları gönderiliyor...")
        await self.send_news_webhook(test_updates)
        await ctx.send("✅ Test webhook mesajları gönderildi!")
    
    @game_news.command(name="rol")
    @commands.has_permissions(manage_guild=True)
    async def set_role(self, ctx, role: discord.Role = None):
        """Bildirim göndermede etiketlenecek rolü ayarlar"""
        if role:
            self.config['ping_role_id'] = role.id
            await ctx.send(f"✅ Oyun haberleri bildirimlerinde {role.mention} rolü etiketlenecek.")
        else:
            self.config['ping_role_id'] = None
            await ctx.send("❌ Oyun haberleri bildirimlerinde rol etiketleme devre dışı bırakıldı.")
            
        self.save_config()

async def setup(bot):
    """Cog'u bota yükler"""
    await bot.add_cog(GameNews(bot))
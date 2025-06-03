import discord
from discord.ext import commands
import aiohttp
import random
import asyncio
from typing import Optional
import logging

class FunCommands(commands.Cog):
    """🎭 Eğlence ve anime etkileşim komutları"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('fun')
        self.session = None
        
        # Anime API endpoint'leri
        self.api_endpoints = {
            # Etkileşim komutları
            "sarıl": "https://nekos.life/api/v2/img/hug",
            "kucakla": "https://nekos.life/api/v2/img/cuddle", 
            "öp": "https://nekos.life/api/v2/img/kiss",
            "tokatlat": "https://nekos.life/api/v2/img/slap",
            "yala": "https://nekos.life/api/v2/img/lick",
            "ısır": "https://nekos.life/api/v2/img/bite",
            "dürt": "https://nekos.life/api/v2/img/poke",
            "okşa": "https://nekos.life/api/v2/img/pat",
            "beşlik-çak": "https://nekos.life/api/v2/img/highfive",
            "yumrukla": "https://nekos.life/api/v2/img/punch",
            "gıdıkla": "https://nekos.life/api/v2/img/tickle",
            "el-tut": "https://nekos.life/api/v2/img/handholding",
            "öldür": "https://nekos.life/api/v2/img/kill",
            "tut": "https://nekos.life/api/v2/img/hold",
            "boop": "https://nekos.life/api/v2/img/boop",
            "selamla": "https://nekos.life/api/v2/img/greet",
            "kokla": "https://nekos.life/api/v2/img/smell",
            
            # Duygusal reaksiyonlar
            "utanç": "https://nekos.life/api/v2/img/blush",
            "ağla": "https://nekos.life/api/v2/img/cry", 
            "dans": "https://nekos.life/api/v2/img/dance",
            "somurt": "https://nekos.life/api/v2/img/pout",
            "omuz-silk": "https://nekos.life/api/v2/img/shrug",
            "uykulu": "https://nekos.life/api/v2/img/sleepy",
            "gülümse": "https://nekos.life/api/v2/img/smile",
            "kibirli": "https://nekos.life/api/v2/img/smug",
            "sallan": "https://nekos.life/api/v2/img/wag",
            "düşün": "https://nekos.life/api/v2/img/thinking",
            "sinirli": "https://nekos.life/api/v2/img/triggered",
            "mutlu": "https://nekos.life/api/v2/img/happy",
            "sırıt": "https://nekos.life/api/v2/img/grin"
        }
          # Waifu.pics API endpoint'leri (güncel ve çalışan endpoint'ler)
        self.waifu_endpoints = {
            "sarıl": "https://api.waifu.pics/sfw/hug",
            "kucakla": "https://api.waifu.pics/sfw/cuddle",
            "öp": "https://api.waifu.pics/sfw/kiss",
            "tokatlat": "https://api.waifu.pics/sfw/slap",
            "yala": "https://api.waifu.pics/sfw/lick",
            "ısır": "https://api.waifu.pics/sfw/bite",
            "dürt": "https://api.waifu.pics/sfw/poke",
            "okşa": "https://api.waifu.pics/sfw/pat",
            "beşlik-çak": "https://api.waifu.pics/sfw/highfive",
            "yumrukla": "https://api.waifu.pics/sfw/kick",  # punch doesn't exist, use kick
            "gıdıkla": "https://api.waifu.pics/sfw/glomp",  # tickle doesn't exist, use glomp
            "el-tut": "https://api.waifu.pics/sfw/handhold",
            "öldür": "https://api.waifu.pics/sfw/kill",
            "tut": "https://api.waifu.pics/sfw/glomp",  # hold doesn't exist, use glomp
            "boop": "https://api.waifu.pics/sfw/poke",  # boop doesn't exist, use poke
            "elle-selamla": "https://api.waifu.pics/sfw/wave",
            "utanç": "https://api.waifu.pics/sfw/blush",
            "ağla": "https://api.waifu.pics/sfw/cry",
            "dans": "https://api.waifu.pics/sfw/dance",
            "somurt": "https://api.waifu.pics/sfw/cry",  # pout doesn't exist, use cry
            "uykulu": "https://api.waifu.pics/sfw/nom",  # sleepy doesn't exist, use nom (close)
            "gülümse": "https://api.waifu.pics/sfw/smile",
            "kibirli": "https://api.waifu.pics/sfw/smug",
            "sallan": "https://api.waifu.pics/sfw/dance",  # wag doesn't exist, use dance
            "düşün": "https://api.waifu.pics/sfw/nom",  # think doesn't exist, use nom
            "sinirli": "https://api.waifu.pics/sfw/bonk",  # angry doesn't exist, use bonk
            "mutlu": "https://api.waifu.pics/sfw/happy",
            "sırıt": "https://api.waifu.pics/sfw/smile",  # grin doesn't exist, use smile
            "kokla": "https://api.waifu.pics/sfw/nom"  # smell doesn't exist, use nom
        }
        
        # waifu.im API endpointleri (yedek)
        self.waifuim_endpoints = {
            "düşün": "https://api.waifu.im/sfw/think/",
            "sinirli": "https://api.waifu.im/sfw/angry/",
            "sırıt": "https://api.waifu.im/sfw/smile/",
            "sallan": "https://api.waifu.im/sfw/dance/",
            "uykulu": "https://api.waifu.im/sfw/sleep/",
            "omuz-silk": "https://api.waifu.im/sfw/shrug/",
            "somurt": "https://api.waifu.im/sfw/pout/",
            "boop": "https://api.waifu.im/sfw/boop/",
            "tut": "https://api.waifu.im/sfw/hold/",
            "yumrukla": "https://api.waifu.im/sfw/punch/",
            "selamla": "https://api.waifu.im/sfw/wave/",
            "kokla": "https://api.waifu.im/sfw/smell/"
        }
        
        # Emoji haritası
        self.emoji_map = {
            "sarıl": "🤗", "kucakla": "🥰", "öp": "😘", "tokatlat": "👋",
            "yala": "👅", "ısır": "😈", "dürt": "👉", "okşa": "😊",
            "elle-selamla": "👋", "beşlik-çak": "🙏", "yumrukla": "👊",
            "gıdıkla": "😄", "el-tut": "🤝", "öldür": "💀", "tut": "🤗",
            "boop": "👆", "selamla": "👋", "utanç": "😊", "ağla": "😭",
            "dans": "💃", "somurt": "😤", "omuz-silk": "🤷", "uykulu": "😴",
            "gülümse": "😊", "kibirli": "😏", "sallan": "🐕", "düşün": "🤔",
            "sinirli": "😡", "mutlu": "😊", "sırıt": "😁", "kokla": "👃"
        }
        
        # Türkçe mesaj şablonları
        self.action_messages = {
            "sarıl": [
                "{author} {target}'e sıcak bir sarılma veriyor! 🤗",
                "{author} {target}'i sımsıkı sarılıyor! ❤️",
                "{author} {target}'e sevgi dolu bir kucaklama yapıyor! 💕"
            ],
            "kucakla": [
                "{author} {target}'i kucaklıyor! 🥰",
                "{author} {target}'e sevgi dolu kucaklaşma yapıyor! 💖",
                "{author} {target}'i yumuşakça kucaklıyor! ✨"
            ],
            "öp": [
                "{author} {target}'i öpüyor! 😘",
                "{author} {target}'e tatlı bir öpücük veriyor! 💋",
                "{author} {target}'i sevgiyle öpüyor! ❤️"
            ],
            "tokatlat": [
                "{author} {target}'e tokat atıyor! 👋",
                "{author} {target}'i tokatlıyor! Ayyy! 😵",
                "{author} {target}'e sert bir tokat indiriyor! 💥"
            ],
            "yala": [
                "{author} {target}'i yalıyor... 👅",
                "{author} {target}'e yaramaz bir şekilde yalıyor! 😜",
                "{author} {target}'i şaşırtıcı bir şekilde yalıyor! 🤪"
            ],
            "ısır": [
                "{author} {target}'i ısırıyor! 😈",
                "{author} {target}'e yaramaz bir ısırık atıyor! 🦷",
                "{author} {target}'i oyuncakça ısırıyor! 😋"
            ],
            "dürt": [
                "{author} {target}'i dürüyor! 👉",
                "{author} {target}'e dikkat çekmek için dürüyor! 👆",
                "{author} {target}'i nazikçe dürüyor! ✋"
            ],
            "okşa": [
                "{author} {target}'in başını okşuyor! 😊",
                "{author} {target}'i sevgiyle okşuyor! 🥰",
                "{author} {target}'e yumuşak okşamalar yapıyor! ✨"
            ],
            "elle-selamla": [
                "{author} {target}'e el sallıyor! 👋",
                "{author} {target}'i selamlıyor! 🙋‍♀️",
                "{author} {target}'e dostça el sallıyor! 😊"
            ],
            "beşlik-çak": [
                "{author} {target} ile beşlik çakıyor! 🙏",
                "{author} {target}'e harika bir beşlik çakıyor! ✋",
                "{author} {target} ile başarı beşliği yapıyor! 🎉"
            ],
            "yumrukla": [
                "{author} {target}'i yumrukluyor! 👊",
                "{author} {target}'e güçlü bir yumruk atıyor! 💥",
                "{author} {target}'i dövüyor! Ouch! 😵"
            ],
            "gıdıkla": [
                "{author} {target}'i gıdıklıyor! 😄",
                "{author} {target}'e gıdıklama saldırısı yapıyor! 🤣",
                "{author} {target}'i gıdıklayarak güldürüyor! 😂"
            ],
            "el-tut": [
                "{author} {target}'in elini tutuyor! 🤝",
                "{author} {target} ile el ele tutuşuyor! 💕",
                "{author} {target}'in elini sevgiyle kavruyor! ❤️"
            ],
            "öldür": [
                "{author} {target}'i öldürüyor! 💀",
                "{author} {target}'e ölümcül saldırı yapıyor! ⚔️",
                "{author} {target}'i yok ediyor! 💥"
            ],
            "tut": [
                "{author} {target}'i tutuyor! 🤗",
                "{author} {target}'i koruyucu şekilde tutuyor! 🛡️",
                "{author} {target}'i sımsıkı tutuyor! 💪"
            ],
            "boop": [
                "{author} {target}'in burnunu dürüyor! 👆",
                "{author} {target}'e tatlı bir boop yapıyor! 😊",
                "{author} {target}'in burnunu oyuncakça dokunuyor! ✨"
            ],
            "selamla": [
                "{author} {target}'i selamlıyor! 👋",
                "{author} {target}'e sıcak bir selamlama yapıyor! 😊",
                "{author} {target} ile tanışıyor! 🤝"
            ],
            "kokla": [
                "{author} {target}'i kokluyor! 👃",
                "{author} {target}'in kokusunu içine çekiyor! 😳",
                "{author} {target}'i merakla kokluyor! 🫧"
            ]
        }
        
        # Duygusal reaksiyonlar için mesajlar
        self.emotion_messages = {
            "utanç": [
                "{author} utanıyor! 😊",
                "{author} kızarıyor ve utanıyor! 🙈",
                "{author} mahcup oluyor! ☺️"
            ],
            "ağla": [
                "{author} ağlıyor! 😭",
                "{author} üzgün ve ağlamaklı! 💧",
                "{author} gözyaşlarına boğuluyor! 😢"
            ],
            "dans": [
                "{author} dans ediyor! 💃",
                "{author} harika dans hareketleri yapıyor! 🕺",
                "{author} müzikle birlikte dans ediyor! 🎵"
            ],
            "somurt": [
                "{author} somurtuyor! 😤",
                "{author} keyfi kaçık ve somurt! 😒",
                "{author} mızmızlanıyor! 😾"
            ],
            "omuz-silk": [
                "{author} omuz silkiyor! 🤷",
                "{author} bilmiyor ve omuz silkiyor! 🤷‍♀️",
                "{author} aldırışsızca omuz silkiyor! 😐"
            ],
            "uykulu": [
                "{author} çok uykulu! 😴",
                "{author} gözleri kapanıyor! 💤",
                "{author} uyumak istiyor! 🛌"
            ],
            "gülümse": [
                "{author} gülümsüyor! 😊",
                "{author} mutlu bir gülümseme yapıyor! 😄",
                "{author} tatlı tatlı gülümsüyor! ☺️"
            ],
            "kibirli": [
                "{author} kibirli gülümsüyor! 😏",
                "{author} üstün bir ifadeyle gülümsüyor! 😌",
                "{author} kendinden emin gülümsüyor! 😎"
            ],
            "sallan": [
                "{author} kuyruk sallıyor! 🐕",
                "{author} mutlulukla sallanıyor! 🐾",
                "{author} heyecanla sallanıyor! 🎉"
            ],
            "düşün": [
                "{author} düşünüyor! 🤔",
                "{author} derin düşüncelerde! 💭",
                "{author} kafa yoruyor! 🧠"
            ],
            "sinirli": [
                "{author} çok sinirli! 😡",
                "{author} öfkeyle kaynıyor! 🔥",
                "{author} sinirden deliye dönüyor! 😤"
            ],            "mutlu": [
                "{author} çok mutlu! 😊",
                "{author} sevinçle dolup taşıyor! 🎉",
                "{author} mutluluktan uçuyor! ✨"
            ],
            "sırıt": [
                "{author} sırıtıyor! 😁",
                "{author} kocaman sırıtıyor! 😃",
                "{author} şımarık sırıtıyor! 😆"
            ]
        }

        # Tenor API ayarları (public key ile, limitsiz arama için kendi key'inizi ekleyin)
        self.tenor_api_key = "LIVDSRZULELA"  # Tenor'ın public demo anahtarı
        self.tenor_limit = 10

    async def get_session(self):
        """HTTP session'ı al veya oluştur"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def get_fallback_gif(self, action: str) -> str:
        """Anime dışı (meme, oyun, genel) GIF için Tenor ve Giphy'den arama yapar."""
        session = await self.get_session()
        # Komutlara göre arama anahtarları
        fallback_terms = {
            "sırıt": ["grin meme gif", "grin game gif", "grinning gif"],
            "sinirli": ["angry meme gif", "angry game gif", "rage gif"],
            "düşün": ["thinking meme gif", "thinking game gif", "think gif"],
            "sallan": ["wag meme gif", "wagging tail gif", "shake gif"],
            "omuz-silk": ["shrug meme gif", "shrug gif", "idk gif"],
            "uykulu": ["sleepy meme gif", "sleep gif", "tired gif"],
            "somurt": ["pout meme gif", "pouting gif", "sad face gif"],
            "kokla": ["smell meme gif", "sniff gif", "smelling gif"],
            "boop": ["boop meme gif", "boop gif", "nose boop gif"],
            "tut": ["hold meme gif", "hug gif", "grab gif"],
            "yumrukla": ["punch meme gif", "punch game gif", "fight gif"],
            "elle-selamla": ["wave meme gif", "wave hello gif", "waving gif"]
        }
        terms = fallback_terms.get(action, [f"{action} meme gif", f"{action} gif"])
        # Önce Tenor, sonra Giphy
        for term in terms:
            # Tenor
            try:
                tenor_url = f"https://tenor.googleapis.com/v2/search?q={term}&key={self.tenor_api_key}&limit={self.tenor_limit}&media_filter=gif"
                async with session.get(tenor_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results")
                        if results:
                            gif_url = results[0]["media_formats"]["gif"]["url"]
                            self.logger.info(f"[🪬] Tenor fallback: {gif_url}")
                            return gif_url
            except Exception as e:
                self.logger.error(f"[🪬] Tenor fallback hata: {e}")
            # Giphy (public beta key)
            try:
                giphy_url = f"https://api.giphy.com/v1/gifs/search?q={term}&api_key=dc6zaTOxFJmzC&limit=10"
                async with session.get(giphy_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("data")
                        if results:
                            gif_url = results[0]["images"]["original"]["url"]
                            self.logger.info(f"[🪬] Giphy fallback: {gif_url}")
                            return gif_url
            except Exception as e:
                self.logger.error(f"[🪬] Giphy fallback hata: {e}")
        return None

    async def get_anime_gif(self, action: str) -> str:
        """Anime gif URL'si al (nekos.life, waifu.im, waifu.pics, Tenor, fallback)"""
        # 1. nekos.life
        nekos_endpoint = self.api_endpoints.get(action)
        if nekos_endpoint:
            try:
                session = await self.get_session()
                async with session.get(nekos_endpoint, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        gif_url = data.get('url')
                        if gif_url:
                            self.logger.info(f"[🪬] nekos.life: {gif_url}")
                            return gif_url
                        else:
                            self.logger.error(f"[🪬] nekos.life yanıtında url yok: {data}")
            except Exception as e:
                self.logger.error(f"[🪬] nekos.life hata: {e}")
        # 2. waifu.im
        waifuim_endpoint = self.waifuim_endpoints.get(action)
        if waifuim_endpoint:
            try:
                session = await self.get_session()
                async with session.get(waifuim_endpoint, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict) and 'images' in data and data['images']:
                            gif_url = data['images'][0].get('url')
                            if gif_url:
                                self.logger.info(f"[🪬] waifu.im: {gif_url}")
                                return gif_url
                        self.logger.error(f"[🪬] waifu.im yanıtında url yok: {data}")
            except Exception as e:
                self.logger.error(f"[🪬] waifu.im hata: {e}")
        # 3. waifu.pics
        waifu_endpoint = self.waifu_endpoints.get(action)
        if waifu_endpoint:
            try:
                session = await self.get_session()
                async with session.get(waifu_endpoint, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        gif_url = data.get('url') or data.get('link')
                        if gif_url:
                            self.logger.info(f"[🪬] waifu.pics: {gif_url}")
                            return gif_url
                        else:
                            self.logger.error(f"[🪬] waifu.pics yanıtında url yok: {data}")
            except Exception as e:
                self.logger.error(f"[🪬] waifu.pics hata: {e}")        # 4. Tenor anime (her zaman en son)
        try:
            session = await self.get_session()
            search_term = action.replace("-", " ")
            tenor_url = f"https://tenor.googleapis.com/v2/search?q=anime+{search_term}&key={self.tenor_api_key}&limit={self.tenor_limit}&media_filter=gif"
            async with session.get(tenor_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results")
                    if results:
                        gif_url = results[0]["media_formats"]["gif"]["url"]
                        self.logger.info(f"[🪬] Tenor anime: {gif_url}")
                        return gif_url
                    else:
                        self.logger.error(f"[🪬] Tenor anime sonuç yok: {data}")
        except Exception as e:
            self.logger.error(f"[🪬] Tenor anime hata: {e}")
            
        # 5. General fallback (meme/game GIFs)
        self.logger.warning(f"[🪬] Hiçbir anime API'dan gif alınamadı: {action}, fallback deneniyor...")
        fallback_gif = await self.get_fallback_gif(action)
        if fallback_gif:
            return fallback_gif
            
        # 6. Son çare: default error gif
        self.logger.error(f"[🪬] Hiçbir API'dan gif alınamadı: {action}")
        return None

    async def create_action_embed(self, ctx, action: str, target: Optional[discord.Member] = None) -> discord.Embed:
        """Aksiyon embed'i oluştur"""
        author = ctx.author
        
        # Gif URL'si al
        gif_url = await self.get_anime_gif(action)
        
        # Mesaj seç
        if target and action in self.action_messages:
            # Etkileşim komutu
            message = random.choice(self.action_messages[action]).format(
                author=author.display_name,
                target=target.display_name
            )
            title = f"{self.emoji_map.get(action, '✨')} {action.title()}"
        elif action in self.emotion_messages:
            # Duygusal reaksiyon
            message = random.choice(self.emotion_messages[action]).format(
                author=author.display_name
            )
            title = f"{self.emoji_map.get(action, '✨')} {action.title()}"
        else:
            message = f"{author.display_name} {action} yapıyor!"
            title = f"✨ {action.title()}"
        
        # Embed oluştur
        embed = discord.Embed(
            title=title,
            description=message,
            color=0xFF69B4
        )
        
        if gif_url:
            embed.set_image(url=gif_url)
        else:
            embed.add_field(
                name="⚠️ Gif Yüklenemedi", 
                value="Anime gif'i şu anda yüklenemiyor, ama hayal gücünüzü kullanabilirsiniz! ✨",
                inline=False
            )
        
        embed.set_footer(
            text=f"{ctx.author.display_name} tarafından kullanıldı",
            icon_url=ctx.author.display_avatar.url
        )
        
        return embed

    # ================================
    # EİLEŞİM KOMUTLARI
    # ================================
    
    @commands.command(name='sarıl', aliases=['hug', 'saril'])
    async def hug(self, ctx, member: Optional[discord.Member] = None):
        """🤗 Birine sarılır"""
        if member is None:
            await ctx.send("❌ Kime sarılmak istiyorsun? Bir kişi etiketle!")
            return
            
        if member == ctx.author:
            await ctx.send("🤗 Kendine sarılıyorsun... Aww! 💕")
            return
            
        embed = await self.create_action_embed(ctx, "sarıl", member)
        await ctx.send(embed=embed)

    @commands.command(name='kucakla', aliases=['cuddle'])
    async def cuddle(self, ctx, member: Optional[discord.Member] = None):
        """🥰 Birine kucaklar"""
        if member is None:
            await ctx.send("❌ Kimi kucaklamak istiyorsun?")
            return
            
        if member == ctx.author:
            await ctx.send("🥰 Kendini kucaklıyorsun! Çok tatlı! 💖")
            return
            
        embed = await self.create_action_embed(ctx, "kucakla", member)
        await ctx.send(embed=embed)

    @commands.command(name='öp', aliases=['kiss', 'op'])
    async def kiss(self, ctx, member: Optional[discord.Member] = None):
        """😘 Birine öper"""
        if member is None:
            await ctx.send("❌ Kimi öpmek istiyorsun?")
            return
            
        if member == ctx.author:
            await ctx.send("😘 Kendini öpüyorsun! Narcissist! 😂")
            return
            
        embed = await self.create_action_embed(ctx, "öp", member)
        await ctx.send(embed=embed)

    @commands.command(name='tokatlat', aliases=['slap', 'tokat'])
    async def slap(self, ctx, member: Optional[discord.Member] = None):
        """👋 Birine tokat atar"""
        if member is None:
            await ctx.send("❌ Kime tokat atacaksın?")
            return
            
        if member == ctx.author:
            await ctx.send("👋 Kendine tokat atıyorsun! Masochist! 😵")
            return
            
        embed = await self.create_action_embed(ctx, "tokatlat", member)
        await ctx.send(embed=embed)

    @commands.command(name='yala', aliases=['lick'])
    async def lick(self, ctx, member: Optional[discord.Member] = None):
        """👅 Birini yalar"""
        if member is None:
            await ctx.send("❌ Kimi yalamak istiyorsun? 😏")
            return
            
        if member == ctx.author:
            await ctx.send("👅 Kendini yalıyorsun! Çok garip! 🤪")
            return
            
        embed = await self.create_action_embed(ctx, "yala", member)
        await ctx.send(embed=embed)

    @commands.command(name='ısır', aliases=['bite', 'isir'])
    async def bite(self, ctx, member: Optional[discord.Member] = None):
        """😈 Birini ısırır"""
        if member is None:
            await ctx.send("❌ Kimi ısırmak istiyorsun?")
            return
            
        if member == ctx.author:
            await ctx.send("😈 Kendini ısırıyorsun! Ouch! 🦷")
            return
            
        embed = await self.create_action_embed(ctx, "ısır", member)
        await ctx.send(embed=embed)

    @commands.command(name='dürt', aliases=['poke', 'durt'])
    async def poke(self, ctx, member: Optional[discord.Member] = None):
        """👉 Birini dürtür"""
        if member is None:
            await ctx.send("❌ Kimi dürtmek istiyorsun?")
            return
            
        if member == ctx.author:
            await ctx.send("👉 Kendini dürtüyorsun! Tuhaf! 😅")
            return
            
        embed = await self.create_action_embed(ctx, "dürt", member)
        await ctx.send(embed=embed)

    @commands.command(name='okşa', aliases=['pat', 'oksa'])
    async def pat(self, ctx, member: Optional[discord.Member] = None):
        """😊 Birinin başını okşar"""
        if member is None:
            await ctx.send("❌ Kimin başını okşamak istiyorsun?")
            return
            
        if member == ctx.author:
            await ctx.send("😊 Kendi başını okşuyorsun! Çok tatlı! 🥰")
            return
            
        embed = await self.create_action_embed(ctx, "okşa", member)
        await ctx.send(embed=embed)

    @commands.command(name='elle-selamla', aliases=['wave', 'selamla'])
    async def wave(self, ctx, member: Optional[discord.Member] = None):
        """👋 Birine el sallar"""
        if member is None:
            # Genel selamlama
            embed = await self.create_action_embed(ctx, "elle-selamla")
            await ctx.send(embed=embed)
            return
            
        if member == ctx.author:
            await ctx.send("👋 Kendine el sallıyorsun! Merhaba sen! 😄")
            return
            
        embed = await self.create_action_embed(ctx, "elle-selamla", member)
        await ctx.send(embed=embed)

    @commands.command(name='beşlik-çak', aliases=['highfive', 'beslik'])
    async def highfive(self, ctx, member: Optional[discord.Member] = None):
        """🙏 Biriyle beşlik çakar"""
        if member is None:
            await ctx.send("❌ Kiminle beşlik çakmak istiyorsun?")
            return
            
        if member == ctx.author:
            await ctx.send("🙏 Kendinle beşlik çakıyorsun! Forever alone! 😂")
            return
            
        embed = await self.create_action_embed(ctx, "beşlik-çak", member)
        await ctx.send(embed=embed)

    @commands.command(name='yumrukla', aliases=['punch'])
    async def punch(self, ctx, member: Optional[discord.Member] = None):
        """👊 Birine yumruk atar"""
        if member is None:
            await ctx.send("❌ Kime yumruk atacaksın?")
            return
            
        if member == ctx.author:
            await ctx.send("👊 Kendini yumrukluyorsun! Self-harm! 😵")
            return
            
        embed = await self.create_action_embed(ctx, "yumrukla", member)
        await ctx.send(embed=embed)

    @commands.command(name='gıdıkla', aliases=['tickle', 'gidikla'])
    async def tickle(self, ctx, member: Optional[discord.Member] = None):
        """😄 Birini gıdıklar"""
        if member is None:
            await ctx.send("❌ Kimi gıdıklamak istiyorsun?")
            return
            
        if member == ctx.author:
            await ctx.send("😄 Kendini gıdıklıyorsun! Hihihi! 🤣")
            return
            
        embed = await self.create_action_embed(ctx, "gıdıkla", member)
        await ctx.send(embed=embed)

    @commands.command(name='el-tut', aliases=['handholding', 'eltut'])
    async def handholding(self, ctx, member: Optional[discord.Member] = None):
        """🤝 Birinin elini tutar"""
        if member is None:
            await ctx.send("❌ Kimin elini tutmak istiyorsun?")
            return
            
        if member == ctx.author:
            await ctx.send("🤝 Kendi elini tutuyorsun! Çok romantik! 😂")
            return
            
        embed = await self.create_action_embed(ctx, "el-tut", member)
        await ctx.send(embed=embed)

    @commands.command(name='öldür', aliases=['kill', 'oldur'])
    async def kill(self, ctx, member: Optional[discord.Member] = None):
        """💀 Birini öldürür (oyuncakça)"""
        if member is None:
            await ctx.send("❌ Kimi öldürmek istiyorsun?")
            return
            
        if member == ctx.author:
            await ctx.send("💀 Kendini öldürüyorsun! Suicide! 😵")
            return
            
        embed = await self.create_action_embed(ctx, "öldür", member)
        await ctx.send(embed=embed)

    @commands.command(name='tut', aliases=['hold'])
    async def hold(self, ctx, member: Optional[discord.Member] = None):
        """🤗 Birini tutar"""
        if member is None:
            await ctx.send("❌ Kimi tutmak istiyorsun?")
            return
            
        if member == ctx.author:
            await ctx.send("🤗 Kendini tutuyorsun! Self-hug! 💕")
            return
            
        embed = await self.create_action_embed(ctx, "tut", member)
        await ctx.send(embed=embed)

    @commands.command(name='boop')
    async def boop(self, ctx, member: Optional[discord.Member] = None):
        """👆 Birinin burnunu dürtür"""
        if member is None:
            await ctx.send("❌ Kimin burnunu dürtmek istiyorsun?")
            return
            
        if member == ctx.author:
            await ctx.send("👆 Kendi burnunu dürtüyorsun! Boop! 😊")
            return
            
        embed = await self.create_action_embed(ctx, "boop", member)
        await ctx.send(embed=embed)

    @commands.command(name='kokla', aliases=['smell'])
    async def smell(self, ctx, member: Optional[discord.Member] = None):
        """👃 Birini koklarsın"""
        if member is None:
            await ctx.send("❌ Kimi koklamak istiyorsun?")
            return
        if member == ctx.author:
            await ctx.send("👃 Kendini kokluyorsun! Garip ama olabilir! 🫧")
            return
        embed = await self.create_action_embed(ctx, "kokla", member)
        await ctx.send(embed=embed)

    # ================================
    # DUYGUSAL REAKSİYONLAR
    # ================================

    @commands.command(name='utanç', aliases=['blush', 'utan'])
    async def blush(self, ctx):
        """😊 Utanırsın"""
        embed = await self.create_action_embed(ctx, "utanç")
        await ctx.send(embed=embed)

    @commands.command(name='ağla', aliases=['cry', 'agla'])
    async def cry(self, ctx):
        """😭 Ağlarsın"""
        embed = await self.create_action_embed(ctx, "ağla")
        await ctx.send(embed=embed)

    @commands.command(name='dans', aliases=['dance'])
    async def dance(self, ctx):
        """💃 Dans edersin"""
        embed = await self.create_action_embed(ctx, "dans")
        await ctx.send(embed=embed)

    @commands.command(name='somurt', aliases=['pout'])
    async def pout(self, ctx):
        """😤 Somurursun"""
        embed = await self.create_action_embed(ctx, "somurt")
        await ctx.send(embed=embed)

    @commands.command(name='omuz-silk', aliases=['shrug', 'omuzsilk'])
    async def shrug(self, ctx):
        """🤷 Omuz silkersin"""
        embed = await self.create_action_embed(ctx, "omuz-silk")
        await ctx.send(embed=embed)

    @commands.command(name='uykulu', aliases=['sleepy'])
    async def sleepy(self, ctx):
        """😴 Uykulu olursun"""
        embed = await self.create_action_embed(ctx, "uykulu")
        await ctx.send(embed=embed)

    @commands.command(name='gülümse', aliases=['smile', 'gulumse'])
    async def smile(self, ctx):
        """😊 Gülümsersin"""
        embed = await self.create_action_embed(ctx, "gülümse")
        await ctx.send(embed=embed)

    @commands.command(name='kibirli', aliases=['smug'])
    async def smug(self, ctx):
        """😏 Kibirli gülümsersin"""
        embed = await self.create_action_embed(ctx, "kibirli")
        await ctx.send(embed=embed)

    @commands.command(name='sallan', aliases=['wag'])
    async def wag(self, ctx):
        """🐕 Kuyruk sallarsın"""
        embed = await self.create_action_embed(ctx, "sallan")
        await ctx.send(embed=embed)

    @commands.command(name='düşün', aliases=['thinking', 'dusun'])
    async def thinking(self, ctx):
        """🤔 Düşünürsün"""
        embed = await self.create_action_embed(ctx, "düşün")
        await ctx.send(embed=embed)

    @commands.command(name='sinirli', aliases=['triggered', 'angry'])
    async def triggered(self, ctx):
        """😡 Sinirlenirsin"""
        embed = await self.create_action_embed(ctx, "sinirli")
        await ctx.send(embed=embed)

    @commands.command(name='mutlu', aliases=['happy'])
    async def happy(self, ctx):
        """😊 Mutlu olursun"""
        embed = await self.create_action_embed(ctx, "mutlu")
        await ctx.send(embed=embed)

    @commands.command(name='sırıt', aliases=['grin', 'sirit'])
    async def grin(self, ctx):
        """😁 Sırıtırsın"""
        embed = await self.create_action_embed(ctx, "sırıt")
        await ctx.send(embed=embed)

    # ================================
    # YARDIMCİ KOMUTLAR
    # ================================

    @commands.command(name='eğlence-help', aliases=['fun-help', 'eglence-help'])
    async def fun_help(self, ctx):
        """🎭 Eğlence komutları yardımı"""
        
        embed = discord.Embed(
            title="🎭 Eğlence Komutları Yardımı",
            description="Anime gif'li etkileşim ve duygusal reaksiyon komutları!",
            color=0xFF69B4
        )
        
        # Etkileşim komutları
        interaction_commands = """
        `!sarıl @kişi` - Birine sarılır 🤗
        `!kucakla @kişi` - Birine kucaklar 🥰
        `!öp @kişi` - Birine öper 😘
        `!tokatlat @kişi` - Birine tokat atar 👋
        `!yala @kişi` - Birini yalar 👅
        `!ısır @kişi` - Birini ısırır 😈
        `!dürt @kişi` - Birini dürtür 👉
        `!okşa @kişi` - Birinin başını okşar 😊
        `!beşlik-çak @kişi` - Biriyle beşlik çakar 🙏
        `!yumrukla @kişi` - Birine yumruk atar 👊
        `!gıdıkla @kişi` - Birini gıdıklar 😄
        `!el-tut @kişi` - Birinin elini tutar 🤝
        `!boop @kişi` - Birinin burnunu dürtür 👆
        `!kokla @kişi` - Birini koklar 👃
        """
        
        emotion_commands = """
        `!utanç` - Utanırsın 😊
        `!ağla` - Ağlarsın 😭
        `!dans` - Dans edersin 💃
        `!somurt` - Somurursun 😤
        `!omuz-silk` - Omuz silkersin 🤷
        `!uykulu` - Uykulu olursun 😴
        `!gülümse` - Gülümsersin 😊
        `!kibirli` - Kibirli gülümsersin 😏
        `!sallan` - Kuyruk sallarsın 🐕
        `!düşün` - Düşünürsün 🤔
        `!sinirli` - Sinirlenirsin 😡
        `!mutlu` - Mutlu olursun 😊
        `!sırıt` - Sırıtırsın 😁
        """
        
        embed.add_field(
            name="👫 Etkileşim Komutları",
            value=interaction_commands,
            inline=False
        )
        
        embed.add_field(
            name="😊 Duygusal Reaksiyonlar",
            value=emotion_commands,
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Not",
                        value="Tüm komutlar anime gif'leri ile birlikte gelir! API bağlantısı yoksa hayal gücünüzü kullanın! ✨",
            inline=False
        )
        
        embed.set_footer(text="Lunaris Eğlence Komutları 🐱")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        """Cog yüklendiğinde"""
        self.logger.info("Eğlence komutları yüklendi!")
        print("[✅] Eğlence komutları yüklendi!")

    def cog_unload(self):
        """Cog kaldırılırken session'ı temizle"""
        if self.session and not self.session.closed:
            # Session'ı asenkron olarak kapatmak için task oluştur
            asyncio.create_task(self.session.close())

async def setup(bot):
    await bot.add_cog(FunCommands(bot))

import discord
from discord.ext import commands
import random
import json
import asyncio
from datetime import datetime
from typing import Optional
import os

class MiniGames(commands.Cog):
    """🎮 Mini oyunlar - Eğlenceli oyunlarla vakit geçirin!"""
    
    def __init__(self, bot):
        self.bot = bot
        self.trivia_file = "data/trivia_questions.json"
        self.game_stats = {}  # Oyuncu istatistikleri
        self.daily_challenges = {}  # Günlük görevler
        
        # Emoji kategorileri
        self.emoji_categories = {
            "🍎": ["elma", "apple", "meyve"],
            "🐶": ["köpek", "dog", "hayvan"],
            "🚗": ["araba", "car", "araç"],
            "⚽": ["futbol", "football", "top"],
            "🏠": ["ev", "house", "home"],
            "🌟": ["yıldız", "star", "ışık"],
            "🎵": ["müzik", "music", "nota"],
            "📱": ["telefon", "phone", "mobil"],
            "☀️": ["güneş", "sun", "ışık"],
            "🌙": ["ay", "moon", "gece"],
            "❤️": ["kalp", "heart", "aşk"],
            "🎂": ["pasta", "cake", "doğum günü"],
            "🌹": ["gül", "rose", "çiçek"],
            "🦋": ["kelebek", "butterfly", "böcek"],
            "🌈": ["gökkuşağı", "rainbow", "renk"]
        }
        
        # Bilmeceler
        self.riddles = [
            {
                "question": "Gündüz uyur, gece kalkar. Bu nedir?",
                "answer": "baykuş",
                "hints": ["Bir kuştur", "Büyük gözleri vardır"]
            },
            {
                "question": "İçinde su olan ama içilmeyen şey nedir?",
                "answer": "deniz",
                "hints": ["Çok büyüktür", "Tuzludur"]
            },
            {
                "question": "Konuşur ama dili yoktur. Bu nedir?",
                "answer": "echo",
                "hints": ["Sesinizi taklit eder", "Dağlarda duyulur"]
            },
            {
                "question": "Bacakları var ama yürüyemez. Bu nedir?",
                "answer": "masa",
                "hints": ["Evde bulunur", "Üzerine bir şeyler konur"]
            },
            {
                "question": "Ne kadar besersen o kadar büyür ama su verirse ölür?",
                "answer": "ateş",
                "hints": ["Sıcaktır", "Yakar"]
            }
        ]
        
        self.load_trivia_questions()
        
    def load_trivia_questions(self):
        """Trivia sorularını yükler"""
        try:
            os.makedirs("data", exist_ok=True)
            with open(self.trivia_file, 'r', encoding='utf-8') as f:
                self.trivia_questions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Varsayılan trivia soruları
            self.trivia_questions = {
                "genel": [
                    {"question": "Türkiye'nin başkenti neresidir?", "answer": "ankara", "options": ["İstanbul", "Ankara", "İzmir", "Bursa"]},
                    {"question": "1 yılda kaç ay vardır?", "answer": "12", "options": ["10", "11", "12", "13"]},
                    {"question": "En büyük gezegen hangisidir?", "answer": "jüpiter", "options": ["Mars", "Venüs", "Jüpiter", "Satürn"]},
                    {"question": "Kaç mevsim vardır?", "answer": "4", "options": ["3", "4", "5", "6"]},
                    {"question": "Dünyanın en büyük okyanusu hangisidir?", "answer": "pasifik", "options": ["Atlantik", "Pasifik", "Hint", "Arktik"]}
                ],
                "tarih": [
                    {"question": "Osmanlı İmparatorluğu ne zaman kuruldu?", "answer": "1299", "options": ["1299", "1453", "1071", "1326"]},
                    {"question": "İstanbul'un fethi hangi yılda gerçekleşti?", "answer": "1453", "options": ["1453", "1299", "1071", "1922"]},
                    {"question": "Türkiye Cumhuriyeti ne zaman kuruldu?", "answer": "1923", "options": ["1920", "1921", "1922", "1923"]}
                ],
                "spor": [
                    {"question": "Futbolda bir takımda kaç oyuncu vardır?", "answer": "11", "options": ["9", "10", "11", "12"]},
                    {"question": "Olimpiyatlar kaç yılda bir düzenlenir?", "answer": "4", "options": ["2", "3", "4", "5"]},
                    {"question": "Basketbolda basket kaç puan eder?", "answer": "2", "options": ["1", "2", "3", "4"]}
                ]
            }
            # Dosyayı oluştur
            with open(self.trivia_file, 'w', encoding='utf-8') as f:
                json.dump(self.trivia_questions, f, ensure_ascii=False, indent=2)

    def update_stats(self, user_id: int, game: str, won: bool = False, score: int = 0, perfect: bool = False):
        """Oyuncu istatistiklerini günceller"""
        if user_id not in self.game_stats:
            self.game_stats[user_id] = {
                "total_games": 0,
                "total_wins": 0,
                "total_score": 0,
                "games": {},
                "achievements": [],
                "daily_progress": {},
                "last_daily_reset": None
            }
        
        stats = self.game_stats[user_id]
        stats["total_games"] += 1
        stats["total_score"] += score
        
        if won:
            stats["total_wins"] += 1
        
        # Oyun bazında istatistikler
        if game not in stats["games"]:
            stats["games"][game] = {"played": 0, "won": 0}
        
        stats["games"][game]["played"] += 1
        if won:
            stats["games"][game]["won"] += 1

    @commands.command(name="tahmin", aliases=["guess"])
    async def number_guess(self, ctx, max_number: int = 100):
        """🔢 Sayı tahmin oyunu"""
        if max_number < 10 or max_number > 1000:
            return await ctx.send("❌ Sayı 10-1000 arasında olmalı!")
        
        target = random.randint(1, max_number)
        attempts = 0
        max_attempts = min(7, max_number // 10 + 3)
        
        embed = discord.Embed(
            title="🔢 Sayı Tahmin Oyunu",
            description=f"1 ile {max_number} arasında bir sayı tuttum!\n"
                       f"**{max_attempts}** tahmin hakkınız var.",
            color=0x3498DB
        )
        embed.set_footer(text="Tahmin etmeye başlayın!")
        await ctx.send(embed=embed)
        
        def check(message):
            return (message.author == ctx.author and 
                   message.channel == ctx.channel and
                   message.content.isdigit())
        
        while attempts < max_attempts:
            try:
                response = await self.bot.wait_for('message', check=check, timeout=30.0)
                guess = int(response.content)
                attempts += 1
                
                if guess == target:
                    # Kazandı
                    points = max(100 - attempts * 10, 10)
                    self.update_stats(ctx.author.id, "tahmin", True, points)
                    
                    embed = discord.Embed(
                        title="🎉 Tebrikler!",
                        description=f"**{target}** sayısını {attempts} tahminde buldunuz!\n"
                                   f"**Kazanılan puan:** +{points} ✨",
                        color=0x00FF00
                    )
                    embed.set_footer(text="Harika tahmin! 🎯")
                    return await ctx.send(embed=embed)
                
                elif guess < target:
                    hint = "📈 Daha büyük bir sayı deneyin!"
                else:
                    hint = "📉 Daha küçük bir sayı deneyin!"
                
                remaining = max_attempts - attempts
                embed = discord.Embed(
                    title="🤔 Tekrar Deneyin",
                    description=f"{hint}\n\n**Kalan hak:** {remaining}",
                    color=0xF39C12
                )
                embed.set_footer(text="Devam edin!")
                await ctx.send(embed=embed)
                
            except asyncio.TimeoutError:
                self.update_stats(ctx.author.id, "tahmin", False)
                embed = discord.Embed(
                    title="⏰ Süre Doldu!",
                    description=f"**Doğru sayı:** {target}",
                    color=0xE74C3C
                )
                embed.set_footer(text="Tekrar deneyin!")
                return await ctx.send(embed=embed)
        
        # Hakkı bitti
        self.update_stats(ctx.author.id, "tahmin", False)
        embed = discord.Embed(
            title="💔 Oyun Bitti!",
            description=f"**{max_attempts}** tahmin hakkınız doldu.\n"
                       f"**Doğru sayı:** {target}",
            color=0xE74C3C
        )
        embed.set_footer(text="Tekrar deneyin!")
        await ctx.send(embed=embed)

    @commands.command(name="trivia", aliases=["bilgi"])
    async def trivia_game(self, ctx, *, category: str = None):
        """❓ Trivia oyunu - bilgi yarışması"""
        try:
            if not hasattr(self, 'trivia_questions') or not self.trivia_questions:
                return await ctx.send("❌ Trivia soruları yüklenemedi!")
            
            # Kategori seçimi
            if category is None:
                categories = list(self.trivia_questions.keys())
                category = random.choice(categories)
            else:
                category = category.lower()
                if category not in self.trivia_questions:
                    available = ", ".join(self.trivia_questions.keys())
                    return await ctx.send(f"❌ Geçersiz kategori! Mevcut kategoriler: {available}")
            
            # Soru seç
            questions = self.trivia_questions[category]
            if not questions:
                return await ctx.send("❌ Bu kategoride soru bulunamadı!")
            
            question_data = random.choice(questions)
            question = question_data["question"]
            correct_answer = question_data["answer"].lower()
            options = question_data["options"]
            
            # Embed oluştur
            embed = discord.Embed(
                title="❓ Trivia Sorusu",
                description=f"**Kategori:** {category.title()}\n\n**{question}**",
                color=0x9B59B6
            )
            
            # Seçenekleri ekle
            options_text = ""
            for i, option in enumerate(options, 1):
                options_text += f"{i}. {option}\n"
            
            embed.add_field(name="📝 Seçenekler:", value=options_text, inline=False)
            embed.set_footer(text="20 saniyeniz var! Seçenek numarasını yazın.")
            await ctx.send(embed=embed)
            
            def check(message):
                return (message.author == ctx.author and 
                       message.channel == ctx.channel and
                       (message.content.isdigit() and 1 <= int(message.content) <= len(options)))
            
            try:
                response = await self.bot.wait_for('message', check=check, timeout=20.0)
                user_choice = int(response.content) - 1
                selected_answer = options[user_choice].lower()
                
                if selected_answer == correct_answer:
                    points = 25
                    self.update_stats(ctx.author.id, "trivia", True, points)
                    
                    embed = discord.Embed(
                        title="✅ Doğru Cevap!",
                        description=f"Tebrikler! **{options[user_choice]}** doğru cevap!\n"
                                   f"**Kazanılan puan:** +{points} ✨",
                        color=0x00FF00
                    )
                    embed.set_footer(text="Zeka ustası! 🧠")
                else:
                    self.update_stats(ctx.author.id, "trivia", False)
                    # Doğru cevabı bul
                    correct_option = None
                    for i, option in enumerate(options):
                        if option.lower() == correct_answer:
                            correct_option = option
                            break
                    
                    embed = discord.Embed(
                        title="❌ Yanlış Cevap!",
                        description=f"**Sizin cevabınız:** {options[user_choice]}\n"
                                   f"**Doğru cevap:** {correct_option}",
                        color=0xE74C3C
                    )
                    embed.set_footer(text="Tekrar deneyin!")
                
                await ctx.send(embed=embed)
                
            except asyncio.TimeoutError:
                self.update_stats(ctx.author.id, "trivia", False)
                # Doğru cevabı bul
                correct_option = None
                for option in options:
                    if option.lower() == correct_answer:
                        correct_option = option
                        break
                
                embed = discord.Embed(
                    title="⏰ Süre Doldu!",
                    description=f"**Doğru cevap:** {correct_option}",
                    color=0xE74C3C
                )
                embed.set_footer(text="Daha hızlı olmalısınız!")
                await ctx.send(embed=embed)
                
        except Exception as e:
            await ctx.send(f"❌ Trivia oyununda bir hata oluştu: {str(e)}")

    @commands.command(name="emoji")
    async def emoji_game(self, ctx):
        """😊 Emoji tahmin oyunu"""
        emoji, possible_answers = random.choice(list(self.emoji_categories.items()))
        correct_answer = possible_answers[0]  # İlk cevap doğru cevap
        
        embed = discord.Embed(
            title="😊 Emoji Tahmin Oyunu",
            description=f"Bu emoji neyi temsil ediyor?\n\n**{emoji}**\n\n"
                       f"⏱️ 15 saniyeniz var!",
            color=0xF39C12
        )
        embed.set_footer(text="Ne olduğunu tahmin edin!")
        await ctx.send(embed=embed)
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel
        
        try:
            response = await self.bot.wait_for('message', check=check, timeout=15.0)
            user_answer = response.content.lower().strip()
            
            if user_answer in [answer.lower() for answer in possible_answers]:
                points = 20
                self.update_stats(ctx.author.id, "emoji", True, points)
                
                embed = discord.Embed(
                    title="🎉 Doğru Tahmin!",
                    description=f"Tebrikler! **{emoji}** = **{correct_answer}**\n"
                               f"**Kazanılan puan:** +{points} ✨",
                    color=0x00FF00
                )
                embed.set_footer(text="Harika tahmin! 😊")
            else:
                self.update_stats(ctx.author.id, "emoji", False)
                all_answers = " / ".join(possible_answers)
                embed = discord.Embed(
                    title="❌ Yanlış Tahmin!",
                    description=f"**Sizin cevabınız:** {response.content}\n"
                               f"**Doğru cevaplar:** {all_answers}",
                    color=0xE74C3C
                )
                embed.set_footer(text="Tekrar deneyin!")
            
            await ctx.send(embed=embed)
            
        except asyncio.TimeoutError:
            self.update_stats(ctx.author.id, "emoji", False)
            all_answers = " / ".join(possible_answers)
            embed = discord.Embed(
                title="⏰ Süre Doldu!",
                description=f"**{emoji}** = **{all_answers}**",
                color=0xE74C3C
            )
            embed.set_footer(text="Daha hızlı olmalısınız!")
            await ctx.send(embed=embed)

    @commands.command(name="hafıza", aliases=["memory"])
    async def memory_game(self, ctx, difficulty: str = "kolay"):
        """🧠 Hafıza oyunu - Sayı dizilerini ezberleyin"""
        difficulties = {
            "kolay": {"length": 4, "time": 3, "points": 20},
            "orta": {"length": 6, "time": 4, "points": 50},
            "zor": {"length": 8, "time": 5, "points": 100}
        }
        
        if difficulty.lower() not in difficulties:
            return await ctx.send("❌ Zorluk seviyesi: **kolay**, **orta**, **zor**")
        
        level = difficulties[difficulty.lower()]
        sequence = [random.randint(1, 9) for _ in range(level["length"])]
        sequence_str = " ".join(map(str, sequence))
        
        # Diziyi göster
        embed = discord.Embed(
            title="🧠 Hafıza Oyunu",
            description=f"**Zorluk:** {difficulty.title()}\n\n"
                       f"Bu sayı dizisini ezberleyin:\n\n**{sequence_str}**\n\n"
                       f"⏱️ {level['time']} saniye süreniz var!",
            color=0x9B59B6
        )
        embed.set_footer(text="Dikkatle bakın!")
        message = await ctx.send(embed=embed)
        
        # Bekleme süresi
        await asyncio.sleep(level["time"])
        
        # Mesajı sil
        try:
            await message.delete()
        except:
            pass
        
        # Soruyu sor
        embed = discord.Embed(
            title="🤔 Şimdi Hatırlayın!",
            description="Gördüğünüz sayı dizisini boşlukla ayırarak yazın:\n"
                       "**Örnek:** 1 2 3 4",
            color=0xF39C12
        )
        embed.set_footer(text="Tam olarak hatırlayın!")
        await ctx.send(embed=embed)
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel
        
        try:
            response = await self.bot.wait_for('message', check=check, timeout=30.0)
            user_sequence = response.content.split()
            
            if len(user_sequence) != len(sequence):
                self.update_stats(ctx.author.id, "memory", False)
                embed = discord.Embed(
                    title="❌ Yanlış Uzunluk!",
                    description=f"**{len(sequence)}** sayı bekleniyor, **{len(user_sequence)}** sayı verdiniz.\n"
                               f"**Doğru dizi:** {sequence_str}",
                    color=0xE74C3C
                )
            elif user_sequence == [str(x) for x in sequence]:
                self.update_stats(ctx.author.id, "memory", True, level["points"])
                embed = discord.Embed(
                    title="🎉 Mükemmel Hafıza!",
                    description=f"Tebrikler! Diziyi tamamen doğru hatırladınız!\n"
                               f"**Kazanılan puan:** +{level['points']} ✨",
                    color=0x00FF00
                )
                embed.set_footer(text="Hafıza ustası! 🧠")
            else:
                self.update_stats(ctx.author.id, "memory", False)
                embed = discord.Embed(
                    title="❌ Yanlış Dizi!",
                    description=f"**Sizin diziniz:** {' '.join(user_sequence)}\n"
                               f"**Doğru dizi:** {sequence_str}",
                    color=0xE74C3C
                )
                embed.set_footer(text="Tekrar deneyin!")
            
            await ctx.send(embed=embed)
            
        except asyncio.TimeoutError:
            self.update_stats(ctx.author.id, "memory", False)
            embed = discord.Embed(
                title="⏰ Süre Doldu!",
                description=f"**Doğru dizi:** {sequence_str}",
                color=0xE74C3C
            )
            embed.set_footer(text="Daha hızlı olmalısınız!")
            await ctx.send(embed=embed)

    @commands.command(name="bilmece", aliases=["riddle"])
    async def riddle_game(self, ctx):
        """🔮 Bilmece çözme oyunu"""
        riddle = random.choice(self.riddles)
        question = riddle["question"]
        answer = riddle["answer"]
        hints = riddle["hints"]
        
        embed = discord.Embed(
            title="🔮 Bilmece",
            description=f"**{question}**\n\n"
                       f"⏱️ 45 saniyeniz var!\n"
                       f"💡 İpucu için **'ipucu'** yazın (maksimum 2 ipucu)",
            color=0x9B59B6
        )
        embed.set_footer(text="Düşünün ve tahmin edin!")
        await ctx.send(embed=embed)
        
        used_hints = 0
        max_hints = 2
        start_time = datetime.now()
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel
        
        while True:
            try:
                response = await self.bot.wait_for('message', check=check, timeout=45.0)
                elapsed = (datetime.now() - start_time).total_seconds()
                
                if elapsed > 45:
                    break
                
                user_response = response.content.lower().strip()
                
                if user_response in ["ipucu", "hint", "ip"]:
                    if used_hints < max_hints:
                        hint_text = hints[used_hints]
                        used_hints += 1
                        remaining_hints = max_hints - used_hints
                        
                        embed = discord.Embed(
                            title="💡 İpucu",
                            description=f"**İpucu {used_hints}:** {hint_text}\n\n"
                                       f"**Kalan ipucu:** {remaining_hints}",
                            color=0xF39C12
                        )
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("❌ Tüm ipuçlarınızı kullandınız!")
                    continue
                
                if user_response == answer.lower():
                    # Doğru cevap
                    points = max(100 - used_hints * 25 - int(elapsed), 10)
                    self.update_stats(ctx.author.id, "riddle", True, points)
                    
                    embed = discord.Embed(
                        title="🎉 Bilmece Çözüldü!",
                        description=f"Tebrikler! Doğru cevap: **{answer}**\n\n"
                                   f"**Süre:** {elapsed:.1f}s\n"
                                   f"**Kullanılan ipucu:** {used_hints}\n"
                                   f"**Kazanılan puan:** +{points} ✨",
                        color=0x00FF00
                    )
                    embed.set_footer(text="Zeka ustası! 🧠")
                    await ctx.send(embed=embed)
                    return
                
                else:
                    remaining_time = 45 - elapsed
                    if remaining_time > 0:
                        embed = discord.Embed(
                            title="❌ Yanlış Cevap",
                            description=f"Tekrar deneyin! **{remaining_time:.0f}** saniyeniz kaldı.",
                            color=0xE74C3C
                        )
                        await ctx.send(embed=embed)
                    else:
                        break
                        
            except asyncio.TimeoutError:
                break
        
        # Süre doldu veya yanlış cevaplar
        self.update_stats(ctx.author.id, "riddle", False)
        embed = discord.Embed(
            title="⏰ Bilmece Bitmedi!",
            description=f"Süre doldu veya doğru cevabı bulamadınız.\n"
                       f"**Doğru cevap:** {answer}",
            color=0xE74C3C
        )
        embed.set_footer(text="Tekrar deneyin!")
        await ctx.send(embed=embed)

    @commands.command(name="oyunlar", aliases=["dashboard", "panel"])
    async def games_dashboard(self, ctx):
        """🎮 Interaktif oyun paneli"""
        embed = discord.Embed(
            title="🎮 Mini Oyunlar Dashboard",
            description="Oynamak istediğiniz oyunu seçin!",
            color=0x9B59B6
        )
        
        embed.add_field(
            name="🎯 Mevcut Oyunlar",
            value="🔢 **Sayı Tahmin** - `!tahmin`\n"
                  "❓ **Trivia** - `!trivia`\n"
                  "😊 **Emoji** - `!emoji`\n"
                  "🧠 **Hafıza** - `!hafıza`\n"
                  "🔮 **Bilmece** - `!bilmece`",
            inline=False
        )
        
        embed.set_footer(text="Komutları kullanarak oyunları başlatabilirsiniz! 🎮")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MiniGames(bot))

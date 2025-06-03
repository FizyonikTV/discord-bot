import discord
from discord.ext import commands
import json
import random
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from utils.permissions import has_mod_role

class Economy(commands.Cog):
    """💰 Ekonomi sistemi - Para kazanın ve harcayın!"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/economy.json"
        self.load_data()
        
    def load_data(self):
        """Ekonomi verilerini yükler"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.economy_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.economy_data = {}
            self.save_data()
    
    def save_data(self):
        """Ekonomi verilerini kaydeder"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.economy_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ekonomi verileri kaydedilirken hata: {e}")
    
    def get_user_data(self, user_id: int, guild_id: int):
        """Kullanıcı verilerini getirir"""
        guild_key = str(guild_id)
        user_key = str(user_id)
        
        if guild_key not in self.economy_data:
            self.economy_data[guild_key] = {}
        
        if user_key not in self.economy_data[guild_key]:
            self.economy_data[guild_key][user_key] = {
                "balance": 100,  # Başlangıç parası
                "last_daily": None,
                "last_work": None,
                "total_earned": 100
            }
        
        return self.economy_data[guild_key][user_key]
    
    def update_balance(self, user_id: int, guild_id: int, amount: int):
        """Kullanıcı bakiyesini günceller"""
        user_data = self.get_user_data(user_id, guild_id)
        user_data["balance"] += amount
        if amount > 0:
            user_data["total_earned"] += amount
        self.save_data()
        return user_data["balance"]

    @commands.command(name="para", aliases=["balance", "bal", "cüzdan"])
    async def balance(self, ctx, member: discord.Member = None):
        """💰 Para durumunuzu gösterir"""
        target = member or ctx.author
        user_data = self.get_user_data(target.id, ctx.guild.id)
        
        embed = discord.Embed(
            title=f"💰 {target.display_name} - Cüzdan",
            color=0xFFD700
        )
        embed.add_field(
            name="🪙 Mevcut Bakiye",
            value=f"**{user_data['balance']:,}** coin",
            inline=True
        )
        embed.add_field(
            name="📈 Toplam Kazanılan",
            value=f"**{user_data['total_earned']:,}** coin",
            inline=True
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="💡 !günlük, !çalış komutları ile para kazanabilirsiniz!")
        
        await ctx.send(embed=embed)

    @commands.command(name="günlük", aliases=["daily"])
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 24 saat cooldown
    async def daily(self, ctx):
        """🎁 Günlük para ödülünüzü alın"""
        user_data = self.get_user_data(ctx.author.id, ctx.guild.id)
        
        # Random günlük ödül
        daily_amount = random.randint(200, 500)
        new_balance = self.update_balance(ctx.author.id, ctx.guild.id, daily_amount)
        
        embed = discord.Embed(
            title="🎁 Günlük Ödül!",
            description=f"Günlük ödülünüz: **{daily_amount:,}** coin!",
            color=0x00FF00
        )
        embed.add_field(
            name="💰 Yeni Bakiye",
            value=f"**{new_balance:,}** coin",
            inline=True
        )
        embed.set_footer(text="📅 Bir sonraki ödül için 24 saat bekleyin!")
        
        await ctx.send(embed=embed)

    @commands.command(name="çalış", aliases=["work"])
    @commands.cooldown(1, 3600, commands.BucketType.user)  # 1 saat cooldown
    async def work(self, ctx):
        """⚒️ Çalışarak para kazanın"""
        
        jobs = [
            ("🍕 Pizza servisi yaptınız", 50, 150),
            ("📦 Kargo taşıdınız", 40, 120),  
            ("🧹 Temizlik yaptınız", 30, 100),
            ("💻 Kod yazdınız", 80, 200),
            ("🎨 Resim çizdiniz", 60, 160),
            ("🚗 Taxi şoförlüğü yaptınız", 70, 180),
            ("📚 Ders verdiniz", 90, 220),
            ("🎵 Müzik yaptınız", 65, 175)
        ]
        
        job_desc, min_earn, max_earn = random.choice(jobs)
        earned = random.randint(min_earn, max_earn)
        new_balance = self.update_balance(ctx.author.id, ctx.guild.id, earned)
        
        embed = discord.Embed(
            title="⚒️ Çalışma Sonucu",
            description=job_desc,
            color=0x3498DB
        )
        embed.add_field(
            name="💵 Kazandığınız",
            value=f"**{earned:,}** coin",
            inline=True
        )
        embed.add_field(
            name="💰 Yeni Bakiye", 
            value=f"**{new_balance:,}** coin",
            inline=True
        )
        embed.set_footer(text="⏰ Bir sonraki çalışma için 1 saat bekleyin!")
        
        await ctx.send(embed=embed)

    @commands.command(name="slot")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def slot_machine(self, ctx, bet: int = None):
        """🎰 Slot makinesi oynayın"""
        if bet is None:
            return await ctx.send("❌ Bahis miktarını belirtin! Örnek: `!slot 100`")
        
        user_data = self.get_user_data(ctx.author.id, ctx.guild.id)
        
        if bet < 10:
            return await ctx.send("❌ Minimum bahis 10 coin!")
        
        if bet > user_data["balance"]:
            return await ctx.send("❌ Yeterli coin'iniz yok!")
        
        # Slot sembolleri
        symbols = ["🍎", "🍊", "🍋", "🍇", "🍒", "⭐", "💎", "7️⃣"]
        weights = [20, 20, 20, 15, 15, 5, 3, 2]  # Nadir semboller daha az çıkar
        
        # 3 sembol seç
        result = random.choices(symbols, weights=weights, k=3)
        
        # Kazanç hesapla
        multiplier = 0
        if result[0] == result[1] == result[2]:  # 3'ü aynı
            if result[0] == "💎":
                multiplier = 10
            elif result[0] == "7️⃣":
                multiplier = 8
            elif result[0] == "⭐":
                multiplier = 5
            else:
                multiplier = 3
        elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:  # 2'si aynı
            multiplier = 1.5
        
        # Para hesapla
        if multiplier > 0:
            winnings = int(bet * multiplier)
            self.update_balance(ctx.author.id, ctx.guild.id, winnings - bet)
            result_text = f"🎉 Kazandınız! **{winnings:,}** coin!"
            color = 0x00FF00
        else:
            self.update_balance(ctx.author.id, ctx.guild.id, -bet)
            result_text = f"😢 Kaybettiniz! **{bet:,}** coin gitti."
            color = 0xFF0000
        
        embed = discord.Embed(
            title="🎰 Slot Makinesi",
            description=f"```\n🎰 [ {' | '.join(result)} ] 🎰\n```",
            color=color
        )
        embed.add_field(name="📊 Sonuç", value=result_text, inline=False)
        
        new_balance = self.get_user_data(ctx.author.id, ctx.guild.id)["balance"]
        embed.add_field(name="💰 Bakiye", value=f"**{new_balance:,}** coin", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="gönder", aliases=["transfer", "pay"])
    async def transfer_money(self, ctx, member: discord.Member, amount: int):
        """💸 Başka bir kullanıcıya para gönderin"""
        if member.bot:
            return await ctx.send("❌ Botlara para gönderemezsiniz!")
        
        if member.id == ctx.author.id:
            return await ctx.send("❌ Kendinize para gönderemezsiniz!")
        
        if amount <= 0:
            return await ctx.send("❌ Miktar 0'dan büyük olmalı!")
        
        sender_data = self.get_user_data(ctx.author.id, ctx.guild.id)
        
        if amount > sender_data["balance"]:
            return await ctx.send("❌ Yeterli coin'iniz yok!")
        
        # Transfer gerçekleştir
        self.update_balance(ctx.author.id, ctx.guild.id, -amount)
        self.update_balance(member.id, ctx.guild.id, amount)
        
        embed = discord.Embed(
            title="💸 Para Transferi",
            description=f"{ctx.author.mention} ➡️ {member.mention}",
            color=0x3498DB
        )
        embed.add_field(
            name="💰 Transfer Miktarı",
            value=f"**{amount:,}** coin",
            inline=True
        )
        
        new_balance = self.get_user_data(ctx.author.id, ctx.guild.id)["balance"]
        embed.add_field(
            name="📊 Yeni Bakiyeniz",
            value=f"**{new_balance:,}** coin",
            inline=True
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="zenginler", aliases=["leaderboard", "top"])
    async def leaderboard(self, ctx, page: int = 1):
        """🏆 En zengin kullanıcıları gösterir"""
        guild_key = str(ctx.guild.id)
        
        if guild_key not in self.economy_data:
            return await ctx.send("❌ Henüz ekonomi verisi yok!")
        
        # Kullanıcıları bakiyeye göre sırala
        users = []
        for user_id, data in self.economy_data[guild_key].items():
            try:
                member = ctx.guild.get_member(int(user_id))
                if member and not member.bot:
                    users.append((member, data["balance"]))
            except:
                continue
        
        users.sort(key=lambda x: x[1], reverse=True)
        
        # Sayfalama
        per_page = 10
        total_pages = (len(users) - 1) // per_page + 1
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_users = users[start_idx:end_idx]
        
        embed = discord.Embed(
            title="🏆 Zenginlik Sıralaması",
            color=0xFFD700
        )
        
        description = ""
        for i, (member, balance) in enumerate(page_users, start=start_idx + 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}.**"
            description += f"{medal} {member.display_name} - **{balance:,}** coin\n"
        
        embed.description = description or "Henüz veri yok."
        embed.set_footer(text=f"Sayfa {page}/{total_pages}")
        
        await ctx.send(embed=embed)

    @commands.command(name="paraver", aliases=["addmoney"])
    @has_mod_role()
    async def add_money(self, ctx, member: discord.Member, amount: int):
        """💰 Kullanıcıya para verir (Sadece yetkili)"""
        new_balance = self.update_balance(member.id, ctx.guild.id, amount)
        
        embed = discord.Embed(
            title="💰 Para Eklendi",
            description=f"{member.mention} kullanıcısına **{amount:,}** coin eklendi!",
            color=0x00FF00
        )
        embed.add_field(
            name="💳 Yeni Bakiye",
            value=f"**{new_balance:,}** coin",
            inline=True
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="blackjack", aliases=["bj"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def blackjack(self, ctx, bet: int = None):
        """🃏 Blackjack oynayın (21)"""
        if bet is None:
            return await ctx.send("❌ Bahis miktarını belirtin! Örnek: `!blackjack 100`")
        
        user_data = self.get_user_data(ctx.author.id, ctx.guild.id)
        
        if bet < 10:
            return await ctx.send("❌ Minimum bahis 10 coin!")
        if bet > user_data["balance"]:
            return await ctx.send("❌ Yeterli coin'iniz yok!")

        def draw_card():
            card = random.choice(["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"])
            value = 11 if card == "A" else 10 if card in ["J", "Q", "K"] else int(card)
            return card, value

        def calculate_hand(hand):
            total = sum(value for card, value in hand)
            # A için ayarlama
            aces = sum(1 for card, value in hand if card == "A")
            while total > 21 and aces:
                total -= 10
                aces -= 1
            return total

        player_hand = [draw_card(), draw_card()]
        dealer_hand = [draw_card(), draw_card()]

        player_total = calculate_hand(player_hand)
        dealer_total = calculate_hand(dealer_hand)

        def format_hand(hand):
            return " ".join(card for card, value in hand)

        # Oyuncuya kart çekip çekmeyeceği sorulur
        while player_total < 21:
            embed = discord.Embed(
                title="🃏 Blackjack",
                description=(
                    f"**Eliniz:** {format_hand(player_hand)} (`{player_total}`)\n"
                    f"**Kasa:** {dealer_hand[0][0]} ❓\n\n"
                    "**Kart çekmek için `çek`, durmak için `dur` yazın.**"
                ),
                color=0x3498DB
            )
            await ctx.send(embed=embed)

            try:
                msg = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ["çek", "dur"],
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                await ctx.send("⏰ Zaman aşımı! Oyun iptal edildi.")
                return

            if msg.content.lower() == "dur":
                break
            else:
                card = draw_card()
                player_hand.append(card)
                player_total = calculate_hand(player_hand)

        # Oyuncu battı mı
        if player_total > 21:
            self.update_balance(ctx.author.id, ctx.guild.id, -bet)
            return await ctx.send(f"💥 Battınız! Eliniz: {format_hand(player_hand)} (`{player_total}`)\n**{bet:,} coin kaybettiniz.**")

        # Kasa sırası
        while dealer_total < 17:
            dealer_hand.append(draw_card())
            dealer_total = calculate_hand(dealer_hand)

        result_embed = discord.Embed(title="🃏 Blackjack Sonucu", color=0x00FF00)

        result_embed.add_field(name="🧑 Oyuncu Eli", value=f"{format_hand(player_hand)} (`{player_total}`)", inline=False)
        result_embed.add_field(name="🏦 Kasa Eli", value=f"{format_hand(dealer_hand)} (`{dealer_total}`)", inline=False)

        if dealer_total > 21 or player_total > dealer_total:
            winnings = bet * 2
            self.update_balance(ctx.author.id, ctx.guild.id, bet)
            result_embed.description = f"🎉 Kazandınız! **{winnings - bet:,}** coin kâr ettiniz."
            result_embed.color = 0x00FF00
        elif player_total == dealer_total:
            result_embed.description = "🤝 Berabere! Bahsiniz iade edildi."
            result_embed.color = 0xAAAAAA
        else:
            self.update_balance(ctx.author.id, ctx.guild.id, -bet)
            result_embed.description = f"😞 Kaybettiniz! **{bet:,}** coin gitti."
            result_embed.color = 0xFF0000

        new_balance = self.get_user_data(ctx.author.id, ctx.guild.id)["balance"]
        result_embed.set_footer(text=f"💰 Yeni Bakiye: {new_balance:,} coin")
        await ctx.send(embed=result_embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))

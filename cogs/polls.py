import discord
from discord.ext import commands
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional

class Polls(commands.Cog):
    """🗳️ Anket sistemi - Topluluk oylamaları yapın"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_polls = {}
        self.polls_data_file = "data/polls.json"
        self.load_polls_data()
    
    def load_polls_data(self):
        """Anket verilerini yükler"""
        try:
            with open(self.polls_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Aktif anketleri yeniden başlat
                for poll_id, poll_data in data.items():
                    if poll_data.get("active", False):
                        self.active_polls[int(poll_id)] = poll_data
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    def save_polls_data(self):
        """Anket verilerini kaydeder"""
        try:
            all_data = {}
            for poll_id, poll_data in self.active_polls.items():
                all_data[str(poll_id)] = poll_data
            
            with open(self.polls_data_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Anket verileri kaydedilirken hata: {e}")

    @commands.command(name="anket", aliases=["poll"])
    async def create_poll(self, ctx, duration: Optional[int] = None, *, question_and_options: str = None):
        """🗳️ Yeni anket oluşturur
        
        Kullanım: !anket [süre_dakika] soru | seçenek1 | seçenek2 | ...
        Örnek: !anket 30 En sevdiğiniz renk? | Kırmızı | Mavi | Yeşil
        """
        if not question_and_options:
            embed = discord.Embed(
                title="❌ Geçersiz Format",
                description=(
                    "**Kullanım:**\n"
                    "`!anket [süre] soru | seçenek1 | seçenek2 | ...`\n\n"
                    "**Örnek:**\n"
                    "`!anket 30 En sevdiğiniz renk? | Kırmızı | Mavi | Yeşil`\n"
                    "`!anket En sevdiğiniz oyun? | Minecraft | Valorant | LOL`"
                ),
                color=0xFF0000
            )
            return await ctx.send(embed=embed)
        
        # Soru ve seçenekleri ayır
        parts = question_and_options.split("|")
        if len(parts) < 3:
            return await ctx.send("❌ En az 2 seçenek belirtmelisiniz!")
        
        if len(parts) > 11:  # 10 seçenek + soru
            return await ctx.send("❌ En fazla 10 seçenek belirtebilirsiniz!")
        
        question = parts[0].strip()
        options = [opt.strip() for opt in parts[1:] if opt.strip()]
        
        if not question:
            return await ctx.send("❌ Soru belirtmelisiniz!")
        
        if len(options) < 2:
            return await ctx.send("❌ En az 2 seçenek belirtmelisiniz!")
        
        # Süre kontrolü
        if duration is None:
            duration = 60  # Varsayılan 1 saat
        
        if duration < 1:
            return await ctx.send("❌ Süre en az 1 dakika olmalıdır!")
        
        if duration > 10080:  # 1 hafta
            return await ctx.send("❌ Süre en fazla 1 hafta (10080 dakika) olabilir!")
        
        # Emoji'ler
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        # Embed oluştur
        embed = discord.Embed(
            title="🗳️ Anket",
            description=f"**{question}**",
            color=0x3498DB,
            timestamp=datetime.utcnow()
        )
        
        options_text = ""
        for i, option in enumerate(options):
            options_text += f"{number_emojis[i]} {option}\n"
        
        embed.add_field(
            name="Seçenekler",
            value=options_text,
            inline=False
        )
        
        end_time = datetime.utcnow() + timedelta(minutes=duration)
        embed.add_field(
            name="⏰ Süre",
            value=f"{duration} dakika",
            inline=True
        )
        embed.add_field(
            name="📊 Durum",
            value="🟢 Aktif",
            inline=True
        )
        embed.add_field(
            name="👤 Oluşturan",
            value=ctx.author.mention,
            inline=True
        )
        
        embed.set_footer(text=f"Bitiş: {end_time.strftime('%d.%m.%Y %H:%M')} UTC")
        
        # Anketi gönder
        poll_message = await ctx.send(embed=embed)
        
        # Reaction'ları ekle
        for i in range(len(options)):
            await poll_message.add_reaction(number_emojis[i])
        
        # Anket verilerini kaydet
        poll_data = {
            "question": question,
            "options": options,
            "creator_id": ctx.author.id,
            "channel_id": ctx.channel.id,
            "guild_id": ctx.guild.id,
            "end_time": end_time.isoformat(),
            "active": True,
            "votes": {str(i): [] for i in range(len(options))}
        }
        
        self.active_polls[poll_message.id] = poll_data
        self.save_polls_data()
        
        # Otomatik bitiş
        await asyncio.sleep(duration * 60)
        await self.end_poll(poll_message.id)

    @commands.command(name="anketsonuç", aliases=["pollresult"])
    async def poll_result(self, ctx, message_id: int = None):
        """📊 Anket sonuçlarını gösterir"""
        if message_id is None:
            # Son anketleri listele
            guild_polls = [(pid, data) for pid, data in self.active_polls.items() 
                          if data["guild_id"] == ctx.guild.id]
            
            if not guild_polls:
                return await ctx.send("❌ Bu sunucuda aktif anket bulunamadı!")
            
            embed = discord.Embed(
                title="📊 Sunucudaki Anketler",
                color=0x9B59B6
            )
            
            for poll_id, poll_data in guild_polls[-5:]:  # Son 5 anket
                status = "🟢 Aktif" if poll_data["active"] else "🔴 Bitti"
                embed.add_field(
                    name=f"{poll_data['question'][:50]}...",
                    value=f"ID: `{poll_id}` - {status}",
                    inline=False
                )
            
            embed.set_footer(text="Detaylı sonuç için: !anketsonuç <message_id>")
            return await ctx.send(embed=embed)
        
        if message_id not in self.active_polls:
            return await ctx.send("❌ Bu ID'ye ait anket bulunamadı!")
        
        poll_data = self.active_polls[message_id]
        
        if poll_data["guild_id"] != ctx.guild.id:
            return await ctx.send("❌ Bu anket bu sunucuya ait değil!")
        
        # Sonuçları hesapla
        total_votes = sum(len(voters) for voters in poll_data["votes"].values())
        
        embed = discord.Embed(
            title="📊 Anket Sonuçları",
            description=f"**{poll_data['question']}**",
            color=0x9B59B6
        )
        
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        results_text = ""
        for i, option in enumerate(poll_data["options"]):
            vote_count = len(poll_data["votes"][str(i)])
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            
            # Progress bar
            bar_length = 10
            filled_length = int(bar_length * vote_count / total_votes) if total_votes > 0 else 0
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            
            results_text += f"{number_emojis[i]} **{option}**\n"
            results_text += f"`{bar}` {vote_count} oy (%{percentage:.1f})\n\n"
        
        embed.add_field(
            name="Sonuçlar",
            value=results_text,
            inline=False
        )
        
        embed.add_field(
            name="📊 İstatistikler",
            value=f"Toplam oy: **{total_votes}**\n"
                  f"Durum: {'🟢 Aktif' if poll_data['active'] else '🔴 Bitti'}",
            inline=True
        )
        
        creator = self.bot.get_user(poll_data["creator_id"])
        if creator:
            embed.add_field(
                name="👤 Oluşturan",
                value=creator.mention,
                inline=True
            )
        
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Anket oylarını işler"""
        if user.bot:
            return
        
        message_id = reaction.message.id
        if message_id not in self.active_polls:
            return
        
        poll_data = self.active_polls[message_id]
        
        if not poll_data["active"]:
            return
        
        # Emoji kontrolü
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        emoji_str = str(reaction.emoji)
        
        if emoji_str not in number_emojis:
            return
        
        option_index = number_emojis.index(emoji_str)
        
        if option_index >= len(poll_data["options"]):
            return
        
        # Kullanıcının önceki oyunu kaldır
        user_id = user.id
        for i, voters in poll_data["votes"].items():
            if user_id in voters:
                voters.remove(user_id)
        
        # Yeni oyu ekle
        poll_data["votes"][str(option_index)].append(user_id)
        self.save_polls_data()

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """Anket oylarını kaldırır"""
        if user.bot:
            return
        
        message_id = reaction.message.id
        if message_id not in self.active_polls:
            return
        
        poll_data = self.active_polls[message_id]
        
        if not poll_data["active"]:
            return
        
        # Emoji kontrolü
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        emoji_str = str(reaction.emoji)
        
        if emoji_str not in number_emojis:
            return
        
        option_index = number_emojis.index(emoji_str)
        
        if option_index >= len(poll_data["options"]):
            return
        
        # Oyu kaldır
        user_id = user.id
        if user_id in poll_data["votes"][str(option_index)]:
            poll_data["votes"][str(option_index)].remove(user_id)
            self.save_polls_data()

    async def end_poll(self, message_id: int):
        """Anketi sonlandırır"""
        if message_id not in self.active_polls:
            return
        
        poll_data = self.active_polls[message_id]
        poll_data["active"] = False
        self.save_polls_data()
        
        # Sonuç mesajı gönder
        try:
            channel = self.bot.get_channel(poll_data["channel_id"])
            if channel:
                total_votes = sum(len(voters) for voters in poll_data["votes"].values())
                
                if total_votes == 0:
                    await channel.send(f"📊 Anket bitti! (ID: {message_id}) - Hiç oy alınmadı.")
                    return
                
                # En çok oyu alan seçeneği bul
                max_votes = 0
                winning_options = []
                
                for i, voters in poll_data["votes"].items():
                    vote_count = len(voters)
                    if vote_count > max_votes:
                        max_votes = vote_count
                        winning_options = [poll_data["options"][int(i)]]
                    elif vote_count == max_votes:
                        winning_options.append(poll_data["options"][int(i)])
                
                embed = discord.Embed(
                    title="🏆 Anket Sonuçlandı!",
                    description=f"**{poll_data['question']}**",
                    color=0x00FF00
                )
                
                if len(winning_options) == 1:
                    embed.add_field(
                        name="🥇 Kazanan",
                        value=f"**{winning_options[0]}** ({max_votes} oy)",
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🤝 Berabere",
                        value=f"**{', '.join(winning_options)}** ({max_votes} oy)",
                        inline=False
                    )
                
                embed.add_field(
                    name="📊 Toplam Oy",
                    value=f"**{total_votes}** oy",
                    inline=True
                )
                
                embed.set_footer(text=f"Detaylı sonuçlar: !anketsonuç {message_id}")
                
                await channel.send(embed=embed)
                
        except Exception as e:
            print(f"Anket sonlandırılırken hata: {e}")

    @commands.command(name="anketbitir", aliases=["endpoll"])
    async def end_poll_command(self, ctx, message_id: int):
        """🛑 Anketi manuel olarak bitirir (Sadece anket sahibi veya yetkili)"""
        if message_id not in self.active_polls:
            return await ctx.send("❌ Bu ID'ye ait aktif anket bulunamadı!")
        
        poll_data = self.active_polls[message_id]
        
        # Yetki kontrolü
        is_creator = poll_data["creator_id"] == ctx.author.id
        is_mod = any(role.id in [1234567890] for role in ctx.author.roles)  # MOD rolü ID'si
        is_admin = ctx.author.guild_permissions.administrator
        
        if not (is_creator or is_mod or is_admin):
            return await ctx.send("❌ Bu anketi sadece oluşturan kişi veya yetkililer bitirebilir!")
        
        if not poll_data["active"]:
            return await ctx.send("❌ Bu anket zaten bitmiş!")
        
        await self.end_poll(message_id)
        await ctx.send(f"✅ Anket başarıyla sonlandırıldı! (ID: {message_id})")

    @commands.command(name="hızlıanket", aliases=["quickpoll"])
    async def quick_poll(self, ctx, *, question: str):
        """⚡ Hızlı Evet/Hayır anketi"""
        embed = discord.Embed(
            title="⚡ Hızlı Anket",
            description=f"**{question}**",
            color=0xE74C3C,
            timestamp=datetime.utcnow()
        )
        embed.add_field(
            name="Seçenekler",
            value="✅ Evet\n❌ Hayır",
            inline=False
        )
        embed.set_footer(text=f"Oluşturan: {ctx.author.display_name}")
        
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")
        await message.add_reaction("❌")

async def setup(bot):
    await bot.add_cog(Polls(bot))

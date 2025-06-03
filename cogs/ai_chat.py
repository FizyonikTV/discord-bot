import discord
from discord.ext import commands
import asyncio
import json
import os
import time
from datetime import datetime
import random
from typing import Optional
import logging

# Ücretsiz AI servisleri için gerekli imports
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

MAX_MESSAGE_LENGTH = 2000

async def send_message_in_chunks(channel, message):
    for i in range(0, len(message), MAX_MESSAGE_LENGTH):
        chunk = message[i:i + MAX_MESSAGE_LENGTH]
        await channel.send(chunk)

class FreeAIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()
        self.conversations = self.load_conversations()
        self.rate_limits = {}
        self.daily_usage = {}
        self.setup_ai_services()
        self.fallback_responses = [
            "Üzgünüm, şu anda cevap veremiyorum. Lütfen daha sonra tekrar deneyin.",
        ]

    def load_config(self):
        config_path = os.path.join("config", "ai_config.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"enabled": False}

    def load_conversations(self):
        conversations_path = os.path.join("data", "ai_conversations.json")
        try:
            with open(conversations_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def save_conversations(self):
        os.makedirs("data", exist_ok=True)
        conversations_path = os.path.join("data", "ai_conversations.json")
        with open(conversations_path, 'w', encoding='utf-8') as f:
            json.dump(self.conversations, f, ensure_ascii=False, indent=2)

    def setup_ai_services(self):
        self.ai_services = {}
        gemini_key = os.getenv("GOOGLE_GEMINI_API_KEY") or self.config.get("google_gemini_api_key")
        if GEMINI_AVAILABLE and gemini_key and gemini_key != "YOUR_GEMINI_API_KEY_HERE":
            try:
                genai.configure(api_key=gemini_key)
                self.ai_services['gemini'] = genai.GenerativeModel('gemini-2.0-flash')
                print("✅ Google Gemini AI hazır!")
            except Exception as e:
                print(f"❌ Gemini kurulumu başarısız: {e}")

    async def get_ai_response(self, prompt: str, user_id: int, model_preference: str = None) -> str:
        if not self.check_rate_limit(user_id):
            return "🚫 Rate limite takıldın! Biraz bekle."
        try:
            response = await self.get_gemini_response(prompt)
            if response:
                self.update_rate_limit(user_id, "gemini")
                return response
        except Exception as e:
            print(f"❌ Gemini hatası: {e}")
        return random.choice(self.fallback_responses)

    async def get_gemini_response(self, prompt: str) -> Optional[str]:
        try:
            if "gemini" not in self.ai_services:
                return None
            model = self.ai_services['gemini']
            response = await model.generate_content_async(prompt)
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'candidates') and response.candidates:
                return response.candidates[0].content.parts[0].text
            return None
        except Exception as e:
            print(f"Gemini hatası: {e}")
            return None

    def check_rate_limit(self, user_id: int) -> bool:
        """Rate limiting kontrolü"""
        now = time.time()
        user_id_str = str(user_id)
        
        # Günlük limit kontrolü
        today = datetime.now().strftime("%Y-%m-%d")
        if user_id_str not in self.daily_usage:
            self.daily_usage[user_id_str] = {}
        if today not in self.daily_usage[user_id_str]:
            self.daily_usage[user_id_str][today] = 0
        
        if self.daily_usage[user_id_str][today] >= self.config.get("daily_limit_per_user", 100):
            return False
        
        # Cooldown kontrolü
        if user_id_str in self.rate_limits:
            if now - self.rate_limits[user_id_str] < self.config.get("cooldown_seconds", 15):
                return False
        
        return True

    def update_rate_limit(self, user_id: int, model: str):
        """Rate limit güncelle"""
        user_id_str = str(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        self.rate_limits[user_id_str] = time.time()
        if user_id_str not in self.daily_usage:
            self.daily_usage[user_id_str] = {}
        if today not in self.daily_usage[user_id_str]:
            self.daily_usage[user_id_str][today] = 0
        self.daily_usage[user_id_str][today] += 1

    @commands.group(name='ai', aliases=['sohbet'])
    async def ai_group(self, ctx):
        """AI Chat komutları"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="🤖 AI Chat Komutları",
                description="Google Gemini 2.0 Flash ile sohbet et!",
                color=0x00ff00
            )
            embed.add_field(
                name="📝 Komutlar",
                value="""
!ai chat <mesaj>    - Gemini 2.0 Flash ile sohbet
!ai stats           - Kullanım istatistikleri
!ai setup           - Kurulum rehberi
""",
                inline=False
            )
            await ctx.send(embed=embed)

    @ai_group.command(name='chat', aliases=['sohbet'])
    async def ai_chat(self, ctx, *, message: str):
        """Genel AI sohbet"""
        if not self.config.get("enabled", False):
            await ctx.send("🚫 AI Chat devre dışı!")
            return

        async with ctx.typing():
            response = await self.get_ai_response(message, ctx.author.id)
            if len(response) > MAX_MESSAGE_LENGTH:
                await send_message_in_chunks(ctx, response)
            else:
                await ctx.send(response)

    @ai_group.command(name='stats')
    async def ai_stats(self, ctx):
        """Kullanım istatistikleri"""
        user_id = str(ctx.author.id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        daily_usage = 0
        if user_id in self.daily_usage and today in self.daily_usage[user_id]:
            daily_usage = self.daily_usage[user_id][today]
        
        daily_limit = self.config.get("daily_limit_per_user", 100)
        remaining = daily_limit - daily_usage
        
        embed = discord.Embed(
            title="📊 AI Kullanım İstatistiklerin",
            color=0x00ff00
        )
        embed.add_field(
            name="Bugün",
            value=f"**Kullanılan:** {daily_usage}\n**Kalan:** {remaining}\n**Limit:** {daily_limit}",
            inline=True
        )
        
        # Rate limit durumu
        last_use = self.rate_limits.get(user_id, 0)
        cooldown_remaining = max(0, self.config.get("cooldown_seconds", 15) - (time.time() - last_use))
        
        embed.add_field(
            name="Cooldown",
            value=f"**Kalan:** {int(cooldown_remaining)} saniye" if cooldown_remaining > 0 else "✅ Hazır",
            inline=True
        )
        
        await ctx.send(embed=embed)

    @ai_group.command(name='setup')
    @commands.has_permissions(administrator=True)
    async def ai_setup(self, ctx):
        """AI kurulum rehberi"""
        embed = discord.Embed(
            title="🛠️ AI Chat Kurulum Rehberi",
            description="Google Gemini 2.0 Flash ile sohbet için kurulum:",
            color=0xffa500
        )
        embed.add_field(
            name="1️⃣ Google Gemini (Ücretsiz)",
            value="• [Google AI Studio](https://makersuite.google.com/app/apikey) adresine git\n"
                  "• Google hesabınla giriş yap\n"
                  "• 'Create API Key' butonuna tıkla\n"
                  "• API anahtarını kopyala",
            inline=False
        )
        embed.add_field(
            name="2️⃣ .env Dosyasını Güncelle",
            value="""
GOOGLE_GEMINI_API_KEY=your_gemini_key_here
""",
            inline=False
        )
        embed.add_field(
            name="3️⃣ Bot Yeniden Başlat",
            value="API anahtarını .env dosyasına ekledikten sonra botu yeniden başlatın.",
            inline=False
        )
        embed.set_footer(text="LunarisBot AI Chat Kurulum Yardımı", icon_url=self.bot.user.display_avatar.url if self.bot.user.avatar else None)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """1377724205835092108 ID'li kanalda otomatik AI yanıtı"""
        if message.author.bot or not message.guild:
            return
        # Kanal ID'sini sabitliyoruz
        AUTO_AI_CHANNEL_ID = 1377724205835092108
        if message.channel.id != AUTO_AI_CHANNEL_ID:
            return
        if not self.config.get("enabled", False):
            return
        if message.content.strip().startswith("!"):
            return  # Komutları atla
        async with message.channel.typing():
            response = await self.get_ai_response(message.content, message.author.id)
            if len(response) > MAX_MESSAGE_LENGTH:
                await send_message_in_chunks(message.channel, response)
            else:
                embed = discord.Embed(
                    title="💬 AI Otomatik Yanıt",
                    description=response,
                    color=0x8e44ad
                )
                embed.set_footer(text=f"{message.author.display_name} • AI Yanıtı", icon_url=message.author.display_avatar.url if message.author.avatar else None)
                await message.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(FreeAIChat(bot))
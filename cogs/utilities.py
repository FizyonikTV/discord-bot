from discord.ext.commands import BucketType
import discord
from discord.ext import commands
from discord.ui import View, Select
import asyncio
import time
from utils.helpers import izin_kontrol, command_check  # Ensure command_check is imported
from config.config import TIMEOUT_LOG_KANAL_ID, BAN_LOG_KANAL_ID, WARN_LOG_KANAL_ID

def create_home_embed():
    """Ana yardım embed'ini oluşturur"""
    embed = discord.Embed(
        title="📚 Lunaris Bot Yardım Menüsü",
        description="Aşağıdaki kategorilerden birini seçin veya belirli bir komut hakkında bilgi almak için `!yardım <komut_adı>` yazın.",
        color=0x8B008B
    )
    embed.set_thumbnail(url="https://i.ibb.co/wvQCt9C/lunaris-pp.png")
    embed.set_footer(text="LunarisBot • Kategorileri görmek için aşağıdaki menüyü kullanın")
    return embed

def create_moderation_embed():
    embed = discord.Embed(
        title="🛡️ Moderasyon Komutları",
        description="Sunucuyu yönetmek için gerekli komutlar:",
        color=0x8B008B
    )

    embed.add_field(
        name="⚠️ Uyarı ve Ceza Sistemi",
        value=(
            "```\n!uyar <@kullanıcı> <sebep>```\n"
            "• Kullanıcıyı belirtilen sebeple uyarır\n"
            "```\n!zaman <@kullanıcı> <süre> [sebep]```\n"
            "• Kullanıcıya timeout verir (mute)\n"
            "```\n!zamankaldir <@kullanıcı>```\n"
            "• Kullanıcının timeout'unu kaldırır\n"
            "```\n!yasakla <@kullanıcı> [sebep]```\n"
            "• Kullanıcıyı sunucudan yasaklar\n"
            "```\n!yasakkaldir <@kullanıcı>```\n"
            "• Kullanıcının yasaklamasını kaldırır\n"
        ),
        inline=False
    )

    embed.add_field(
        name="📋 Moderasyon Kayıtları",
        value=(
            "```\n!notlar <kullanıcı_id>```\n"
            "• Kullanıcının moderasyon geçmişini gösterir\n"
            "```\n!notsil <kullanıcı_id> <uyari/timeout/ban> <index>```\n"
            "• Kullanıcının belirtilen notunu siler\n"
            "```\n!nottemizle <kullanıcı_id>```\n"
            "• Kullanıcının tüm moderasyon kayıtlarını temizler"
        ),
        inline=False
    )

    embed.add_field(
        name="🧹 Mesaj Yönetimi",
        value=(
            "```\n!temizle <miktar>```\n"
            "• Belirtilen sayıda mesajı siler (max 100)"
        ),
        inline=False
    )

    embed.add_field(
        name="🤖 AutoMod Yönetimi",
        value=(
            "```\n!automod```\n"
            "• AutoMod ayarlarını gösterir\n"
            "```\n!automod toggle```\n"
            "• AutoMod'u açar/kapatır\n"
            "```\n!automod blacklist add/remove <kelime>```\n"
            "• Yasaklı kelime ekler/kaldırır\n"
            "```\n!automod ihlallar <@kullanıcı>```\n"
            "• Kullanıcının ihlallerini gösterir\n"
            "```\n!automod ihlalsifirla [@kullanıcı]```\n"
            "• Kullanıcının veya tüm kullanıcıların ihlallerini sıfırlar"
        ),
        inline=False
    )

    embed.set_footer(text="🔒 Bu komutları kullanmak için yönetici izinleri gerekir")
    return embed

def create_cekilis_embed():
    embed = discord.Embed(
        title="🎉 Çekiliş Komutları",
        description="Heyecan verici çekilişler düzenleyin!",
        color=0x8B008B
    )

    embed.add_field(
        name="📊 Çekiliş Yönetimi",
        value=(
            "```\n!çekiliş <süre> <kazanan_sayısı> [@rol] <ödül>```\n"
            "• Yeni bir çekiliş başlatır\n"
            "• Süre formatı: 1s, 1m, 1h, 1d\n"
            "• İsteğe bağlı minimum rol gereksinimi\n"
            "```\n!çekilişbitir <mesaj_id>```\n"
            "• Aktif bir çekilişi erkenden bitirir\n"
            "```\n!yenidençek <mesaj_id>```\n"
            "• Bitmiş bir çekilişi yeniden çeker\n"
            "```\n!çekilişler```\n"
            "• Aktif çekilişleri listeler\n"
            "```\n!çekilişbilgi <mesaj_id>```\n"
            "• Belirli bir çekiliş hakkında bilgi verir"
        ),
        inline=False
    )

    embed.set_footer(text="🎉 Çekilişlere katılmak için tepki emojisine tıklayın")
    return embed

def create_info_embed():
    embed = discord.Embed(
        title="ℹ️ Bilgi Komutları",
        description="Sunucu ve kullanıcı bilgileri için komutlar:",
        color=0x8B008B
    )

    embed.add_field(
        name="📊 Sunucu Komutları",
        value=(
            "```\n!sunucu```\n"
            "• Sunucu hakkında detaylı bilgi verir\n"
            "```\n!ping```\n"
            "• Botun yanıt verme süresini gösterir"
        ),
        inline=False
    )

    embed.add_field(
        name="📝 Bot Bilgileri",
        value=(
            "```\n!yardım [komut_adı]```\n"
            "• Komutlar hakkında yardım gösterir\n"
            "• Belirli bir komut için detaylı bilgi alabilirsiniz"
        ),
        inline=False
    )

    embed.set_footer(text="Bot hakkında daha fazla bilgi için: !yardım <komut_adı>")
    return embed

def create_level_embed():
    embed = discord.Embed(
        title="⭐ Seviye Sistemi",
        description="Aktif olmaya devam ederek seviye kazanın!",
        color=0x8B008B
    )

    embed.add_field(
        name="📊 Seviye Komutları",
        value=(
            "```\n!seviye [@kullanıcı]```\n"
            "• Seviyenizi veya belirtilen kullanıcının seviyesini gösterir\n"
            "```\n!sıralama [sayfa]```\n"
            "• Sunucudaki en yüksek seviyeli üyeleri gösterir\n"
            "```\n!xpekle [@kullanıcı]```\n"
            "• Belirtilen kullanıcıya XP ekler\n"
            "```\n!xpsıfırla [@kullanıcı]```\n"
            "• Belirtilen kullanıcının XP'sini sıfırlar\n"
        ),
        inline=False
    )

    embed.add_field(
        name="🏆 Seviye Ödülleri",
        value=(
            "Her seviye ile birlikte XP kazanım hızınız artar.\n"
            "Belirli seviyelerde özel roller kazanırsınız.\n"
            "Seviye atladığınızda bildirim alırsınız."
        ),
        inline=False
    )

    embed.set_footer(text="Sohbet ettikçe ve sesli kanallarda vakit geçirdikçe XP kazanırsınız")
    return embed

def create_user_info_embed():
    embed = discord.Embed(
        title="👤 Kullanıcı Komutları",
        description="Kullanıcı bilgilerine erişim komutları:",
        color=0x8B008B
    )

    embed.add_field(
        name="👤 Profil Komutları",
        value=(
            "```\n!kullanici [@kullanıcı]```\n"
            "• Kullanıcı hakkında detaylı bilgi gösterir\n"
            "```\n!avatar [@kullanıcı]```\n"
            "• Kullanıcının avatarını gösterir\n"
            "```\n!banner [@kullanıcı]```\n"
            "• Kullanıcının banner'ını gösterir (varsa)\n"
        ),
        inline=False
    )

    embed.add_field(
        name="📱 Bot Bilgileri",
        value=(
            "```\n!botinfo```\n"
            "• Bot hakkında detaylı bilgi gösterir\n"
        ),
        inline=False
    )

    embed.set_footer(text="Bu komutları herkes kullanabilir")
    return embed

class HelpView(View):
    def __init__(self, ctx):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.value = None
        
        # Kategori seçimi dropdown menüsü
        self.category_select = Select(
            placeholder="Yardım kategorisini seçin",
            options=[
                discord.SelectOption(
                    label="Ana Sayfa",
                    description="Ana yardım menüsü",
                    emoji="🏠",
                    value="home"
                ),
                discord.SelectOption(
                    label="Moderasyon",
                    description="Moderasyon komutları",
                    emoji="🛡️",
                    value="moderation"
                ),
                discord.SelectOption(
                    label="Seviye Sistemi",
                    description="Seviye komutları",
                    emoji="⭐",
                    value="level"
                ),
                discord.SelectOption(
                    label="Kullanıcı Komutları",
                    description="Kullanıcı bilgileri komutları",
                    emoji="👤",
                    value="user"
                ),
                discord.SelectOption(
                    label="Çekiliş Komutları",
                    description="Çekiliş yönetimi",
                    emoji="🎉",
                    value="cekilis"
                ),
                discord.SelectOption(
                    label="Bilgi Komutları",
                    description="Bilgi komutları",
                    emoji="ℹ️",
                    value="bilgi"
                )
            ]
        )
        self.category_select.callback = self.select_callback
        self.add_item(self.category_select)
    
    async def select_callback(self, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ Bu menüyü sadece komutu kullanan kişi kullanabilir!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        selected = self.category_select.values[0]
        
        if selected == "home":
            embed = create_home_embed()
        elif selected == "moderation":
            embed = create_moderation_embed()
        elif selected == "level":
            embed = create_level_embed()
        elif selected == "user":
            embed = create_user_info_embed()
        elif selected == "cekilis":
            embed = create_cekilis_embed()
        elif selected == "bilgi":
            embed = create_info_embed()
        else:
            embed = create_home_embed()
            
        await interaction.message.edit(embed=embed)

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')

    @commands.command(name="yardım", aliases=["yardim", "help", "h", "y"])
    @commands.cooldown(1, 3, BucketType.user)
    @commands.check(command_check())  # Apply the channel restriction check
    async def yardim(self, ctx, command_name=None):
        """İnteraktif yardım menüsünü gösterir"""
        if command_name:
            # Belirli bir komuta ait yardım bilgisini göster
            command = self.bot.get_command(command_name)
            if not command:
                await ctx.send(f"❌ `{command_name}` adında bir komut bulunamadı.")
                return
                
            embed = discord.Embed(
                title=f"📖 {command.name.capitalize()} Komutu",
                description=command.help or "Bu komut için açıklama bulunmuyor.",
                color=0x8B008B
            )
            
            usage = f"!{command.name}"
            if command.signature:
                usage = f"!{command.name} {command.signature}"
                
            embed.add_field(name="📝 Kullanım", value=f"`{usage}`", inline=False)
            
            if command.aliases:
                embed.add_field(
                    name="🔄 Alternatif Komutlar", 
                    value=", ".join([f"`!{alias}`" for alias in command.aliases]),
                    inline=False
                )
                
            await ctx.send(embed=embed)
            return
        
        # Ana yardım menüsünü göster
        view = HelpView(ctx)
        embed = create_home_embed()
        await ctx.send(embed=embed, view=view)

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Botun gecikme süresini gösterir"""
        # Websocket gecikmesi
        ws_latency = round(self.bot.latency * 1000)
        
        # Mesaj gecikmesi
        start_time = time.time()
        message = await ctx.send("Ölçülüyor...")
        end_time = time.time()
        msg_latency = round((end_time - start_time) * 1000)

        embed = discord.Embed(
            title="🏓 Pong!",
            color=0x2ecc71 if ws_latency < 200 else 0xe74c3c
        )
        
        embed.add_field(
            name="📡 Websocket Gecikmesi",
            value=f"```{ws_latency}ms```",
            inline=True
        )
        
        embed.add_field(
            name="💭 Mesaj Gecikmesi",
            value=f"```{msg_latency}ms```",
            inline=True
        )

        embed.set_footer(text="🟢 İyi | 🟡 Orta | 🔴 Kötü")
        
        # Gecikme durumuna göre emoji
        status = "🟢" if ws_latency < 200 else "🟡" if ws_latency < 400 else "🔴"
        embed.description = f"Genel Durum: {status}"
        
        await message.edit(content=None, embed=embed)

    @commands.command(name="temizle", aliases=["clear", "sil"])
    @commands.cooldown(1, 5, BucketType.user)
    @commands.has_permissions(manage_messages=True)
    async def temizle(self, ctx, miktar: int):
        """Belirtilen sayıda mesajı siler"""
        if miktar <= 0:
            return await ctx.send("❌ Silinecek mesaj sayısı 0'dan büyük olmalıdır.")
        if miktar > 100:
            return await ctx.send("❌ En fazla 100 mesaj silebilirim.")
        
        deleted = await ctx.channel.purge(limit=miktar + 1)

        # Send a confirmation message
        info_message = await ctx.send(
            embed=discord.Embed(
                title="🧹 Mesajlar Temizlendi",
                description=f"{len(deleted) - 1} mesaj başarıyla silindi.",
                color=discord.Color.green()
            )
        )
        
        await asyncio.sleep(3)
        await info_message.delete()

async def setup(bot):
    await bot.add_cog(Utilities(bot))
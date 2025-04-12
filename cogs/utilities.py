import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import datetime
import time
from discord.ext.commands import cooldown, BucketType
import asyncio
from config.config import IZIN_VERILEN_ROLLER

def has_required_role():
    async def predicate(ctx):
        return any(role.id in IZIN_VERILEN_ROLLER for role in ctx.author.roles)
    return commands.check(predicate)

class HelpView(View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx

        # Ana Menü Butonu
        self.home_button = Button(
            style=discord.ButtonStyle.secondary,
            emoji="🏠",
            custom_id="home",
            label="Ana Menü"
        )
        self.home_button.callback = self.home_callback
        self.add_item(self.home_button)

        # Kategori Seçici
        self.category_select = Select(
            placeholder="Kategori Seçin",
            options=[
                discord.SelectOption(
                    label="Moderasyon",
                    description="Moderasyon komutları",
                    emoji="🛡️",
                    value="moderasyon"
                ),
                discord.SelectOption(
                    label="Seviye Sistemi",
                    description="XP ve seviye yönetimi",
                    emoji="📈",
                    value="seviye"
                ),
                discord.SelectOption(
                    label="Çekiliş Sistemi",
                    description="Çekiliş yönetimi",
                    emoji="🎉",
                    value="cekilis"
                ),
                discord.SelectOption(
                    label="Diğer Komutlar",
                    description="Diğer komutlar",
                    emoji="ℹ️",
                    value="bilgi"
                )
            ]
        )
        self.category_select.callback = self.select_callback
        self.add_item(self.category_select)

    async def home_callback(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ Bu menüyü sadece komutu kullanan kişi kullanabilir!", ephemeral=True)
        embed = create_home_embed()
        await interaction.response.edit_message(embed=embed)

    async def select_callback(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                "❌ Bu menüyü sadece komutu kullanan kişi kullanabilir!", 
                ephemeral=True
            )

        category = self.category_select.values[0]
        embed = None

        if category == "moderasyon":
            embed = create_moderasyon_embed()
        elif category == "seviye":
            embed = create_seviye_embed()
        elif category == "cekilis":
            embed = create_cekilis_embed()
        elif category == "bilgi":
            embed = create_bilgi_embed()

        if embed:
            await interaction.response.edit_message(embed=embed)

def create_home_embed():
    embed = discord.Embed(
        title="✨ Lunaris Bot - Yardım Menüsü",
        description=(
            "Hoş geldiniz! Aşağıdaki kategorilerden birini seçerek ilgili komutlar hakkında detaylı bilgi alabilirsiniz.\n"
        ),
        color=0x2b2d31
    )

    embed.add_field(
        name="🛡️ Moderasyon Komutları",
        value=(
            "• Uyarı ve ceza sistemi\n"
            "• Timeout yönetimi\n"
            "• Yasaklama işlemleri\n"
            "• Not yönetimi"
        ),
        inline=True
    )

    embed.add_field(
        name="📈 Seviye Sistemi",
        value=(
            "• XP kazanma\n"
            "• Seviye rolleri\n"
            "• Sıralama tablosu\n"
            "• XP yönetimi"
        ),
        inline=True
    )

    embed.add_field(name="\u200b", value="\u200b", inline=True)

    embed.add_field(
        name="🎉 Çekiliş Sistemi",
        value=(
            "• Çekiliş başlatma\n"
            "• Yeniden çekme\n"
            "• Aktif çekilişler\n"
            "• Çekiliş yönetimi"
        ),
        inline=True
    )

    embed.add_field(
        name="ℹ️ Diğer Komutlar",
        value=(
            "• Temizleme komutları\n"
            "• Sunucu bilgileri\n"
            "• Kullanıcı bilgileri\n"
            "• İstatistikler"
            "• Bot bilgileri\n"
        ),
        inline=True
    )

    embed.set_footer(text="💡 Bir kategori seçmek için aşağıdaki menüyü kullanın")
    return embed

def create_moderasyon_embed():
    embed = discord.Embed(
        title="🛡️ Moderasyon Komutları",
        description="Sunucunuzu yönetmek için gereken tüm moderasyon komutları burada!",
        color=0xff3366
    )

    embed.add_field(
        name="⚠️ Uyarı Komutları",
        value=(
            "```\n!uyar @kullanıcı <sebep>```\n"
            "Kullanıcıyı belirtilen sebeple uyarır.\n"
        ),
        inline=False
    )

    embed.add_field(
        name="📝 Not Komutları",
        value=(
            "```\n!notlar <kullanıcı_id>```\n"
            "Kullanıcının tüm moderasyon geçmişini gösterir.\n"
            "```\n!notsil <kullanıcı_id> <tür> <sıra>```\n"
            "Belirtilen moderasyon kaydını siler.\n"
            "```\n!nottemizle <kullanıcı_id>```\n"
            "Kullanıcının tüm kayıtlarını temizler."
        ),
        inline=False
    )

    embed.add_field(
        name="⏳ Timeout Komutları",
        value=(
            "```\n!zaman @kullanıcı <süre> <sebep>```\n"
            "Kullanıcıya belirtilen süre kadar timeout verir.\n"
            "```\n!zamankaldir @kullanıcı```\n"
            "Kullanıcının timeout'unu kaldırır."
        ),
        inline=False
    )

    embed.add_field(
        name="🔨 Yasaklama Komutları",
        value=(
            "```\n!yasakla @kullanıcı <sebep>```\n"
            "Kullanıcıya yasaklı rolü verir.\n"
            "```\n!yasakkaldir @kullanıcı```\n"
            "Kullanıcının yasaklı rolünü kaldırır."
        ),
        inline=False
    )

    embed.set_footer(text="⚠️ Bu komutları kullanmak için yetki gerekir")
    return embed

def create_seviye_embed():
    embed = discord.Embed(
        title="📈 Seviye Sistemi",
        description="Aktif olarak sohbet ederek seviye kazanın ve ödüller alın!",
        color=0x2ecc71
    )

    embed.add_field(
        name="📊 Seviye Komutları",
        value=(
            "```\n!rank [@kullanıcı]```\n"
            "• Kendinizin veya başka bir kullanıcının seviyesini görün\n"
            "• XP miktarını ve bir sonraki seviyeye kalan XP'yi öğrenin\n"
            "```\n!sıralama [sayfa]```\n"
            "• Sunucudaki XP sıralamasını görün\n"
            "• Sayfa numarası belirterek farklı sıralamaları inceleyin"
        ),
        inline=False
    )

    embed.add_field(
        name="⚡ Yetkili Komutları",
        value=(
            "```\n!xpekle @kullanıcı <miktar>```\n"
            "• Belirtilen kullanıcıya XP ekler\n"
            "```\n!xpsıfırla @kullanıcı```\n"
            "• Kullanıcının XP'sini sıfırlar"
        ),
        inline=False
    )

    embed.set_footer(text="💡 Her mesaj gönderdiğinizde XP kazanırsınız")
    return embed

def create_cekilis_embed():
    embed = discord.Embed(
        title="🎉 Çekiliş Komutları",
        description="Heyecan verici çekilişler düzenleyin!",
        color=0xffd700
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
            "• Aktif çekilişleri listeler"
        ),
        inline=False
    )

    embed.set_footer(text="🎉 Çekilişlere katılmak için tepki emojisine tıklayın")
    return embed

def create_bilgi_embed():
    embed = discord.Embed(
        title="ℹ️ Diğer Komutlar",
        description="Diğer komutlar!",
        color=0x95a5a6
    )


    embed.add_field(
        name="🧹 Temizleme Komutları",
        value=(
            "```\n!temizle <mesaj_sayısı>```\n"
            "• Belirtilen sayıda mesajı siler\n"
            "• En fazla 100 mesaj silinebilir\n"
            "• Yalnızca yöneticiler kullanabilir"
        ),
        inline=False
    )
    
    embed.add_field(
        name="👤 Kullanıcı Bilgileri",
        value=(
            "```\n!kullanici [@kullanıcı]```\n"
            "• Kullanıcı hakkında detaylı bilgi\n"
            "• Roller, katılım tarihi ve daha fazlası\n"
            "```\n!avatar [@kullanıcı]```\n"
            "• Kullanıcının profil resmini görüntüler"
        ),
        inline=False
    )

    embed.add_field(
        name="📊 Sunucu Bilgileri",
        value=(
            "```\n!sunucu```\n"
            "• Sunucu hakkında detaylı bilgiler\n"
            "• Üye sayısı, rol sayısı ve daha fazlası"
        ),
        inline=False
    )

    embed.add_field(
        name="🤖 Bot Bilgileri",
        value=(
            "```\n!botinfo```\n"
            "• Bot hakkında teknik bilgiler\n"
            "• Çalışma süresi ve sistem durumu\n"
            "```\n!ping```\n"
            "• Botun gecikme süresini gösterir"
        ),
        inline=False
    )

    embed.set_footer(text="🔄 Bot sürekli güncellenmektedir")
    return embed

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')

    @commands.command(name="yardım", aliases=["yardim"])
    @commands.cooldown(1, 3, BucketType.user)
    async def yardim(self, ctx):
        """İnteraktif yardım menüsünü gösterir"""
        view = HelpView(ctx)
        embed = create_home_embed()
        await ctx.send(embed=embed, view=view)

    @commands.command(name="ping")
    @has_required_role()
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

    @commands.command(name="temizle", allias=["clear", "sil"])
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
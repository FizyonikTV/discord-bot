import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from config.config import (
    BAN_LOG_KANAL_ID, 
    WARN_LOG_KANAL_ID, 
    TIMEOUT_LOG_KANAL_ID,
    YASAKLI,
    IZIN_VERILEN_ROLLER
)
from utils.permissions import has_mod_role, has_admin
from utils.shared_models import SharedDataManager

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.shared_data = SharedDataManager(bot)
        print(f"[MOD] Moderation cog yüklendi.")
    
    async def add_mod_note(self, user_id, note_type, reason, moderator, duration=None):
        """Moderasyon notu ekler ve dashboard ile paylaşır"""
        try:
            # Tek sunucu için çalışacak şekilde düzenlendi (çoklu sunucu desteği eklenebilir)
            self.shared_data.add_note(
                guild_id=self.bot.guilds[0].id if self.bot.guilds else 0,  # İlk sunucuyu kullan
                user_id=user_id,
                note_type=note_type,
                reason=reason,
                moderator_id=moderator.id,
                moderator_name=str(moderator),
                duration=duration  # Timeout süresi
            )
            print(f"[MOD] Not eklendi: {user_id}, {note_type}, {reason}")
        except Exception as e:
            print(f"[HATA] Not eklenirken hata oluştu: {e}")
            import traceback
            traceback.print_exc()

    def create_embed(self, title, description, color, user=None):
        """Standart embed oluşturma yardımcısı"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        
        if user:
            embed.set_thumbnail(url=user.display_avatar.url)
            
        return embed

    @commands.command(name="uyar", aliases=["warn", "uyarı"])
    @has_mod_role()
    async def warn_command(self, ctx, member: discord.Member, *, reason: str = None):
        """Kullanıcıya uyarı verir"""
        if ctx.author.top_role <= member.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Bu kullanıcıya uyarı veremezsiniz!")
        
        reason = reason or "Sebep belirtilmedi"
        
        try:
            # Log oluştur
            embed = discord.Embed(
                title="⚠️ Uyarı Verildi",
                description=f"```diff\n- {member} kullanıcısı uyarıldı.\n+ Sebep: {reason}```",
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            embed.add_field(
                name="👤 Kullanıcı Bilgileri",
                value=f"```yaml\nKullanıcı: {member}\nID: {member.id}```",
                inline=False
            )
            embed.add_field(
                name="👮 Moderatör Bilgileri",
                value=f"```yaml\nModeratör: {ctx.author}\nID: {ctx.author.id}```",
                inline=False
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            
            # Not ekle - bu artık ortak veri modelini kullanacak
            await self.add_mod_note(
                user_id=member.id,
                note_type="UYARILAR",
                reason=reason,
                moderator=ctx.author
            )
            
            # Log ve DM mesajlarını gönder
            log_channel = self.bot.get_channel(WARN_LOG_KANAL_ID)
            if log_channel:
                await log_channel.send(embed=embed)
            
            # Kullanıcıya DM
            try:
                dm_embed = discord.Embed(
                    title="⚠️ Uyarı Aldınız",
                    description=f"**{ctx.guild.name}** sunucusunda uyarı aldınız.",
                    color=discord.Color.gold()
                )
                dm_embed.add_field(name="📝 Sebep", value=reason, inline=False)
                await member.send(embed=dm_embed)
            except Exception as e:
                print(f"DM gönderilirken hata: {e}")
                await ctx.send(f"⚠️ {member.mention} kullanıcısına DM gönderilemedi.")
            
            # Komut kanalına mesaj gönder (detaylı embed yerine basit onay mesajı)
            await ctx.send(f"✅ {member.mention} kullanıcısı başarıyla uyarıldı.")
            
        except Exception as e:
            await ctx.send(f"❌ Bir hata oluştu: {e}")
            import traceback
            traceback.print_exc()

    @commands.command(name="zaman", aliases=["to", "timeout", "mute"])
    @has_mod_role()
    async def timeout(self, ctx, member: discord.Member, duration: int, *, reason: str = None):
        """Kullanıcıya timeout verir - süre saniye cinsinden"""
        if ctx.author.top_role <= member.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Bu kullanıcıya timeout veremezsiniz!")

        reason = reason or "Sebep belirtilmedi"
        
        try:
            # Timeout uygula (saniye cinsinden)
            timeout_duration = timedelta(seconds=duration)
            await member.timeout(timeout_duration, reason=f"{ctx.author}: {reason}")
            
            # Not ekle
            await self.add_mod_note(
                user_id=member.id,
                note_type="TIMEOUTLAR",
                reason=reason,
                moderator=ctx.author,
                duration=f"{duration} saniye"
            )
            
            # Embed oluştur
            embed = discord.Embed(
                title="⏳ Timeout Verildi",
                description=f"```diff\n- {member} kullanıcısı timeout aldı.\n+ Süre: {duration} saniye\n+ Sebep: {reason}```",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )
            
            # Kullanıcı ve moderatör bilgilerini ekle
            embed.add_field(
                name="👤 Kullanıcı Bilgileri",
                value=f"```yaml\nKullanıcı: {member}\nID: {member.id}```",
                inline=False
            )
            embed.add_field(
                name="👮 Moderatör Bilgileri",
                value=f"```yaml\nModeratör: {ctx.author}\nID: {ctx.author.id}```",
                inline=False
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            
            # Log ve DM mesajlarını gönder
            log_channel = self.bot.get_channel(TIMEOUT_LOG_KANAL_ID)
            if log_channel:
                await log_channel.send(embed=embed)
            else:
                print(f"Log kanalı bulunamadı: {TIMEOUT_LOG_KANAL_ID}")
            
            # Kullanıcıya DM
            try:
                dm_embed = discord.Embed(
                    title="⏳ Timeout Aldınız",
                    description=f"**{ctx.guild.name}** sunucusunda timeout aldınız.",
                    color=discord.Color.orange()
                )
                dm_embed.add_field(name="⏱️ Süre", value=f"{duration} saniye", inline=True)
                dm_embed.add_field(name="📝 Sebep", value=reason, inline=True)
                await member.send(embed=dm_embed)
            except Exception as dm_error:
                print(f"DM gönderilirken hata: {dm_error}")
                await ctx.send(f"⚠️ {member.mention} kullanıcısına DM gönderilemedi.")
            
            # Komut kanalına mesajı gönder
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Bir hata oluştu: {e}")
            import traceback
            traceback.print_exc()

    @commands.command(name="zamankaldir", aliases=["untimeout", "unmute", "unto"])
    @has_mod_role()
    async def untimeout(self, ctx, member: discord.Member):
        """Kullanıcının timeout'unu kaldırır"""
        try:
            # Timeout kaldır
            await member.timeout(None, reason=f"Timeout kaldıran: {ctx.author}")
            
            # Embed oluştur
            embed = discord.Embed(
                title="✅ Timeout Kaldırıldı",
                description=f"```diff\n+ {member} kullanıcısının timeout'u kaldırıldı.```",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            # Kullanıcı ve moderatör bilgilerini ekle
            embed.add_field(
                name="👤 Kullanıcı Bilgileri",
                value=f"```yaml\nKullanıcı: {member}\nID: {member.id}```",
                inline=False
            )
            embed.add_field(
                name="👮 Moderatör Bilgileri",
                value=f"```yaml\nModeratör: {ctx.author}\nID: {ctx.author.id}```",
                inline=False
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            
            # Log ve DM mesajlarını gönder
            log_channel = self.bot.get_channel(TIMEOUT_LOG_KANAL_ID)
            if log_channel:
                await log_channel.send(embed=embed)
            
            # Kullanıcıya DM
            try:
                dm_embed = discord.Embed(
                    title="✅ Timeout'unuz Kaldırıldı",
                    description=f"**{ctx.guild.name}** sunucusundaki timeout'unuz kaldırıldı.",
                    color=discord.Color.green()
                )
                await member.send(embed=dm_embed)
            except:
                await ctx.send(f"⚠️ {member.mention} kullanıcısına DM gönderilemedi.")
            
            # Komut kanalına mesajı gönder
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Bir hata oluştu: {e}")
            import traceback
            traceback.print_exc()

    @commands.command(name="yasakla", aliases=["ban"])
    @has_mod_role()
    async def ban_command(self, ctx, member: discord.Member, *, reason: str = None):
        """Kullanıcıya yasaklı rolü verir"""
        if ctx.author.top_role <= member.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Bu kullanıcıyı yasaklayamazsınız!")
        
        reason = reason or "Sebep belirtilmedi"
        
        try:
            # Yasaklı rolü kontrol et
            yasakli_rol = ctx.guild.get_role(YASAKLI)
            if not yasakli_rol:
                return await ctx.send(f"❌ Yasaklı rolü (ID: {YASAKLI}) bulunamadı!")
            
            # Yasaklı rolü ver
            await member.add_roles(yasakli_rol, reason=f"{ctx.author}: {reason}")
            
            # Not ekle - "BANLAR" olarak düzgün tipte not ekleyin
            await self.add_mod_note(
                user_id=member.id,
                note_type="BANLAR",  # "BANLAR" olarak düzeltin
                reason=reason,
                moderator=ctx.author
            )
            
            # Embed oluştur
            embed = discord.Embed(
                title="🚫 Kullanıcı Yasaklandı",
                description=f"```diff\n- {member} kullanıcısı sunucuda yasaklandı.\n+ Sebep: {reason}```",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="👤 Kullanıcı Bilgileri",
                value=f"```yaml\nKullanıcı: {member}\nID: {member.id}```",
                inline=False
            )
            embed.add_field(
                name="👮 Moderatör Bilgileri",
                value=f"```yaml\nModeratör: {ctx.author}\nID: {ctx.author.id}```",
                inline=False
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            
            # Log ve DM mesajlarını gönder
            log_channel = self.bot.get_channel(BAN_LOG_KANAL_ID)
            if log_channel:
                await log_channel.send(embed=embed)
            
            # Kullanıcıya DM
            try:
                dm_embed = discord.Embed(
                    title="🚫 Yasaklandınız",
                    description=f"**{ctx.guild.name}** sunucusunda yasaklandınız.",
                    color=discord.Color.red()
                )
                dm_embed.add_field(name="📝 Sebep", value=reason, inline=False)
                dm_embed.add_field(name="ℹ️ Not", value="Bu bir sunucu yasaklaması değil, yasaklı rolü verilmesidir. Sunucuya erişiminiz kısıtlanmıştır.", inline=False)
                await member.send(embed=dm_embed)
            except:
                await ctx.send(f"⚠️ {member.mention} kullanıcısına DM gönderilemedi.")
            
            # Komut kanalına mesajı gönder
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Bir hata oluştu: {e}")
            import traceback
            traceback.print_exc()

    @commands.command(name="yasakkaldir", aliases=["unban"])
    @has_mod_role()
    async def unban_command(self, ctx, member: discord.Member):
        """Kullanıcının yasaklı rolünü kaldırır"""
        try:
            # Yasaklı rolü kontrol et
            yasakli_rol = ctx.guild.get_role(YASAKLI)
            if not yasakli_rol:
                return await ctx.send(f"❌ Yasaklı rolü (ID: {YASAKLI}) bulunamadı!")
            
            # Kullanıcının yasaklı rolünü kaldır
            if yasakli_rol in member.roles:
                await member.remove_roles(yasakli_rol, reason=f"Yasaklamayı kaldıran: {ctx.author}")
                
                # Embed oluştur
                embed = discord.Embed(
                    title="✅ Yasaklama Kaldırıldı",
                    description=f"```diff\n+ {member} kullanıcısının yasaklaması kaldırıldı.```",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="👤 Kullanıcı Bilgileri",
                    value=f"```yaml\nKullanıcı: {member}\nID: {member.id}```",
                    inline=False
                )
                embed.add_field(
                    name="👮 Moderatör Bilgileri",
                    value=f"```yaml\nModeratör: {ctx.author}\nID: {ctx.author.id}```",
                    inline=False
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                
                # Log ve DM mesajlarını gönder
                log_channel = self.bot.get_channel(BAN_LOG_KANAL_ID)
                if log_channel:
                    await log_channel.send(embed=embed)
                
                # Kullanıcıya DM
                try:
                    dm_embed = discord.Embed(
                        title="✅ Yasaklamanız Kaldırıldı",
                        description=f"**{ctx.guild.name}** sunucusundaki yasaklamanız kaldırıldı.",
                        color=discord.Color.green()
                    )
                    await member.send(embed=dm_embed)
                except:
                    await ctx.send(f"⚠️ {member.mention} kullanıcısına DM gönderilemedi.")
                
                # Komut kanalına mesajı gönder
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Bu kullanıcıda yasaklı rolü bulunmuyor.")
            
        except Exception as e:
            await ctx.send(f"❌ Bir hata oluştu: {e}")
            import traceback
            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(Moderation(bot))
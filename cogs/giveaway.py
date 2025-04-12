import discord
from discord.ext import commands, tasks
import json
import asyncio
from datetime import datetime, timedelta, timezone
import random
from typing import Optional, Dict, Set, List
import os

# Türkiye zaman dilimi sabiti
TR_TIMEZONE = timezone(timedelta(hours=3))

class GiveawayButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,
            emoji="🎉",
            label="Katıl!",
            custom_id="giveaway_join"
        )

    async def callback(self, interaction: discord.Interaction):
        if not self.view:
            return

        view: GiveawayView = self.view
        required_role = view.required_role

        if required_role and not interaction.user.get_role(required_role):
            role = interaction.guild.get_role(required_role)
            return await interaction.response.send_message(
                f"❌ Bu çekilişe katılmak için {role.mention} rolüne sahip olmalısınız!",
                ephemeral=True
            )

        if interaction.user.id in view.participants:
            view.participants.remove(interaction.user.id)
            await interaction.response.send_message("❌ Çekilişten ayrıldınız!", ephemeral=True)
        else:
            view.participants.add(interaction.user.id)
            await interaction.response.send_message("✅ Çekilişe katıldınız!", ephemeral=True)

        # Çekiliş verilerini güncelle
        if view.giveaway_manager:
            await view.giveaway_manager.update_participants(view.message_id, view.participants)

        await view.update_message()

class GiveawayView(discord.ui.View):
    def __init__(self, message_id: int, giveaway_manager=None, required_role: Optional[int] = None, participants: Optional[Set[int]] = None):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.participants = participants or set()  # Küme kullanarak katılımcıları sakla
        self.required_role = required_role
        self.giveaway_manager = giveaway_manager
        self.message = None
        self.add_item(GiveawayButton())

    async def update_message(self):
        if not self.message:
            return

        embed = self.message.embeds[0]
        embed.set_field_at(
            0,
            name="🎮 Katılımcılar",
            value=f"**{len(self.participants)}** katılımcı"
        )
        await self.message.edit(embed=embed)

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.giveaways_file = os.path.join(self.data_dir, "giveaways.json")
        self.ended_giveaways_file = os.path.join(self.data_dir, "ended_giveaways.json")  # Yeni dosya
        self.active_giveaways = {}
        self.ended_giveaways = {}  # Biten çekilişler için yeni dictionary
        self.active_views = {}
        self.ensure_data_directory()
        self.load_giveaways()
        self.load_ended_giveaways()  # Biten çekilişleri yükle
        self.check_giveaways.start()
        self.reroll_attempts = 5

    def ensure_data_directory(self):
        """Veri dizininin var olduğundan emin ol"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def cog_unload(self):
        self.check_giveaways.cancel()
        self.save_giveaways()  # Cog kaldırılırken verileri kaydet

    async def cog_load(self):
        """Cog yüklendiğinde çalışan metod"""
        await self.restore_active_giveaways()

    async def restore_active_giveaways(self):
        """Bot yeniden başlatıldığında aktif çekilişleri yükle"""
        for message_id, giveaway_data in self.active_giveaways.items():
            try:
                channel_id = giveaway_data["channel_id"]
                channel = self.bot.get_channel(channel_id)

                if not channel:
                    continue

                message = await channel.fetch_message(int(message_id))
                if not message:
                    continue

                participants = set(giveaway_data.get("participants", []))
                required_role = giveaway_data.get("required_role")

                # Yeni view oluştur
                view = GiveawayView(
                    message_id=int(message_id),
                    giveaway_manager=self,
                    required_role=required_role,
                    participants=participants
                )
                view.message = message

                # Mesajı güncelle
                await message.edit(view=view)

                # Aktif view'ları kaydet
                self.active_views[message_id] = view

            except (discord.NotFound, discord.HTTPException) as e:
                print(f"Çekiliş mesajı yüklenirken hata: {e} - ID: {message_id}")
                # Bulunamayan çekilişleri sil
                self.active_giveaways.pop(message_id, None)

        # Değişiklikleri kaydet
        self.save_giveaways()

    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        """Düzenli olarak çekilişleri kontrol et"""
        try:
            current_time = datetime.now(TR_TIMEZONE).timestamp()
            ended_giveaways = []

            for message_id, giveaway in self.active_giveaways.items():
                if current_time >= giveaway["end_time"]:
                    ended_giveaways.append(int(message_id))

            for message_id in ended_giveaways:
                await self.end_giveaway(message_id)
        except Exception as e:
            print(f"Çekiliş kontrolü sırasında hata: {e}")

    def load_giveaways(self):
        """Çekiliş verilerini yükle"""
        try:
            with open(self.giveaways_file, 'r', encoding='utf-8') as f:
                self.active_giveaways = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.active_giveaways = {}
            self.save_giveaways()

    def save_giveaways(self):
        """Çekiliş verilerini kaydet"""
        with open(self.giveaways_file, 'w', encoding='utf-8') as f:
            json.dump(self.active_giveaways, f, indent=4, ensure_ascii=False)

    def load_ended_giveaways(self):
        """Biten çekiliş verilerini yükle"""
        try:
            with open(self.ended_giveaways_file, 'r', encoding='utf-8') as f:
                self.ended_giveaways = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.ended_giveaways = {}
            self.save_ended_giveaways()

    def save_ended_giveaways(self):
        """Biten çekiliş verilerini kaydet"""
        with open(self.ended_giveaways_file, 'w', encoding='utf-8') as f:
            json.dump(self.ended_giveaways, f, indent=4, ensure_ascii=False)

    async def update_participants(self, message_id: int, participants: Set[int]):
        """Katılımcı listesini güncelle ve kaydet"""
        message_id_str = str(message_id)
        if message_id_str in self.active_giveaways:
            self.active_giveaways[message_id_str]["participants"] = list(participants)
            self.save_giveaways()

    def parse_time(self, time_str: str) -> int:
        """Zaman formatını saniyeye çevir"""
        time_dict = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        try:
            value = int(time_str[:-1])
            unit = time_str[-1].lower()
            if unit in time_dict:
                return value * time_dict[unit]
        except ValueError:
            return 0

    def create_giveaway_embed(self, prize: str, end_time: datetime, winners: int, host: discord.Member, required_role: Optional[discord.Role] = None):
        """Çekiliş embed'ini oluşturur"""
        embed = discord.Embed(
            title="🎉 YENİ ÇEKİLİŞ BAŞLADI!",
            description=(
                f"**🎁 Ödül: {prize}**\n\n"
                f"• 🕒 Bitiş: <t:{int(end_time.timestamp())}:R>\n"
                f"• 👥 Kazanan Sayısı: {winners}\n"
            ),
            color=0xFF1493
        )

        if required_role:
            embed.description += f"• 🎭 Gereken Rol: {required_role.mention}"

        embed.add_field(
            name="🎮 Katılımcılar",
            value="**0** katılımcı"
        )
        embed.add_field(
            name="📋 Nasıl Katılırım?",
            value="Aşağıdaki 🎉 butonuna tıklayarak katılabilirsiniz!",
            inline=False
        )
        embed.set_footer(text=f"• Çekilişi Başlatan: {host.display_name}", icon_url=host.display_avatar.url)
        return embed

    async def format_participant_list(self, ctx, participants: List[int], limit: int = 10) -> str:
        """Katılımcı listesini formatlı şekilde döndürür"""
        participant_mentions = []
        for i, p_id in enumerate(participants[:limit]):
            member = ctx.guild.get_member(p_id)
            if member:
                participant_mentions.append(f"{i+1}. {member.mention}")

        if participant_mentions:
            result = "\n".join(participant_mentions)
            if len(participants) > limit:
                result += f"\n... ve {len(participants) - limit} kişi daha"
            return result
        return "Henüz katılımcı yok"

    @commands.command(name="çekiliş", aliases=["giveaway", "çekilişbaşlat"])
    @commands.has_permissions(manage_messages=True)
    async def create_giveaway(self, ctx, time: str, winners: int, required_role: Optional[discord.Role] = None, *, prize: str):
        """Yeni bir çekiliş başlat"""
        seconds = self.parse_time(time)
        if not seconds or seconds < 10:
            return await ctx.send("❌ Geçersiz süre! En az 10 saniye olmalı.")

        if winners < 1:
            return await ctx.send("❌ Kazanan sayısı en az 1 olmalıdır!")

        end_time = datetime.now(TR_TIMEZONE) + timedelta(seconds=seconds)

        embed = self.create_giveaway_embed(prize, end_time, winners, ctx.author, required_role)

        # Önce mesajı gönder
        message = await ctx.send(embed=embed)

        # Mesaj ID'sini kullanarak view oluştur
        view = GiveawayView(
            message_id=message.id,
            giveaway_manager=self,
            required_role=required_role.id if required_role else None
        )
        view.message = message

        # Mesajı view ile güncelle
        await message.edit(view=view)

        # Aktif view'ları kaydet
        self.active_views[str(message.id)] = view

        giveaway_data = {
            "channel_id": ctx.channel.id,
            "message_id": message.id,
            "prize": prize,
            "winners": winners,
            "end_time": end_time.timestamp(),
            "host_id": ctx.author.id,
            "required_role": required_role.id if required_role else None,
            "participants": []  # Boş katılımcı listesi ile başla
        }

        self.active_giveaways[str(message.id)] = giveaway_data
        self.save_giveaways()

        await ctx.send(f"✅ Çekiliş başarıyla oluşturuldu! ID: `{message.id}`", delete_after=5)

    async def end_giveaway(self, message_id: int):
        """Çekilişi bitirir ve kazananları seçer"""
        message_id_str = str(message_id)
        giveaway = self.active_giveaways.get(message_id_str)
        if not giveaway:
            return

        try:
            channel = self.bot.get_channel(giveaway["channel_id"])
            if not channel:
                print(f"Kanal bulunamadı: {giveaway['channel_id']}")
                self.active_giveaways.pop(message_id_str, None)
                self.save_giveaways()
                return

            # Mesajı getir
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                print(f"Çekiliş mesajı bulunamadı: {message_id}")
                self.active_giveaways.pop(message_id_str, None)
                self.save_giveaways()
                return

            # Katılımcıları al
            participants = set(giveaway.get("participants", []))

            # View nesnesini aktif view'lardan temizle
            view = self.active_views.pop(message_id_str, None)

            # Geçerli katılımcıları filtrele (gerekli role sahip olanlar)
            valid_participants = []
            required_role_id = giveaway.get("required_role")
            for participant_id in participants:
                member = channel.guild.get_member(participant_id)
                if member and (required_role_id is None or member.get_role(required_role_id)):
                    valid_participants.append(participant_id)

            # Katılımcı yoksa çekilişi iptal et
            if not valid_participants:
                embed = message.embeds[0]
                embed.description += "\n\n**🔴 Çekiliş İptal Edildi: Geçerli Katılımcı Yok!**"
                embed.color = discord.Color.red()
                await message.edit(embed=embed, view=None)
                self.active_giveaways.pop(message_id_str, None)
                self.save_giveaways()
                return

            # Kazanan sayısını kontrol et
            winners_count = min(giveaway["winners"], len(valid_participants))
            if not valid_participants:
                winners = []
            else:
                winners = random.sample(valid_participants, winners_count)

            # Kazanan üyeleri bul ve mention oluştur
            winner_mentions = []
            valid_winners = []
            for winner_id in winners:
                member = channel.guild.get_member(winner_id)
                if member:
                    winner_mentions.append(member.mention)
                    valid_winners.append(member)

            # Kazanan embedini oluştur
            embed = message.embeds[0]
            embed.description += f"\n\n**🎊 Çekiliş Bitti!**"

            if winner_mentions:
                embed.add_field(
                    name="🏆 Kazananlar",
                    value="\n".join(winner_mentions),
                    inline=False
                )
            else:
                embed.add_field(
                    name="🏆 Kazananlar",
                    value="Kazanan bulunamadı!",
                    inline=False
                )

            embed.color = discord.Color.green()

            # Mesajı güncelle
            await message.edit(embed=embed, view=None)

            # Kazanan yoksa
            if not winner_mentions:
                await channel.send("❌ Çekiliş bitti fakat geçerli kazanan bulunamadı!")
            else:
                # Kazananları duyur
                announce_embed = discord.Embed(
                    title="🎉 Çekiliş Bitti!",
                    description=(
                        f"**🎁 Ödül: {giveaway['prize']}**\n"
                        f"**🏆 Kazananlar:**\n" + "\n".join(winner_mentions)
                    ),
                    color=discord.Color.gold()
                )
                announce_embed.set_footer(text=f"Çekiliş ID: {message_id}")

                await channel.send(
                    f"🎊 Tebrikler {', '.join(winner_mentions)}! **{giveaway['prize']}** kazandınız!",
                    embed=announce_embed
                )

                # Kazananlara özel mesaj gönder
                for winner in valid_winners:
                    try:
                        winner_embed = discord.Embed(
                            title="🎉 Tebrikler! Bir çekiliş kazandınız!",
                            description=f"**{channel.guild.name}** sunucusunda **{giveaway['prize']}** ödülünü kazandınız!",
                            color=discord.Color.gold()
                        )
                        winner_embed.add_field(
                            name="📢 Çekilişin olduğu kanal",
                            value=f"<#{channel.id}>",
                            inline=False
                        )
                        winner_embed.add_field(
                            name="🔗 Çekiliş bağlantısı",
                            value=f"[Buraya tıkla]({message.jump_url})",
                            inline=False
                        )
                        await winner.send(embed=winner_embed)
                    except (discord.Forbidden, discord.HTTPException):
                        pass  # DM gönderilemiyorsa devam et

        except Exception as e:
            print(f"Çekiliş bitirme hatası: {e}")
        finally:
            # Çekilişi aktif listeden çıkar ve biten çekilişlere ekle
            if message_id_str in self.active_giveaways:
                giveaway_data = self.active_giveaways.pop(message_id_str)
                self.ended_giveaways[message_id_str] = giveaway_data
                self.save_giveaways()
                self.save_ended_giveaways()

    async def _get_giveaway_data(self, message_id: int) -> Optional[Dict]:
        """Çekiliş verilerini ID'ye göre getirir."""
        message_id_str = str(message_id)
        return self.active_giveaways.get(message_id_str)

    async def _get_valid_participants(self, channel: discord.TextChannel, participants: Set[int], required_role_id: Optional[int] = None) -> List[discord.Member]:
        """Geçerli katılımcı listesini (sunucuda olan ve gerekli role sahip) döndürür."""
        valid_participants = []
        for participant_id in participants:
            member = channel.guild.get_member(participant_id)
            if member and (required_role_id is None or member.get_role(required_role_id)):
                valid_participants.append(member)
        return valid_participants

    @commands.command(name="çekilişbitir", aliases=["endgiveaway"])
    @commands.has_permissions(manage_messages=True)
    async def end_giveaway_command(self, ctx, message_id: int):
        """Bir çekilişi erken bitir"""
        message_id_str = str(message_id)
        if message_id_str not in self.active_giveaways:
            return await ctx.send("❌ Belirtilen ID'ye sahip aktif bir çekiliş bulunamadı!")

        await self.end_giveaway(message_id)
        await ctx.send("✅ Çekiliş erken bitirildi!")

    @commands.command(name="yenidençek", aliases=["reroll"])
    @commands.has_permissions(manage_messages=True)
    async def reroll(self, ctx, message_id: int):
        """Bir çekilişte yeni kazanan seç"""
        message_id_str = str(message_id)
        giveaway_data = self.active_giveaways.get(message_id_str) or self.ended_giveaways.get(message_id_str)

        if not giveaway_data:
            return await ctx.send("❌ Bu çekiliş bulunamadı!")

        try:
            message = await ctx.channel.fetch_message(message_id)

            participants = set(giveaway_data.get("participants", []))
            required_role_id = giveaway_data.get("required_role")

            channel = self.bot.get_channel(giveaway_data["channel_id"])
            if not channel:
                return await ctx.send("❌ Çekilişin kanalı bulunamadı!")

            valid_participants = await self._get_valid_participants(channel, participants, required_role_id)

            if not valid_participants:
                return await ctx.send("❌ Bu çekilişte geçerli katılımcı bulunmuyor!")

            winner = random.choice(valid_participants)

            # Ödülü bul
            prize = "bilinmeyen ödül"
            for embed in message.embeds:
                try:
                    prize = embed.description.split("**🎁 Ödül: ")[1].split("**")[0]
                    break
                except:
                    pass

            # Kazanan bilgisini gönder
            embed = discord.Embed(
                title="🎉 Yeni Kazanan!",
                description=f"🎁 Ödül: **{prize}**\n🏆 Yeni Kazanan: {winner.mention}",
                color=discord.Color.gold()
            )
            embed.set_footer(text=f"Çekiliş ID: {message_id}")

            await ctx.send(
                f"🎊 Tebrikler {winner.mention}! **{prize}** ödülünü kazandın!",
                embed=embed
            )

            # Kazanana DM gönder
            try:
                winner_embed = discord.Embed(
                    title="🎉 Tebrikler! Bir çekiliş kazandınız!",
                    description=f"**{ctx.guild.name}** sunucusunda **{prize}** ödülünü kazandınız!",
                    color=discord.Color.gold()
                )
                winner_embed.add_field(
                    name="📢 Çekilişin olduğu kanal",
                    value=f"<#{ctx.channel.id}>",
                    inline=False
                )
                winner_embed.add_field(
                    name="🔗 Çekiliş bağlantısı",
                    value=f"[Buraya tıkla]({message.jump_url})",
                    inline=False
                )
                await winner.send(embed=winner_embed)
            except (discord.Forbidden, discord.HTTPException):
                pass  # DM gönderilemiyorsa devam et

        except discord.NotFound:
            await ctx.send("❌ Belirtilen mesaj bulunamadı!")
        except Exception as e:
            print(f"Reroll hatası: {e}")
            await ctx.send("❌ Bir hata oluştu!")

    @commands.command(name="çekilişler", aliases=["giveaways", "aktivecekilis"])
    @commands.has_permissions(manage_messages=True)
    async def list_giveaways(self, ctx):
        """Aktif çekilişleri listele"""
        if not self.active_giveaways:
            return await ctx.send("❌ Aktif çekiliş bulunmuyor!")

        embed = discord.Embed(
            title="🎉 Aktif Çekilişler",
            color=discord.Color.blue()
        )

        for message_id, giveaway in self.active_giveaways.items():
            channel = self.bot.get_channel(giveaway["channel_id"])
            if not channel:
                continue

            end_time = datetime.fromtimestamp(giveaway["end_time"], TR_TIMEZONE)

            # Katılımcı sayısını al
            participant_count = len(giveaway.get("participants", []))

            embed.add_field(
                name=f"🎁 {giveaway['prize']}",
                value=(
                    f"• 📋 Çekiliş ID: `{message_id}`\n"
                    f"• 🕒 Bitiş: <t:{int(end_time.timestamp())}:R>\n"
                    f"• 👥 Kazanan Sayısı: {giveaway['winners']}\n"
                    f"• 🎮 Katılımcı Sayısı: {participant_count}\n"
                    f"• 📢 Kanal: {channel.mention}"
                ),
                inline=False
            )

        embed.set_footer(text=f"Toplam {len(self.active_giveaways)} aktif çekiliş")
        await ctx.send(embed=embed)

    @commands.command(name="çekilişbilgi", aliases=["giveawayinfo"])
    @commands.has_permissions(manage_messages=True)
    async def giveaway_info(self, ctx, message_id: int):
        """Bir çekiliş hakkında detaylı bilgi ver"""
        message_id_str = str(message_id)
        giveaway = self.active_giveaways.get(message_id_str)
        if not giveaway:
            return await ctx.send("❌ Belirtilen ID'ye sahip aktif bir çekiliş bulunamadı!")

        channel = self.bot.get_channel(giveaway["channel_id"])
        host = ctx.guild.get_member(giveaway["host_id"])
        end_time = datetime.fromtimestamp(giveaway["end_time"], TR_TIMEZONE)

        # Katılımcı bilgilerini al
        participants = giveaway.get("participants", [])
        participant_count = len(participants)

        # Gerekli rol bilgisi
        required_role = None
        if giveaway.get("required_role"):
            required_role = ctx.guild.get_role(giveaway["required_role"])

        embed = discord.Embed(
            title="🎉 Çekiliş Bilgisi",
            description=f"**🎁 Ödül:** {giveaway['prize']}",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="⏱️ Zaman Bilgisi",
            value=(
                f"• 🕒 Bitiş: <t:{int(end_time.timestamp())}:R>\n"
                f"• 📅 Bitiş Tarihi: <t:{int(end_time.timestamp())}:F>"
            ),
            inline=False
        )

        embed.add_field(
            name="👥 Katılım Bilgisi",
            value=(
                f"• 🎮 Katılımcı Sayısı: {participant_count}\n"
                f"• 🏆 Kazanan Sayısı: {giveaway['winners']}\n"
                f"• 🎭 Gereken Rol: {required_role.mention if required_role else 'Rol gerekmiyor'}"
            ),
            inline=False
        )

        embed.add_field(
            name="📋 Diğer Bilgiler",
            value=(
                f"• 📢 Kanal: {channel.mention if channel else 'Bilinmiyor'}\n"
                f"• 🧑‍💻 Çekilişi Başlatan: {host.mention if host else 'Bilinmiyor'}\n"
                f"• 🆔 Çekiliş ID: `{message_id}`"
            ),
            inline=False
        )

        # Katılımcıları göster (maks 10 kişi)
        if participants:
            participants_text = await self.format_participant_list(ctx, participants)
            embed.add_field(
                name="🎮 Katılımcılar",
                value=participants_text,
                inline=False
            )

        # Mesaj bağlantısı
        try:
            message = await channel.fetch_message(message_id)
            embed.add_field(
                name="🔗 Bağlantı",
                value=f"[Çekilişe Git]({message.jump_url})",
                inline=False
            )
        except discord.NotFound:
            # Mesaj bulunamadı
            pass
        except discord.HTTPException as e:
            # Dİğer Discord API hataları
            print(f"Mesaj bağlantısı alınırken hata: {e}")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
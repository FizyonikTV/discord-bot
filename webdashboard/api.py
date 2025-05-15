from datetime import datetime, timedelta
from aiohttp_session import get_session
import discord
from aiohttp import web
import json
import logging
import traceback
from utils.shared_models import SharedDataManager
from .auth import require_login

routes = web.RouteTableDef()
logger = logging.getLogger('dashboard')

class API:
    def __init__(self, bot):
        self.bot = bot
    
    # Yardımcı fonksiyonlar
    def get_user_from_token(self, request):
        """Get user data from session token"""
        if not hasattr(request, 'session'):
            return None
        
        user = request.session.get('user')
        if not user:
            return None
        
        return user
    
    # API endpoint handlers
    async def get_guilds(self, request):
        """Get all guilds the bot is in"""
        user = self.get_user_from_token(request)
        if not user:
            return web.json_response({"error": "Unauthorized"}, status=401)
        
        guilds = [
            {
                "id": str(guild.id),
                "name": guild.name,
                "icon": str(guild.icon.url) if guild.icon else None,
                "member_count": guild.member_count
            }
            for guild in self.bot.guilds
        ]
        
        return web.json_response(guilds)
    
    async def get_guild(self, request):
        """Get a specific guild's info"""
        user = self.get_user_from_token(request)
        if not user:
            return web.json_response({"error": "Unauthorized"}, status=401)
        
        guild_id = request.match_info['guild_id']
        guild = self.bot.get_guild(int(guild_id))
        
        if not guild:
            return web.json_response({"error": "Guild not found"}, status=404)
        
        # Kullanıcının yetkisini kontrol et
        user_guilds = user['guilds']
        user_perm = False
        
        for g in user_guilds:
            if g['id'] == guild_id:
                if (int(g['permissions']) & 0x8) == 0x8:  # 0x8 = Administrator
                    user_perm = True
                    break
        
        if not user_perm:
            return web.json_response({"error": "Unauthorized"}, status=403)
        
        # Sunucu bilgilerini döndür
        return web.json_response({
            "id": str(guild.id),
            "name": guild.name,
            "icon": str(guild.icon.url) if guild.icon else None,
            "member_count": guild.member_count,
            "owner_id": str(guild.owner_id) if guild.owner_id else None,
            "channels": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "type": str(c.type)
                }
                for c in guild.channels if hasattr(c, 'name')
            ],
            "roles": [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "color": r.color.value,
                    "position": r.position,
                    "mentionable": r.mentionable
                }
                for r in guild.roles
            ]
        })
    
    async def get_settings(self, request):
        """Get guild settings"""
        user = self.get_user_from_token(request)
        if not user:
            return web.json_response({"error": "Unauthorized"}, status=401)
        
        guild_id = request.match_info['guild_id']
        
        # Örnek veri - gerçekte veritabanından alınacak
        settings = {
            "prefix": "!",
            "welcome_channel": None,
            "log_channel": None,
            "autorole": None
        }
        
        return web.json_response(settings)
    
    async def update_settings(self, request):
        """Update guild settings"""
        user = self.get_user_from_token(request)
        if not user:
            return web.json_response({"error": "Unauthorized"}, status=401)
        
        guild_id = request.match_info['guild_id']
        
        try:
            data = await request.json()
            
            # Ayarları güncelle (örnek)
            # Gerçekte veritabanına kaydedilecek
            return web.json_response({"success": True})
            
        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON"}, status=400)
    
    async def report_error(self, request):
        """Log frontend errors"""
        try:
            data = await request.json()
            error_message = data.get('message', 'No message provided')
            error_location = data.get('location', 'Unknown')
            
            logging.error(f"Frontend Error: {error_message}")
            logging.error(f"Location: {error_location}")
            
            return web.json_response({"success": True})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

class BotAPI:
    def __init__(self, bot):
        self.bot = bot
        
    async def get_bot_stats(self, request):
        """Bot istatistiklerini döndürür"""
        uptime = datetime.now(datetime.UTC) - self.bot.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        stats = {
            "name": self.bot.user.name,
            "id": self.bot.user.id,
            "avatar_url": str(self.bot.user.avatar.url) if self.bot.user.avatar else None,
            "guilds": len(self.bot.guilds),
            "users": sum(guild.member_count for guild in self.bot.guilds),
            "uptime": f"{hours}h {minutes}m {seconds}s",
            "commands": len(self.bot.commands)
        }
        return web.json_response(stats)
    
    async def get_guilds(self, request):
        """Kullanıcının erişimi olan sunucuları listele"""
        user = self.bot.get_user_from_token(request)
        if not user:
            return web.json_response({"error": "Unauthenticated"}, status=401)
        
        # Kullanıcının erişimi olan sunucuları al
        guilds = []
        for guild in self.bot.guilds:
            member = guild.get_member(int(user['user_id']))
            if member and member.guild_permissions.administrator:
                guilds.append({
                    "id": guild.id,
                    "name": guild.name,
                    "icon_url": str(guild.icon.url) if guild.icon else None,
                    "member_count": guild.member_count,
                    "bot_in_guild": True
                })
        
        return web.json_response({"guilds": guilds})
    
    async def get_guild_info(self, request):
        """Sunucu bilgilerini verir"""
        user = self.bot.get_user_from_token(request)
        if not user:
            return web.json_response({"error": "Unauthenticated"}, status=401)
        
        guild_id = request.match_info['guild_id']
        guild = self.bot.get_guild(int(guild_id))
        
        if not guild:
            return web.json_response({"error": "Guild not found"}, status=404)
        
        # Kullanıcının bu sunucuda admin yetkisi var mı kontrol et
        member = guild.get_member(int(user['user_id']))
        if not member or not member.guild_permissions.administrator:
            return web.json_response({"error": "Unauthorized"}, status=403)
        
        # Sunucu bilgilerini döndür
        return web.json_response({
            "id": guild.id,
            "name": guild.name,
            "icon_url": str(guild.icon.url) if guild.icon else None,
            "member_count": guild.member_count,
            "channels": [{"id": c.id, "name": c.name, "type": str(c.type)} for c in guild.channels],
            "roles": [{"id": r.id, "name": r.name, "color": r.color.value} for r in guild.roles]
        })
    
    async def update_guild_settings(self, request):
        """Sunucu ayarlarını günceller"""
        user = self.bot.get_user_from_token(request)
        if not user:
            return web.json_response({"error": "Unauthenticated"}, status=401)
        
        guild_id = request.match_info['guild_id']
        guild = self.bot.get_guild(int(guild_id))
        
        if not guild:
            return web.json_response({"error": "Guild not found"}, status=404)
        
        # Kullanıcının bu sunucuda admin yetkisi var mı kontrol et
        member = guild.get_member(int(user['user_id']))
        if not member or not member.guild_permissions.administrator:
            return web.json_response({"error": "Unauthorized"}, status=403)
        
        # Ayarları güncelle
        try:
            data = await request.json()
            print(f"Guild settings update: {data}")
            
            # TODO: Veritabanına ayarları kaydet
            
            return web.json_response({"success": True})
        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logging.error(f"Error updating guild settings: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_game_news_settings(self, request):
        """Oyun haberleri ayarlarını getirir"""
        user = self.bot.get_user_from_token(request)
        if not user:
            return web.json_response({"error": "Unauthenticated"}, status=401)
        
        guild_id = request.match_info['guild_id']
        guild = self.bot.get_guild(int(guild_id))
        
        if not guild:
            return web.json_response({"error": "Guild not found"}, status=404)
        
        # Kullanıcının bu sunucuda admin yetkisi var mı kontrol et
        member = guild.get_member(int(user['user_id']))
        if not member or not member.guild_permissions.administrator:
            return web.json_response({"error": "Unauthorized"}, status=403)
        
        # Oyun haberleri ayarlarını veritabanından al
        # Burada gerçek implementasyonu ekleyebilirsiniz
        settings = {
            "enabled": True,
            "news_channel_id": None,
            "ping_role_id": None,
            "check_interval_minutes": 60,
            "min_discount_percent": 75,
            "news_sources": {
                "epic_games": True,
                "steam_deals": True
            },
            "last_news": {
                "epic_free": [],
                "steam_deals": []
            }
        }
        
        return web.json_response(settings)

    async def update_game_news_settings(self, request):
        """Oyun haberleri ayarlarını günceller"""
        user = self.bot.get_user_from_token(request)
        if not user:
            return web.json_response({"error": "Unauthenticated"}, status=401)
        
        guild_id = request.match_info['guild_id']
        guild = self.bot.get_guild(int(guild_id))
        
        if not guild:
            return web.json_response({"error": "Guild not found"}, status=404)
        
        # Kullanıcının bu sunucuda admin yetkisi var mı kontrol et
        member = guild.get_member(int(user['user_id']))
        if not member or not member.guild_permissions.administrator:
            return web.json_response({"error": "Unauthorized"}, status=403)
        
        # Ayarları güncelle
        try:
            data = await request.json()
            # Burada gerçek veritabanı güncellemesi yapılmalı
            
            return web.json_response({"success": True})
        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON"}, status=400)
            
    async def test_game_news_webhook(self, request):
        """Oyun haberleri webhook'unu test eder"""
        user = self.bot.get_user_from_token(request)
        if not user:
            return web.json_response({"error": "Unauthenticated"}, status=401)
        
        guild_id = request.match_info['guild_id']
        guild = self.bot.get_guild(int(guild_id))
        
        if not guild:
            return web.json_response({"error": "Guild not found"}, status=404)
        
        # Kullanıcının bu sunucuda admin yetkisi var mı kontrol et
        member = guild.get_member(int(user['user_id']))
        if not member or not member.guild_permissions.administrator:
            return web.json_response({"error": "Unauthorized"}, status=403)
        
        # Test webhook'u gönder
        # Burada gerçek implementasyonu ekleyebilirsiniz
        
        return web.json_response({"success": True})

    async def get_user_notes(self, request):
        """Kullanıcı moderasyon notlarını getirir"""
        user = self.bot.get_user_from_token(request)
        if not user:
            return web.json_response({"error": "Unauthenticated"}, status=401)
        
        guild_id = request.match_info['guild_id']
        user_id = request.match_info['user_id']
        
        try:
            # Discord API'den kullanıcı bilgilerini al
            discord_user = await self.bot.fetch_user(int(user_id))
            
            # Kullanıcı notları
            # Gerçek implementasyonda bu veriler notes.json'dan veya veritabanından gelecek
            example_notes = {
                "UYARILAR": [
                    {"tarih": "10.05.2023 14:30", "sebep": "Uygunsuz davranış", "moderator": "Admin123"},
                    {"tarih": "15.05.2023 18:45", "sebep": "Spam", "moderator": "AutoMod"}
                ],
                "TIMEOUTLAR": [
                    {"tarih": "20.05.2023 10:15", "sebep": "Tartışma çıkarma", "süre": "1 saat", "moderator": "Admin456"}
                ],
                "BANLAR": []
            }
            
            return web.json_response({
                "user": {
                    "username": discord_user.name,
                    "id": user_id,
                    "avatar_url": str(discord_user.avatar.url) if discord_user.avatar else str(discord_user.default_avatar.url)
                },
                "notes": example_notes
            })
        except Exception as e:
            return web.json_response({"error": f"Kullanıcı bilgileri alınamadı: {str(e)}"}, status=404)

    async def delete_note(self, request):
        """Moderasyon notunu siler"""
        user = self.bot.get_user_from_token(request)
        if not user:
            return web.json_response({"error": "Unauthenticated"}, status=401)
        
        guild_id = request.match_info['guild_id']
        guild = self.bot.get_guild(int(guild_id))
        
        if not guild:
            return web.json_response({"error": "Guild not found"}, status=404)
        
        # Kullanıcının admin yetkisi var mı kontrol et
        member = guild.get_member(int(user['user_id']))
        if not member or not member.guild_permissions.administrator:
            return web.json_response({"error": "Unauthorized"}, status=403)
        
        try:
            data = await request.json()
            user_id = data.get('user_id')
            note_type = data.get('note_type')
            note_id = int(data.get('note_id', 0))
            
            # Burada gerçek silme işlemi yapılacak
            # Örnek: self.bot.get_cog('Notes').remove_note(user_id, note_type, note_id)
            
            return web.json_response({"success": True})
        except Exception as e:
            return web.json_response({"error": f"Not silinemedi: {str(e)}"}, status=500)

    async def report_error(self, request):
        """Hata bildirimini kaydeder"""
        try:
            data = await request.json()
            error_message = data.get('message', 'No message provided')
            error_location = data.get('location', 'Unknown')
            error_stack = data.get('stack', 'No stack trace')
            
            # Log the error
            print(f"Frontend Error: {error_message}")
            print(f"Location: {error_location}")
            print(f"Stack: {error_stack}")
            
            # TODO: Hataları db'ye kaydet veya discord webhook'a gönder
            
            return web.json_response({"success": True})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

async def setup_api_routes(app, dashboard):
    """Setup API routes for the dashboard."""
    # Guild settings
    app.router.add_post('/api/guild/{guild_id}/settings', lambda request: handle_guild_settings(request, dashboard))
    
    # Moderation actions
    app.router.add_post('/api/guild/{guild_id}/moderation/warning', lambda request: handle_warning(request, dashboard))
    app.router.add_post('/api/guild/{guild_id}/moderation/timeout', lambda request: handle_timeout(request, dashboard))
    app.router.add_post('/api/guild/{guild_id}/moderation/ban', lambda request: handle_ban(request, dashboard))
    app.router.add_delete('/api/guild/{guild_id}/moderation/case/{case_id}', lambda request: handle_delete_case(request, dashboard))

async def handle_guild_settings(request, dashboard):
    """Handle API request to update guild settings."""
    try:
        session = await get_session(request)
        
        if not session:
            return web.json_response({'success': False, 'error': 'Not authenticated'}, status=401)
        
        guild_id = int(request.match_info['guild_id'])
        guild = dashboard.bot.get_guild(guild_id)
        
        if not guild:
            return web.json_response({'success': False, 'error': 'Guild not found'}, status=404)
        
        # Get data from request
        data = await request.json()
        setting = data.get('setting')
        value = data.get('value')
        
        # Here you would update the setting in your database
        # For now, just log it
        logging.info(f"Updated setting {setting} to {value} for guild {guild.name} ({guild.id})")
        
        return web.json_response({'success': True})
    except json.JSONDecodeError:
        return web.json_response({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logging.error(f"Error updating guild settings: {e}")
        logging.error(traceback.format_exc())
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def handle_warning(request, dashboard):
    """Handle API request to issue a warning."""
    try:
        session = await get_session(request)
        
        if not session:
            return web.json_response({'success': False, 'error': 'Not authenticated'}, status=401)
        
        guild_id = int(request.match_info['guild_id'])
        guild = dashboard.bot.get_guild(guild_id)
        
        if not guild:
            return web.json_response({'success': False, 'error': 'Guild not found'}, status=404)
        
        # Get data from request
        data = await request.json()
        user_id = int(data.get('user_id'))
        reason = data.get('reason')
        
        if not reason:
            return web.json_response({'success': False, 'error': 'Reason is required'}, status=400)
        
        # Find the member
        member = guild.get_member(user_id)
        if not member:
            return web.json_response({'success': False, 'error': 'Member not found'}, status=404)
        
        # Log the warning (in a real implementation, store in database)
        logging.info(f"Warning issued to {member.display_name} ({member.id}) in {guild.name}: {reason}")
        
        # Check if we can DM the user
        try:
            await member.send(f"You have received a warning in **{guild.name}**:\n**Reason:** {reason}")
        except discord.Forbidden:
            logging.warning(f"Could not send DM to {member.display_name}")
        except Exception as e:
            logging.error(f"Error sending warning DM: {e}")
        
        return web.json_response({
            'success': True, 
            'case_id': 123  # This would normally be the ID from your database
        })
    except json.JSONDecodeError:
        return web.json_response({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logging.error(f"Error issuing warning: {e}")
        logging.error(traceback.format_exc())
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def handle_timeout(request, dashboard):
    """Handle API request to timeout a user."""
    session = await get_session(request)
    
    if not session:
        return web.json_response({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        guild_id = int(request.match_info['guild_id'])
        guild = dashboard.bot.get_guild(guild_id)
        
        if not guild:
            return web.json_response({'success': False, 'error': 'Guild not found'}, status=404)
        
        # Get data from request
        data = await request.json()
        user_id = int(data.get('user_id'))
        days = int(data.get('days') or 0)
        hours = int(data.get('hours') or 0)
        minutes = int(data.get('minutes') or 0)
        reason = data.get('reason')
        
        # Calculate timeout duration
        duration = timedelta(days=days, hours=hours, minutes=minutes)
        
        if duration.total_seconds() == 0:
            return web.json_response({'success': False, 'error': 'Timeout duration cannot be zero'}, status=400)
        
        # Find the member
        member = guild.get_member(user_id)
        if not member:
            return web.json_response({'success': False, 'error': 'Member not found'}, status=404)
        
        # Apply timeout (requires discord.py 2.0+)
        try:
            await member.timeout_for(duration, reason=reason)
            logging.info(f"Timeout applied to {member.name}#{member.discriminator} for {duration} in {guild.name}: {reason}")
            
            return web.json_response({
                'success': True, 
                'case_id': 124  # This would normally be the ID from your database
            })
        except discord.Forbidden:
            return web.json_response({'success': False, 'error': 'Bot lacks permission to timeout this user'}, status=403)
        
    except Exception as e:
        logging.error(f"Error applying timeout: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def handle_ban(request, dashboard):
    """Handle API request to ban a user."""
    session = await get_session(request)
    
    if not session:
        return web.json_response({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        guild_id = int(request.match_info['guild_id'])
        guild = dashboard.bot.get_guild(guild_id)
        
        if not guild:
            return web.json_response({'success': False, 'error': 'Guild not found'}, status=404)
        
        # Get data from request
        data = await request.json()
        user_id = int(data.get('user_id'))
        delete_days = int(data.get('delete_days') or 0)
        reason = data.get('reason')
        
        # Find the member
        member = guild.get_member(user_id)
        if not member:
            return web.json_response({'success': False, 'error': 'Member not found'}, status=404)
        
        # Ban the member
        try:
            await guild.ban(member, delete_message_days=delete_days, reason=reason)
            logging.info(f"Banned {member.name}#{member.discriminator} from {guild.name}: {reason}")
            
            return web.json_response({
                'success': True, 
                'case_id': 125  # This would normally be the ID from your database
            })
        except discord.Forbidden:
            return web.json_response({'success': False, 'error': 'Bot lacks permission to ban this user'}, status=403)
        
    except Exception as e:
        logging.error(f"Error banning user: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def handle_delete_case(request, dashboard):
    """Handle API request to delete a moderation case."""
    session = await get_session(request)
    
    if not session:
        return web.json_response({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        guild_id = int(request.match_info['guild_id'])
        case_id = int(request.match_info['case_id'])
        
        # Here you would delete the case from your database
        # For demo purposes, we'll just log it
        logging.info(f"Deleted case {case_id} from guild {guild_id}")
        
        return web.json_response({'success': True})
    except Exception as e:
        logging.error(f"Error deleting case: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

    
# Moderasyon notlarını getir
def require_login(f):
    async def wrapped(request, *args, **kwargs):
        session = await get_session(request)
        if not session or 'user' not in session:
            return web.json_response({"error": "Unauthorized"}, status=401)
        request['user'] = session['user']
        return await f(request, *args, **kwargs)
    return wrapped

async def validate_guild_access(request, guild_id):
    """Check if user has administrator access to guild"""
    user = request['user']
    guild = request.app['bot'].get_guild(int(guild_id))
    
    if not guild:
        return False
        
    # Check user permissions in guild
    member = guild.get_member(int(user['id']))
    if not member or not member.guild_permissions.administrator:
        return False
        
    return True

@routes.get('/api/guild/{guild_id}/notes/{user_id}')
@require_login
async def get_user_notes(request):
    """Kullanıcı moderasyon notlarını getir"""
    user = request['user']
    guild_id = request.match_info['guild_id']
    user_id = request.match_info['user_id']
    
    # Guild erişim kontrolü
    if not await validate_guild_access(request, guild_id):
        return web.json_response({'error': 'Bu sunucuya erişim izniniz yok'})
    
    # Bot'tan shared_data al
    shared_data = request.app['bot'].shared_data
    
    # Notları yükle
    all_notes = shared_data.load_notes(guild_id)
    
    # Kullanıcı notları
    user_notes = all_notes.get(str(user_id), {})
    
    # Discord'dan kullanıcı bilgilerini al
    try:
        discord_user = await request.app['bot'].fetch_user(int(user_id))
        user_info = {
            'id': str(discord_user.id),
            'username': str(discord_user),
            'avatar_url': str(discord_user.display_avatar.url)
        }
    except:
        user_info = {
            'id': user_id,
            'username': 'Bilinmeyen Kullanıcı',
            'avatar_url': ''
        }
        
    return web.json_response({
        'user': user_info,
        'notes': user_notes
    })

# Not silme API
@routes.post('/api/guild/{guild_id}/notes/delete')
@require_login
async def delete_user_note(request):
    """Moderasyon notu sil"""
    user = request['user']
    guild_id = request.match_info['guild_id']
    
    # Guild erişim kontrolü
    if not await validate_guild_access(request, guild_id):
        return web.json_response({'error': 'Bu sunucuya erişim izniniz yok'})
    
    # JSON verisini al
    try:
        data = await request.json()
        user_id = data['user_id']
        note_type = data['note_type']
        note_id = data['note_id']
    except Exception as e:
        return web.json_response({'error': f'Geçersiz istek verisi: {str(e)}'})
    
    # Bot'tan shared_data al
    shared_data = request.app['bot'].shared_data
    
    # Notu sil
    success = shared_data.remove_note(guild_id, user_id, note_type, note_id)
    
    return web.json_response({
        'success': success
    })
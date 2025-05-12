import discord
from aiohttp import web
import json
from datetime import datetime, timedelta
from .auth import get_session
import logging
import traceback

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
        """Botun bulunduğu sunucuları listeler"""
        session = await get_user_session(request)
        if not session or "user_id" not in session:
            return web.json_response({"error": "Authentication required"}, status=401)
            
        user_id = int(session["user_id"])
        
        # Bot sahibi kontrolü
        is_owner = await self.bot.is_owner(discord.Object(user_id))
        
        guilds = []
        for guild in self.bot.guilds:
            # Eğer kullanıcı bot sahibi değilse, sadece yönetici olduğu sunucuları görebilsin
            if not is_owner:
                member = guild.get_member(user_id)
                if not member or not member.guild_permissions.administrator:
                    continue
                    
            guilds.append({
                "id": guild.id,
                "name": guild.name,
                "icon_url": str(guild.icon.url) if guild.icon else None,
                "member_count": guild.member_count
            })
            
        return web.json_response({"guilds": guilds})
        
    async def get_guild_info(self, request):
        """Belirli bir sunucu hakkında detaylı bilgi verir"""
        guild_id = request.match_info.get("guild_id")
        if not guild_id:
            return web.json_response({"error": "Guild ID is required"}, status=400)
            
        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            return web.json_response({"error": "Guild not found"}, status=404)
            
        # Sunucu hakkında detaylı bilgileri topla
        channels = [{"id": c.id, "name": c.name, "type": str(c.type)} for c in guild.channels]
        roles = [{"id": r.id, "name": r.name, "color": r.color.value} for r in guild.roles]
        
        guild_info = {
            "id": guild.id,
            "name": guild.name,
            "icon_url": str(guild.icon.url) if guild.icon else None,
            "owner": {"id": guild.owner.id, "name": guild.owner.name},
            "created_at": guild.created_at.isoformat(),
            "member_count": guild.member_count,
            "channels": channels,
            "roles": roles
        }
        
        return web.json_response(guild_info)

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
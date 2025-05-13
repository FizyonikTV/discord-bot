import logging
import os
import aiohttp_jinja2
import jinja2
from aiohttp import web
from datetime import datetime
import traceback
import asyncio
import discord
from .auth import get_session

async def setup_routes(app, dashboard):
    """Setup routes for the dashboard."""
    # Setup Jinja2 templates
    aiohttp_jinja2.setup(
        app, 
        loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
    )
    
    # Add routes
    app.router.add_get('/', lambda request: handle_index(request, dashboard))
    app.router.add_get('/dashboard', lambda request: handle_dashboard(request, dashboard))
    app.router.add_get('/guilds', lambda request: handle_guilds(request, dashboard))
    app.router.add_get('/guild/{guild_id}', lambda request: handle_guild_detail(request, dashboard))
    app.router.add_get('/guild/{guild_id}/moderation', lambda request: handle_guild_moderation(request, dashboard))
    
    # Import and setup API routes
    from .api import setup_api_routes
    await setup_api_routes(app, dashboard)
    
    # Error handler
    app.middlewares.append(error_middleware)

@web.middleware
async def error_middleware(request, handler):
    """Middleware to catch and log exceptions."""
    try:
        return await handler(request)
    except web.HTTPException:
        # HTTP exceptions should be handled normally
        raise
    except Exception as ex:
        # Log the exception
        logging.error(f"Unhandled exception in route handler: {ex}")
        logging.error(traceback.format_exc())
        
        # Return a friendly error page
        error_data = {
            'error': str(ex),
            'path': request.path,
        }
        response = aiohttp_jinja2.render_template('error.html', request, error_data)
        response.set_status(500)
        return response

async def handle_index(request, dashboard):
    """Handle the index route."""
    try:
        session = await get_session(request)
        
        # Calculate bot statistics
        bot = dashboard.bot
        guild_count = len(bot.guilds)
        member_count = sum(g.member_count for g in bot.guilds)
        
        # Calculate uptime
        current_time = datetime.utcnow()
        uptime_delta = current_time - bot.start_time.replace(tzinfo=None)
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{days}d {hours}h {minutes}m {seconds}s"
        
        context = {
            'user': session['user'] if session else None,
            'logged_in': session is not None,
            'stats': {
                'guilds': guild_count,
                'members': member_count,
                'uptime': uptime,
                'commands': len(bot.commands)
            }
        }
        
        return aiohttp_jinja2.render_template('index.html', request, context)
    except Exception as e:
        logging.error(f"Error rendering index page: {e}")
        logging.error(traceback.format_exc())
        return web.Response(text=f"Error rendering index page: {str(e)}", status=500)

async def handle_dashboard(request, dashboard):
    """Handle the dashboard route."""
    try:
        session = await get_session(request)
        
        if not session:
            return web.HTTPFound('/login')
        
        # Calculate bot uptime
        uptime_delta = datetime.utcnow() - dashboard.bot.start_time.replace(tzinfo=None)
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{days}d {hours}h {minutes}m {seconds}s"
        
        # Get bot statistics
        bot = dashboard.bot
        bot_status = "Online" if bot.is_ready() else "Starting up..."
        guild_count = len(bot.guilds)
        member_count = sum(g.member_count for g in bot.guilds)
        command_count = len(bot.commands)
        
        # For demo purposes - would be replaced with actual metrics
        import random
        cpu_percent = random.randint(15, 45)
        ram_percent = random.randint(20, 60)
        
        context = {
            'user': session['user'],
            'bot_status': bot_status,
            'uptime': uptime,
            'guild_count': guild_count,
            'member_count': member_count,
            'command_count': command_count,
            'cpu_percent': cpu_percent,
            'ram_percent': ram_percent
        }
        
        response = aiohttp_jinja2.render_template('dashboard.html', request, context)
        return response
    except Exception as e:
        logging.error(f"Error rendering dashboard page: {e}")
        logging.error(traceback.format_exc())
        return web.Response(text=f"Error rendering dashboard page: {str(e)}", status=500)

async def handle_guilds(request, dashboard):
    """Handle the guilds route."""
    try:
        session = await get_session(request)
        
        if not session:
            return web.HTTPFound('/login')
        
        # Filter only the guilds where the bot is present
        bot_guild_ids = {guild.id for guild in dashboard.bot.guilds}
        user_guilds = session['guilds']
        common_guilds = []
        
        for guild_data in user_guilds:
            guild_id = int(guild_data['id'])
            if guild_id in bot_guild_ids:
                bot_guild = dashboard.bot.get_guild(guild_id)
                if bot_guild:
                    guild_data['member_count'] = bot_guild.member_count
                    guild_data['icon_url'] = str(bot_guild.icon.url) if bot_guild.icon else "https://cdn.discordapp.com/embed/avatars/0.png"
                    common_guilds.append(guild_data)
        
        context = {
            'user': session['user'],
            'guilds': common_guilds,
        }
        
        response = aiohttp_jinja2.render_template('guild.html', request, context)
        return response
    except Exception as e:
        logging.error(f"Error rendering guilds page: {e}")
        logging.error(traceback.format_exc())
        return web.Response(text=f"Error rendering guilds page: {str(e)}", status=500)

async def handle_guild_detail(request, dashboard):
    """Handle the guild detail route."""
    try:
        session = await get_session(request)
        
        if not session:
            return web.HTTPFound('/login')
        
        guild_id = int(request.match_info['guild_id'])
        guild = dashboard.bot.get_guild(guild_id)
        
        if not guild:
            return web.Response(text='Guild not found', status=404)
        
        # Get guild statistics
        member_count = guild.member_count
        bot_count = len([m for m in guild.members if m.bot])
        human_count = member_count - bot_count
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        
        context = {
            'user': session['user'],
            'guild': {
                'id': guild.id,
                'name': guild.name,
                'icon_url': str(guild.icon.url) if guild.icon else "https://cdn.discordapp.com/embed/avatars/0.png",
                'member_count': member_count,
                'bot_count': bot_count,
                'human_count': human_count,
                'text_channels': text_channels,
                'voice_channels': voice_channels,
            }
        }
        
        response = aiohttp_jinja2.render_template('guild_detail.html', request, context)
        return response
    except Exception as e:
        logging.error(f"Error rendering guild detail page: {e}")
        logging.error(traceback.format_exc())
        return web.Response(text=f"Error rendering guild detail page: {str(e)}", status=500)

async def handle_guild_moderation(request, dashboard):
    """Handle the guild moderation route."""
    try:
        session = await get_session(request)
        
        if not session:
            return web.HTTPFound('/login')
        
        guild_id = int(request.match_info['guild_id'])
        guild = dashboard.bot.get_guild(guild_id)
        
        if not guild:
            return web.Response(text='Guild not found', status=404)
        
        # Generate sample moderation cases for demonstration
        # In a real implementation, these would come from a database
        import random
        from datetime import datetime, timedelta
        
        mod_cases = []
        case_types = ['Warning', 'Timeout', 'Ban']
        
        # Sample moderator names
        moderator_names = ["Admin", "Moderator", "Staff"]
        
        # Sample reasons
        reasons = [
            "Inappropriate language", 
            "Spamming", 
            "Harassment", 
            "Advertising", 
            "NSFW content",
            "Off-topic posting"
        ]
        
        for i in range(1, 21):
            # Create a sample user avatar URL
            user_avatar = f"https://cdn.discordapp.com/embed/avatars/{random.randint(0, 4)}.png"
            
            # Create random date within the last 30 days
            days_ago = random.randint(0, 30)
            case_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M")
            
            case_type = random.choice(case_types)
            
            mod_cases.append({
                'id': i,
                'type': case_type,
                'username': f'User{random.randint(1000, 9999)}',
                'user_id': f'{random.randint(100000000000000000, 999999999999999999)}',
                'user_avatar': user_avatar,
                'moderator': random.choice(moderator_names),
                'reason': random.choice(reasons),
                'date': case_date
            })
        
        # Sort cases by ID (newest first)
        mod_cases.sort(key=lambda x: x['id'], reverse=True)
        
        # Get the guild members (limited to a sample size for demo)
        members = []
        for member in list(guild.members)[:50]:  # Limit to 50 members for performance
            members.append({
                'id': member.id,
                'name': member.name,
                'discriminator': member.discriminator if hasattr(member, 'discriminator') else '0000',
                'avatar_url': str(member.avatar.url) if member.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
            })
        
        context = {
            'user': session['user'],
            'guild': {
                'id': guild.id,
                'name': guild.name,
                'icon_url': str(guild.icon.url) if guild.icon else "https://cdn.discordapp.com/embed/avatars/0.png"
            },
            'mod_cases': mod_cases,
            'members': members
        }
        
        response = aiohttp_jinja2.render_template('moderation.html', request, context)
        return response
    except Exception as e:
        logging.error(f"Error rendering guild moderation page: {e}")
        logging.error(traceback.format_exc())
        return web.Response(text=f"Error rendering guild moderation page: {str(e)}", status=500)
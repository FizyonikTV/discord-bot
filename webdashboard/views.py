import aiohttp_jinja2
from aiohttp import web
import discord
from webdashboard.auth import get_user_from_token, create_jwt_token, require_login

@aiohttp_jinja2.template('index.html')
async def index(request):
    """Ana sayfa"""
    user = get_user_from_token(request)
    bot_stats = {
        "user_count": sum(g.member_count for g in request.app['bot'].guilds),
        "command_count": 0
    }
    return {
        'user': user,
        'bot': request.app['bot'].user,
        'bot_stats': bot_stats
    }

@aiohttp_jinja2.template('dashboard.html')
@require_login
async def dashboard(request):
    """Kullanıcı dashboard'u"""
    user = request['user']
    
    # Basit versiyon - gerçekte API'den veri çekersiniz
    guilds = []
    for guild in request.app['bot'].guilds:
        member = guild.get_member(int(user['user_id']))
        if member and member.guild_permissions.administrator:
            guilds.append({
                "id": guild.id,
                "name": guild.name,
                "icon_url": str(guild.icon.url) if guild.icon else None,
                "member_count": guild.member_count,
                "bot_in_guild": True
            })
    
    return {
        'user': user,
        'guilds': guilds,
        'bot': request.app['bot'].user
    }

@aiohttp_jinja2.template('server.html')
@require_login
async def server_view(request):
    """Sunucu yönetim sayfası"""
    user = request['user']
    guild_id = request.match_info['guild_id']
    
    guild = request.app['bot'].get_guild(int(guild_id))
    if not guild:
        raise web.HTTPFound('/dashboard')
    
    # Kullanıcının bu sunucuda admin yetkisi var mı kontrol et
    member = guild.get_member(int(user['user_id']))
    if not member or not member.guild_permissions.administrator:
        raise web.HTTPFound('/dashboard')
    
    guild_data = {
        "id": guild.id,
        "name": guild.name,
        "icon_url": str(guild.icon.url) if guild.icon else None,
        "member_count": guild.member_count,
        "channels": [{"id": c.id, "name": c.name, "type": str(c.type)} for c in guild.channels],
        "roles": [{"id": r.id, "name": r.name} for r in guild.roles]
    }
    
    return {
        'user': user,
        'guild': guild_data,
        'bot': request.app['bot'].user
    }

async def login(request):
    """Login sayfası - OAuth'a yönlendirir"""
    oauth = request.app['oauth']
    auth_url = oauth.get_authorize_url()
    raise web.HTTPFound(auth_url)

async def callback(request):
    """OAuth callback"""
    try:
        oauth = request.app['oauth']
        code = request.query.get('code')
        
        if not code:
            raise web.HTTPFound('/')
        
        token_data, user_data = await oauth.get_token(code)
        
        # JWT token oluştur
        token = create_jwt_token(request, user_data, token_data)
        
        # Cookie'de sakla
        response = web.HTTPFound('/dashboard')
        response.set_cookie('auth', token, httponly=True, max_age=3600*24)
        
        return response
    except Exception as e:
        print(f"OAuth hatası: {e}")
        raise web.HTTPFound('/')

async def logout(request):
    """Çıkış işlemi"""
    response = web.HTTPFound('/')
    response.del_cookie('auth')
    return response
import datetime
import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session
import aiohttp
import json
from urllib.parse import urlencode
from datetime import datetime, timedelta
import functools

# Yardımcı fonksiyon - giriş gerektiren sayfalar için
def require_login(func):
    """Decorator to require login for a view"""
    @functools.wraps(func)
    async def wrapper(request):
        session = await get_session(request)
        user = session.get('user')
        if not user:
            return web.HTTPFound('/login')
        request['user'] = user
        return await func(request)
    return wrapper

# Ana sayfa
@aiohttp_jinja2.template('index.html')
async def index_view(request):
    """Index page view"""
    session = await get_session(request)
    user = session.get('user')
    
    return {'user': user}

# Giriş sayfası
async def login_view(request):
    """Login view - redirects to Discord OAuth2"""
    client_id = request.app['client_id']
    redirect_uri = request.app['redirect_uri']
    
    # OAuth2 parametreleri
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'identify guilds'
    }
    
    # Discord OAuth2 URL'sine yönlendir
    url = f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"
    return web.HTTPFound(url)

# OAuth2 geri çağrı
async def callback_view(request):
    """Callback for Discord OAuth2"""
    code = request.query.get('code')
    if not code:
        return web.HTTPFound('/')
    
    client_id = request.app['client_id']
    client_secret = request.app['client_secret']
    redirect_uri = request.app['redirect_uri']
    
    # Token alma isteği
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post('https://discord.com/api/oauth2/token', data=data) as resp:
            if resp.status != 200:
                return web.HTTPFound('/')
            
            token_data = await resp.json()
            access_token = token_data['access_token']
            
            # Kullanıcı bilgilerini al
            headers = {'Authorization': f"Bearer {access_token}"}
            
            # Kullanıcı kimliği
            async with session.get('https://discord.com/api/users/@me', headers=headers) as resp:
                if resp.status != 200:
                    return web.HTTPFound('/')
                user_data = await resp.json()
            
            # Sunucu listesi
            async with session.get('https://discord.com/api/users/@me/guilds', headers=headers) as resp:
                if resp.status != 200:
                    return web.HTTPFound('/')
                guilds_data = await resp.json()
            
            # Sadece bot'un da olduğu sunucuları filtrele
            bot_guild_ids = [guild.id for guild in request.app['bot'].guilds]
            guilds = [g for g in guilds_data if g['id'] in map(str, bot_guild_ids)]
            
            # Oturum oluştur
            req_session = await get_session(request)
            req_session['user'] = {
                'id': user_data['id'],
                'username': user_data['username'],
                'avatar': user_data['avatar'],
                'discriminator': user_data.get('discriminator', '0000'),
                'guilds': guilds,
                'access_token': access_token
            }
            
            return web.HTTPFound('/dashboard')

# Dashboard sayfası
@aiohttp_jinja2.template('dashboard.html')
@require_login
async def dashboard_view(request):
    """Dashboard page view"""
    user = request['user']
    bot = request.app['bot']
    
    # Kullanıcının yetkili olduğu sunucular
    guilds = user['guilds']
    
    # Bot istatistikleri
    bot_stats = {
        'user_count': sum(g.member_count for g in bot.guilds if hasattr(g, 'member_count')),
        'command_count': getattr(bot, 'command_count', 0),
        'uptime': 'N/A',
        'recent_activities': []
    }
    
    return {
        'user': user,
        'bot': bot,
        'guilds': guilds,
        'bot_stats': bot_stats
    }

# Çıkış
async def logout_view(request):
    """Logout view - clears session"""
    session = await get_session(request)
    session.clear()
    return web.HTTPFound('/')

# Sunucu sayfası
@aiohttp_jinja2.template('server.html')
@require_login
async def server_view(request):
    """Server configuration page"""
    user = request['user']
    guild_id = request.match_info['guild_id']
    
    # Sunucu kimliğini doğrula
    bot = request.app['bot']
    guild = bot.get_guild(int(guild_id))
    
    if not guild:
        return web.HTTPFound('/dashboard')
    
    # Kullanıcının yönetici yetkisini kontrol et
    user_guilds = user['guilds']
    user_perm = False
    
    for g in user_guilds:
        if g['id'] == guild_id:
            # 0x8 = 0b1000 = Administrator permission
            if (int(g['permissions']) & 0x8) == 0x8:
                user_perm = True
                break
    
    if not user_perm:
        return web.HTTPFound('/dashboard')
    
    # Sunucu bilgilerini topla
    text_channels = [c for c in guild.channels if hasattr(c, 'topic')]
    roles = guild.roles
    
    return {
        'user': user,
        'guild': guild,
        'text_channels': text_channels,
        'roles': roles
    }
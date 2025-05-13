import functools
import aiohttp
from aiohttp import web
import discord
import json
import secrets
import asyncio
import logging
import jwt
import time
from urllib.parse import urlencode
from aiohttp_session import get_session

# Store active sessions
sessions = {}

class DiscordOAuth:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = "identify guilds"
        self.discord_api = "https://discord.com/api/v10"
        
    def get_authorize_url(self):
        return f"{self.discord_api}/oauth2/authorize?client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type=code&scope={self.scope}"
        
    async def get_token(self, code):
        async with aiohttp.ClientSession() as session:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.redirect_uri,
                'scope': self.scope
            }
            
            async with session.post(f"{self.discord_api}/oauth2/token", data=data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Invalid response {resp.status}: {text}")
                token_data = await resp.json()
                
            # Token'la kullanıcı bilgilerini al
            headers = {'Authorization': f"Bearer {token_data['access_token']}"}
            async with session.get(f"{self.discord_api}/users/@me", headers=headers) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to get user data {resp.status}")
                user_data = await resp.json()
                
            return token_data, user_data

def setup_oauth(app, client_id, client_secret, redirect_uri):
    app['oauth'] = DiscordOAuth(client_id, client_secret, redirect_uri)

def create_jwt_token(request, user_data, token_data):
    """JWT token oluştur"""
    payload = {
        'user_id': user_data['id'],
        'username': user_data['username'],
        'avatar': user_data.get('avatar'),
        'access_token': token_data['access_token'],
        'exp': int(time.time()) + 3600 * 24  # 1 gün geçerli
    }
    
    token = jwt.encode(payload, request.app['jwt_secret'], algorithm='HS256')
    return token

def get_user_from_token(request):
    """Cookie'den JWT tokenı çıkar ve doğrula"""
    try:
        token = request.cookies.get('auth')
        if not token:
            return None
        
        payload = jwt.decode(token, request.app['jwt_secret'], algorithms=['HS256'])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def require_login(func):
    """Login gerektiren sayfalar için dekoratör"""
    async def wrapper(request):
        user = get_user_from_token(request)
        if not user:
            raise web.HTTPFound('/login')
        request['user'] = user
        return await func(request)
    return wrapper

async def new_session(request):
    session = await request.session()
    session.clear()
    return session

async def handle_login(request):
    """Handle Discord OAuth2 login."""
    oauth = request.app['oauth']
    state = secrets.token_urlsafe(32)
    response = web.HTTPFound(oauth.get_authorize_url())
    response.set_cookie('discord_oauth_state', state, httponly=True)
    return response

async def handle_callback(request):
    """Handle the OAuth2 callback from Discord."""
    oauth = request.app['oauth']
    state = request.cookies.get('discord_oauth_state')
    if not state or state != request.query.get('state'):
        return web.Response(text='Authentication failed: Invalid state', status=400)
    
    code = request.query.get('code')
    if not code:
        return web.Response(text='Authentication failed: No code provided', status=400)
    
    try:
        token_data, user_data = await oauth.get_token(code)
        token = create_jwt_token(request, user_data, token_data)
        response = web.HTTPFound('/dashboard')
        response.set_cookie('auth', token, httponly=True)
        return response
    except Exception as e:
        logging.error(f"Auth error: {e}")
        return web.Response(text=f'Authentication error: {str(e)}', status=500)

async def handle_logout(request):
    """Handle user logout."""
    response = web.HTTPFound('/')
    response.del_cookie('auth')
    return response

def setup_auth_routes(app):
    """Setup authentication routes for the app."""
    app.router.add_get('/login', handle_login)
    app.router.add_get('/callback', handle_callback)
    app.router.add_get('/logout', handle_logout)
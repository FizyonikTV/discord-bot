import aiohttp
from aiohttp import web
import json
import secrets
import asyncio
import logging
from urllib.parse import urlencode

# Store active sessions
sessions = {}

class DiscordOAuth:
    def __init__(self, client_id, client_secret, redirect_uri, host, port):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.host = host
        self.port = port
        self.session = aiohttp.ClientSession()

def setup_auth_routes(app, dashboard):
    """Setup authentication routes for the dashboard."""
    app.router.add_get('/login', lambda request: handle_login(request, dashboard))
    app.router.add_get('/callback', lambda request: handle_callback(request, dashboard))
    app.router.add_get('/logout', handle_logout)

async def handle_login(request, dashboard):
    """Handle Discord OAuth2 login."""
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Create the authorization URL
    params = {
        'client_id': dashboard.client_id,
        'redirect_uri': f"http://{dashboard.host}:{dashboard.port}/callback",
        'response_type': 'code',
        'scope': 'identify guilds',
        'state': state
    }
    
    # Store the state in a cookie for verification
    response = web.HTTPFound(f"https://discord.com/api/oauth2/authorize?{urlencode(params)}")
    response.set_cookie('discord_oauth_state', state, httponly=True)
    
    return response

async def handle_callback(request, dashboard):
    """Handle the OAuth2 callback from Discord."""
    # Verify the state to prevent CSRF attacks
    state = request.cookies.get('discord_oauth_state')
    if not state or state != request.query.get('state'):
        return web.Response(text='Authentication failed: Invalid state', status=400)
    
    # Get the code from the request
    code = request.query.get('code')
    if not code:
        return web.Response(text='Authentication failed: No code provided', status=400)
    
    try:
        # Exchange code for token
        token_url = "https://discord.com/api/oauth2/token"
        token_data = {
            'client_id': dashboard.client_id,
            'client_secret': dashboard.client_secret,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': f"http://{dashboard.host}:{dashboard.port}/callback",
            'scope': 'identify guilds'
        }
        
        # Timeout süresini artıralım ve rate limit için yeniden deneme mekanizması ekleyelim
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                async with dashboard.session.post(token_url, data=token_data, timeout=30) as response:
                    if response.status == 429:  # Rate limit
                        retry_after = int(response.headers.get('Retry-After', 5))
                        await asyncio.sleep(retry_after)
                        retry_count += 1
                        continue
                        
                    if response.status != 200:
                        error_text = await response.text()
                        logging.error(f"Token exchange failed: {response.status} - {error_text}")
                        return web.Response(text=f'Authentication failed: {response.status}', status=500)
                    
                    token_response = await response.json()
                    break
            except asyncio.TimeoutError:
                retry_count += 1
                if retry_count >= max_retries:
                    return web.Response(text='Authentication failed: Discord API timeout', status=500)
                await asyncio.sleep(1)
        else:
            return web.Response(text='Authentication failed: Maximum retries reached', status=500)
        
        access_token = token_response['access_token']
        
        # User bilgilerini çekerken de benzer hata işleme ekleyelim
        try:
            # Get user info
            user_url = "https://discord.com/api/users/@me"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with dashboard.session.get(user_url, headers=headers, timeout=30) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logging.error(f"Failed to get user data: {response.status} - {error_text}")
                    return web.Response(text='Authentication failed: Could not retrieve user data', status=500)
                user_data = await response.json()
            
            # Get user's guilds
            guilds_url = "https://discord.com/api/users/@me/guilds"
            
            async with dashboard.session.get(guilds_url, headers=headers, timeout=30) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logging.error(f"Failed to get guilds: {response.status} - {error_text}")
                    return web.Response(text='Authentication failed: Could not retrieve guilds', status=500)
                guilds_data = await response.json()
            
            # Create a session
            session_id = secrets.token_urlsafe(32)
            sessions[session_id] = {
                'user': user_data,
                'guilds': guilds_data,
                'access_token': access_token
            }
            
            # Redirect to the dashboard
            response = web.HTTPFound('/dashboard')
            response.set_cookie('session_id', session_id, httponly=True)
            
            return response
            
        except Exception as e:
            logging.error(f"Auth error: {e}")
            return web.Response(text=f'Authentication error: {str(e)}', status=500)
    except Exception as e:
        logging.error(f"Auth error: {e}")
        return web.Response(text=f'Authentication error: {str(e)}', status=500)

async def handle_logout(request):
    """Handle user logout."""
    session_id = request.cookies.get('session_id')
    
    if session_id and session_id in sessions:
        del sessions[session_id]
    
    response = web.HTTPFound('/')
    response.del_cookie('session_id')
    
    return response

async def get_session(request):
    """Get the current session data."""
    session_id = request.cookies.get('session_id')
    
    if not session_id or session_id not in sessions:
        return None
    
    return sessions[session_id]
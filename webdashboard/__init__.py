import logging
import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2
import os
from aiohttp_session import setup as setup_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
import base64
from cryptography import fernet

class Dashboard:
    """Discord bot web dashboard."""
    
    def __init__(self, bot, client_id, client_secret, base_url="http://localhost", port=8080, redirect_uri=None):
        self.bot = bot
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.port = port
        self.redirect_uri = redirect_uri or f"{base_url}:{port}/callback"
        self.app = web.Application()
        
    async def start(self):
        """Start the web server."""
        try:
            # Setup app
            self.app["bot"] = self.bot
            self.app["client_id"] = self.client_id
            self.app["client_secret"] = self.client_secret
            self.app["redirect_uri"] = self.redirect_uri

            # Session setup
            fernet_key = fernet.Fernet.generate_key()
            secret_key = base64.urlsafe_b64decode(fernet_key)
            setup_session(self.app, EncryptedCookieStorage(secret_key))

            # Templates
            templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
            aiohttp_jinja2.setup(self.app, loader=jinja2.FileSystemLoader(templates_dir))

            # Static files
            static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
            self.app.router.add_static('/static/', static_dir, name='static')

            # Set up routes
            from .routes import setup_routes
            setup_routes(self.app, self.bot, self.client_id, self.client_secret, self.redirect_uri)

            # Start the web server
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, '0.0.0.0', self.port)
            await self.site.start()
            
            print(f"[OK] Dashboard running at http://localhost:{self.port}")
            return True
        except Exception as e:
            logging.error(f"Dashboard başlatılamadı: {e}")
            logging.exception(e)
            print(f"[NO] Dashboard başlatılamadı: {e}")
            return False
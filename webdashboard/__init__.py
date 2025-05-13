import logging
import aiohttp
from aiohttp import web
import asyncio
import os
import jinja2
import aiohttp_jinja2
import jwt
import time
import secrets

class Dashboard:
    def __init__(self, bot, client_id, client_secret, base_url="http://localhost", port=8080):
        self.bot = bot
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.port = port
        self.redirect_uri = f"{base_url}:{port}/callback"
        # JWT için gizli anahtar
        self.jwt_secret = secrets.token_hex(32)
        self.app = web.Application()
        self.setup_app()
        
    def setup_app(self):
        # Static dosyalar için klasör tanımla
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        self.app.router.add_static('/static/', path=static_dir, name='static')
        
        # Template sistemi kurulumu
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)
        aiohttp_jinja2.setup(
            self.app,
            loader=jinja2.FileSystemLoader(template_dir)
        )
        
        # JWT gizli anahtarını app'e ekle
        self.app['jwt_secret'] = self.jwt_secret
        
        # Bot referansını app'e ekle
        self.app['bot'] = self.bot
        
        # Route'ları yükle
        from webdashboard.routes import setup_routes
        setup_routes(self.app, self.bot, self.client_id, self.client_secret, self.redirect_uri)
        
        print("✅ Dashboard kurulumu tamamlandı")

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        self.site = web.TCPSite(runner, 'localhost', self.port)
        await self.site.start()
        logging.info(f"✅ Dashboard started at http://localhost:{self.port}")
        print(f"✅ Web panel başlatıldı: http://localhost:{self.port}")
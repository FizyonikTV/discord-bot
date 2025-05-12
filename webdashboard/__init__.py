import asyncio
import aiohttp
from aiohttp import web
import discord
import logging
import jinja2
import aiohttp_jinja2
import os

class Dashboard:
    def __init__(self, bot, client_id, client_secret, host="0.0.0.0", port=8080):
        """Initialize the dashboard with the bot instance and configuration."""
        self.bot = bot
        self.client_id = client_id
        self.client_secret = client_secret
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.session = None
        
    async def start(self):
        """Start the dashboard web server."""
        try:
            # Create session
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
            
            # Setup Jinja2 templates
            aiohttp_jinja2.setup(
                self.app, 
                loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates'))
            )
            
            # Setup static routes for CSS, JS, etc.
            static_path = os.path.join(os.path.dirname(__file__), 'static')
            if os.path.exists(static_path):
                self.app.router.add_static('/static/', path=static_path, name='static')
            else:
                logging.warning(f"Static directory does not exist: {static_path}")
            
            # Import route setup functions
            from .auth import setup_auth_routes
            from .routes import setup_routes
            from .api import setup_api_routes
            
            # Setup routes
            setup_auth_routes(self.app, self)
            setup_routes(self.app, self)
            setup_api_routes(self.app, self)
            
            # Start the web server
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            
            logging.info(f"✅ Dashboard started on http://{self.host}:{self.port}")
            print(f"✅ Dashboard started on http://{self.host}:{self.port}")
        except Exception as e:
            logging.error(f"Failed to start dashboard: {e}")
            print(f"❌ Failed to start dashboard: {e}")
    
    async def stop(self):
        """Stop the dashboard web server."""
        if self.runner:
            await self.runner.cleanup()
        if self.session:
            await self.session.close()
        logging.info("Dashboard stopped")
import logging
import os
import aiohttp_jinja2
import jinja2
from aiohttp import web
from datetime import datetime
import traceback
import asyncio
import discord
from webdashboard.auth import setup_oauth
from .middlewares import error_middleware
from .views import index_view, login_view, callback_view, dashboard_view, logout_view, server_view
from .api import API

def setup_routes(app, bot, client_id, client_secret, redirect_uri):
    """Set up web routes"""
    # OAuth ayarları
    setup_oauth(app, client_id, client_secret, redirect_uri)
    
    # Middleware'i ekleyin
    app.middlewares.append(error_middleware)
    
    # Diğer middlewareleri buraya ekleyin
    # ...
    
    # Ana sayfalar
    app.router.add_get('/', index_view, name='index')
    app.router.add_get('/login', login_view, name='login')
    app.router.add_get('/callback', callback_view, name='callback')
    app.router.add_get('/dashboard', dashboard_view, name='dashboard')
    app.router.add_get('/logout', logout_view, name='logout')
    app.router.add_get('/server/{guild_id}', server_view, name='server')
    
    # API Endpoint'leri
    api = API(bot)
    
    # Basic guild info endpoints
    app.router.add_get('/api/guilds', api.get_guilds)
    app.router.add_get('/api/guild/{guild_id}', api.get_guild)
    
    # Settings endpoints
    app.router.add_get('/api/guild/{guild_id}/settings', api.get_settings)
    app.router.add_post('/api/guild/{guild_id}/settings', api.update_settings)
    
    # Error reporting endpoint
    app.router.add_post('/api/error-report', api.report_error)
    
    # Diğer API endpointleri buraya eklenebilir
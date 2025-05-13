import logging
import os
import aiohttp_jinja2
import jinja2
from aiohttp import web
from datetime import datetime
import traceback
import asyncio
import discord
from webdashboard.api import BotAPI
from webdashboard.views import index, dashboard, login, callback, logout, server_view
from webdashboard.auth import setup_oauth

def setup_routes(app, bot, client_id, client_secret, redirect_uri):
    # OAuth ayarları
    setup_oauth(app, client_id, client_secret, redirect_uri)
    
    # API
    api = BotAPI(bot)
    
    # Ana sayfalar
    app.router.add_get('/', index, name='index')
    app.router.add_get('/login', login, name='login')
    app.router.add_get('/callback', callback, name='callback')
    app.router.add_get('/logout', logout, name='logout')
    app.router.add_get('/dashboard', dashboard, name='dashboard')
    app.router.add_get('/server/{guild_id}', server_view, name='server')
    
    # API Endpoint'leri
    app.router.add_get('/api/guilds', api.get_guilds, name='api_guilds')
    app.router.add_get('/api/guild/{guild_id}', api.get_guild_info, name='api_guild')
    app.router.add_post('/api/guild/{guild_id}/settings', api.update_guild_settings, name='api_update_guild')
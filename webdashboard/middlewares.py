from aiohttp import web
import time
import logging
import traceback
import sys

logger = logging.getLogger('dashboard')

@web.middleware
async def timing_middleware(request, handler):
    """İstek sürelerini ölçer."""
    start_time = time.time()
    response = await handler(request)
    end_time = time.time()
    
    # İstek süresi başlığı ekle
    response.headers['X-Process-Time'] = f"{(end_time - start_time):.3f} sec"
    return response

@web.middleware
async def error_middleware(request, handler):
    """Global hata yakalama middleware'i."""
    try:
        return await handler(request)
    except web.HTTPException as ex:
        # HTTP hataları için normal davranış
        raise
    except Exception as e:
        # Beklenmeyen hatalar için
        logger.error(f"Beklenmeyen hata: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Kullanıcıya güzel bir hata sayfası göster
        return web.HTTPInternalServerError(
            text=f"""
            <html>
                <head>
                    <title>500 Internal Server Error</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; padding: 20px; text-align: center; }}
                        h1 {{ color: #d9534f; }}
                        .container {{ max-width: 800px; margin: 0 auto; }}
                        .error-details {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; text-align: left; }}
                        pre {{ overflow: auto; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>500 Internal Server Error</h1>
                        <p>Sunucuda bir hata oluştu. Yönetici log dosyalarını kontrol etmelidir.</p>
                        <div class="error-details">
                            <h3>Hata Detayı:</h3>
                            <pre>{str(e)}</pre>
                        </div>
                        <p><a href="/">Ana sayfaya dön</a></p>
                    </div>
                </body>
            </html>
            """, 
            content_type="text/html"
        )

@web.middleware
async def csrf_middleware(request, handler):
    """CSRF koruması için middleware"""
    # GET istekleri için CSRF gerektirme
    if request.method == "GET":
        return await handler(request)
    
    # API istekleri için özel Origin ve Referer kontrolü
    if request.path.startswith('/api/'):
        origin = request.headers.get('Origin', '')
        referer = request.headers.get('Referer', '')
        
        # Host'u kontrol et
        host = request.headers.get('Host', '')
        
        # Bu örnekte basit bir kontrol yapıyoruz
        # Daha gelişmiş kontrollerle değiştirilebilir
        if origin and not (origin.endswith(host) or 'localhost' in origin):
            return web.json_response({"error": "CSRF check failed"}, status=403)
        
        if referer and not (host in referer or 'localhost' in referer):
            return web.json_response({"error": "CSRF check failed"}, status=403)
    
    return await handler(request)

def setup_middlewares(app, bot):
    """Middleware'leri ayarlar."""
    app.middlewares.append(timing_middleware)
    app.middlewares.append(error_middleware)
    app.middlewares.append(csrf_middleware)
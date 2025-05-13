from aiohttp import web
import time

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
    """Hata yönetimi."""
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception as e:
        print(f"Dashboard error: {e}")
        return web.HTTPInternalServerError(text=str(e))

def setup_middlewares(app, bot):
    """Middleware'leri ayarlar."""
    app.middlewares.append(timing_middleware)
    app.middlewares.append(error_middleware)
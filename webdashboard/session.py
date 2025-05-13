import base64
import os
import aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet

def setup_session(app):
    """Session yapılandırması."""
    # Gizli anahtar oluştur veya var olanı kullan
    secret_key_file = os.path.join(os.path.dirname(__file__), 'secret_key.txt')
    if os.path.exists(secret_key_file):
        with open(secret_key_file, 'rb') as f:
            secret_key = f.read()
    else:
        # Yeni bir gizli anahtar oluştur
        fernet_key = fernet.Fernet.generate_key()
        secret_key = base64.urlsafe_b64decode(fernet_key)
        
        # Anahtarı dosyaya kaydet
        with open(secret_key_file, 'wb') as f:
            f.write(secret_key)
            
    # Session storage ayarla
    storage = EncryptedCookieStorage(secret_key, max_age=3600*24*7)  # 1 hafta
    aiohttp_session.setup(app, storage)
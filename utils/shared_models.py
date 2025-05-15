import json
import os
from datetime import datetime
from utils.json_handler import JsonHandler

class SharedDataManager:
    """Discord bot ve dashboard arasında paylaşılan verileri yönetir"""
    
    def __init__(self, bot=None):
        self.bot = bot
        self.notes_file = "data/notes.json"
    
    def add_note(self, guild_id, user_id, note_type, reason, moderator_id, moderator_name, duration=None):
        """Moderasyon notu ekler ve json formatında kaydeder"""
        # Notes.json dosyasını yükle
        notes_data = JsonHandler.load_json(self.notes_file, default={})
        
        # Kullanıcı ID'sini string'e dönüştür (JSON uyumluluğu için)
        user_id = str(user_id)
        moderator_id = str(moderator_id)
        
        # Kullanıcı için boş sözlük oluştur
        if user_id not in notes_data:
            notes_data[user_id] = {}
        
        # Not tipi için boş liste oluştur
        if note_type not in notes_data[user_id]:
            notes_data[user_id][note_type] = []
        
        # Yeni not ekle
        new_note = {
            "sebep": reason,
            "moderator": moderator_name,
            "moderator_id": moderator_id,
            "tarih": datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        
        # Timeout için süre ekle
        if duration and note_type == "TIMEOUTLAR":
            new_note["süre"] = duration
        
        # Notu ekle ve kaydet
        notes_data[user_id][note_type].append(new_note)
        JsonHandler.save_json(self.notes_file, notes_data)
        
        print(f"[NOTES] '{user_id}' kullanıcısına '{note_type}' tipinde not eklendi: {reason}")
        return new_note
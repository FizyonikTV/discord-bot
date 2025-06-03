import json
import os
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

class NoteManager:
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NoteManager, cls).__new__(cls)
            cls._instance.notes = {}
            cls._instance.initialized = False
            cls._instance._listeners = []
            cls._instance._saving = False
            cls._instance._load()
        return cls._instance
    
    def __init__(self, bot):
        self.bot = bot
        self.note_manager = NoteManager()

    def _load(self):
        """Notları dosyadan yükle"""
        try:
            if os.path.exists("data/notes.json"):
                with open("data/notes.json", "r", encoding="utf-8") as f:
                    self.notes = json.load(f)
            self.initialized = True
        except Exception as e:
            print(f"Notları yüklerken hata: {e}")
            self.notes = {}
    
    async def save(self):
        """Notları dosyaya kaydet"""
        if not self.initialized:
            return
            
        async with self._lock:
            if self._saving:
                return
                
            self._saving = True
            try:
                # Dizinin mevcut olduğundan emin olun
                os.makedirs("data", exist_ok=True)
                
                # Dosyaya kaydet
                with open("data/notes.json", "w", encoding="utf-8") as f:
                    json.dump(self.notes, f, ensure_ascii=False, indent=4)

                # Dinleyicileri bilgilendir
                for listener in self._listeners:
                    try:
                        await listener(self.notes)
                    except Exception as e:
                        print(f"Dinleyici bilgilendirilirken hata: {e}")
            finally:
                self._saving = False
    
    def register_change_listener(self, callback):
        """Not değişiklikleri için bir geri çağırma kaydet"""
        if callback not in self._listeners:
            self._listeners.append(callback)
    
    def unregister_change_listener(self, callback):
        """Not değişiklikleri için bir geri çağırmayı kaydet"""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def get_user_notes(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Bir kullanıcı için tüm notları al"""
        return self.notes.get(str(user_id), {"UYARILAR": [], "TIMEOUTLAR": [], "BANLAR": []})
    
    async def add_note(self, user_id: int, note_type: str, reason: str, moderator: str, moderator_id: int):
        """Bir kullanıcıya not ekle"""
        user_id_str = str(user_id)

        # Kullanıcı girişi yoksa başlat
        if user_id_str not in self.notes:
            self.notes[user_id_str] = {"UYARILAR": [], "TIMEOUTLAR": [], "BANLAR": []}

        # Notu oluştur
        note_data = {
            "sebep": reason,
            "moderator": moderator,
            "moderator_id": moderator_id,
            "tarih": datetime.now().strftime("%d.%m.%Y %H:%M")
        }

        # Notu ekle
        self.notes[user_id_str][note_type].append(note_data)

        # Değişiklikleri kaydet
        await self.save()
        return note_data
    
    async def delete_note(self, user_id: int, note_type: str, index: int) -> Optional[Dict[str, Any]]:
        """Belirtilen indeksteki notu sil"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.notes:
            return None
            
        if note_type not in self.notes[user_id_str]:
            return None
            
        if index-1 < 0 or index-1 >= len(self.notes[user_id_str][note_type]):
            return None

        # Notu kaldır
        deleted_note = self.notes[user_id_str][note_type].pop(index-1)
        
        # Hiçbir not kalmamışsa kullanıcıyı kaldır
        if (not self.notes[user_id_str]["UYARILAR"] and 
            not self.notes[user_id_str]["TIMEOUTLAR"] and 
            not self.notes[user_id_str]["BANLAR"]):
            del self.notes[user_id_str]

        # Değişiklikleri kaydet
        await self.save()
        return deleted_note
    
    async def clear_user_notes(self, user_id: int) -> bool:
        """Bir kullanıcı için tüm notları temizle"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.notes:
            return False

        # Kullanıcıyı kaldır
        del self.notes[user_id_str]

        # Değişiklikleri kaydet
        await self.save()
        return True
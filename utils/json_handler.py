import json
import os
import logging
import shutil
from datetime import datetime

class JsonHandler:
    """JSON dosyalarını güvenli bir şekilde yönetmek için yardımcı sınıf"""
    
    @staticmethod
    def load_json(file_path, default=None):
        """
        JSON dosyasını güvenli bir şekilde yükler.
        Dosya bozuksa yedekten geri yükler.
        """
        if default is None:
            default = {}
            
        # Dosya yoksa boş veri oluştur
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default, f, ensure_ascii=False, indent=4)
            return default
            
        try:
            # Dosyayı yüklemeye çalış
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logging.error(f"Veri dosyası bozuk: {file_path}, Hata: {e}")
            
            # Yedek dosya var mı kontrol et
            backup_path = f"{file_path}.backup"
            if os.path.exists(backup_path):
                logging.info(f"Yedekten veri geri yükleniyor: {backup_path}")
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # Yedekten yüklemek başarılı oldu, bozuk dosyanın üzerine yaz
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    return data
                except:
                    logging.critical(f"Yedek dosya da bozuk: {backup_path}")
                    
            # Yedek yoksa veya yedek de bozuksa yeni bir dosya oluştur
            logging.warning(f"Bozuk dosya yeniden oluşturuluyor: {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default, f, ensure_ascii=False, indent=4)
            return default
    
    @staticmethod
    def save_json(file_path, data):
        """
        Veriyi güvenli bir şekilde JSON dosyasına kaydeder.
        Önce yedek alır, sonra yeni veriyi kaydeder.
        """
        directory = os.path.dirname(file_path)
        os.makedirs(directory, exist_ok=True)
        
        # Eğer dosya zaten varsa yedek al
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            try:
                shutil.copy2(file_path, backup_path)
            except Exception as e:
                logging.error(f"Dosya yedeklenirken hata: {e}")
        
        # Yeni veriyi kaydet
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logging.error(f"Dosya kaydedilirken hata: {e}")
            return False
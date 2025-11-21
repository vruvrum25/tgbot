import os
import json
from datetime import datetime

class DataManager:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        # Файл, куда пишет PHP
        self.leads_file = os.path.join(data_dir, "leads.txt")
        # Временная связь User-Yclid
        self.temp_file = os.path.join(data_dir, "waiting_captcha.txt") 
        # Финальный файл для отправки
        self.verified_file = os.path.join(data_dir, "to_send_yandex.txt") 

    def find_yclid_by_hash(self, invite_hash):
        """Ищет хеш в файле leads.txt"""
        if not os.path.exists(self.leads_file):
            return None
        try:
            with open(self.leads_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        data = json.loads(line)
                        if data.get('hash') == invite_hash:
                            return data.get('yclid')
                    except: continue
        except Exception as e:
            print(f"Error reading leads.txt: {e}")
        return None

    def save_temp_link(self, user_id, yclid):
        """Запоминаем юзера до капчи"""
        try:
            with open(self.temp_file, "a", encoding="utf-8") as f:
                f.write(f"{user_id}|{yclid}\n")
        except Exception as e:
            print(f"Error saving temp: {e}")

    def get_yclid_from_temp(self, user_id):
        """Достаем yclid при успешной капче"""
        if not os.path.exists(self.temp_file): return None
        target_yclid = None
        try:
            with open(self.temp_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines:
                if str(user_id) in line:
                    parts = line.strip().split('|')
                    if len(parts) >= 2:
                        target_yclid = parts[1]
        except: pass
        return target_yclid

    def save_verified_user(self, user_id, yclid):
        """Пишем в файл на отправку"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{user_id}|{yclid}|verified|{timestamp}\n"
        try:
            with open(self.verified_file, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            print(f"Error saving verified: {e}")

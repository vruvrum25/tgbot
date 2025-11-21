import os
import json
from datetime import datetime

class DataManager:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        # 1. Файл от PHP (Входные данные)
        self.leads_file = os.path.join(data_dir, "leads.txt")
        
        # 2. Временная связка: UserID <-> Yclid (Пока не решил капчу)
        self.temp_file = os.path.join(data_dir, "waiting_captcha.txt") 
        
        # 3. Финал: Очередь на отправку в Яндекс
        self.verified_file = os.path.join(data_dir, "to_send_yandex.txt") 

    def find_yclid_by_hash(self, invite_hash):
        """Ищет хеш ссылки в файле leads.txt"""
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
                    except:
                        continue
        except Exception as e:
            print(f"Error reading leads.txt: {e}")
        return None

    def save_temp_link(self, user_id, yclid):
        """Запоминаем юзера перед капчей"""
        try:
            with open(self.temp_file, "a", encoding="utf-8") as f:
                f.write(f"{user_id}|{yclid}\n")
        except Exception as e:
            print(f"Error saving temp link: {e}")

    def get_yclid_from_temp(self, user_id):
        """Ищем yclid по юзеру (читаем файл waiting_captcha.txt)"""
        if not os.path.exists(self.temp_file):
            return None
        
        target_yclid = None
        try:
            with open(self.temp_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Ищем совпадение. Если юзер кликал много раз, берем последний Yclid.
            for line in lines:
                if str(user_id) in line:
                    parts = line.strip().split('|')
                    if len(parts) >= 2:
                        target_yclid = parts[1]
        except:
            return None
        
        return target_yclid

    def save_verified_user(self, user_id, yclid):
        """ФИНАЛ: Записываем в файл для отправки в Яндекс"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Формат: ID | YCLID | STATUS | TIME
        line = f"{user_id}|{yclid}|verified|{timestamp}\n"
        
        try:
            with open(self.verified_file, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            print(f"Error saving verified user: {e}")

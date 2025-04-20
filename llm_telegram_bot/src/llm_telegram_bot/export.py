#!/usr/bin/env python
import os
import pandas as pd
import yadisk
import logging
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

CSV_FILE_PATH = "/app/analytics/user_actions.csv"
EXPORT_INTERVAL_HOURS = 2
YADISK_TOKEN = os.getenv("YADISK_TOKEN")
YADISK_FOLDER = os.getenv("YADISK_FOLDER", "telegram_bot_analytics")

def export_data():
    if not os.path.exists(CSV_FILE_PATH) or not YADISK_TOKEN:
        return
    
    try:
        # CSV в XLSX
        os.makedirs("/tmp", exist_ok=True)
        xlsx_path = "/tmp/analytics.xlsx"
        
        df = pd.read_csv(CSV_FILE_PATH)
        df.to_excel(xlsx_path, index=False)
        
        # Загрузка на Яндекс Диск
        client = yadisk.Client(token=YADISK_TOKEN)
        
        if not client.check_token():
            logger.error("Недействительный токен Яндекс Диска")
            return
        
        if not client.exists(f"/{YADISK_FOLDER}"):
            client.mkdir(f"/{YADISK_FOLDER}")
        
        upload_path = f"/{YADISK_FOLDER}/analytics.xlsx"
        
        client.upload(xlsx_path, upload_path, overwrite=True)
        logger.info(f"Данные экспортированы на Яндекс Диск: {upload_path}")
        
        # Удаление временного файла
        os.remove(xlsx_path)
    except Exception as e:
        logger.error(f"Ошибка экспорта: {e}")
    finally:
        if 'client' in locals():
            client.close()

def run_scheduler():
    schedule.every(EXPORT_INTERVAL_HOURS).hours.do(export_data)
    logger.info(f"Запущен экспорт данных (интервал {EXPORT_INTERVAL_HOURS}ч)")
    
    export_data()  # Начальный экспорт
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    run_scheduler() 
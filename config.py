import os
from dotenv import load_dotenv

load_dotenv()

# Получаем значения из переменных окружения
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

# Если переменные не найдены, используем значения по умолчанию
if not API_TOKEN:
    API_TOKEN = '8257412493:AAHBybb-RUcPs85NP-c78aXpQU4Z0M0_P3w'
    print("Warning: Using default TELEGRAM_BOT_TOKEN from code")

if not DATABASE_URL:
    DATABASE_URL = 'postgresql://ivanvasil4:Vasanna_7@pg4.sweb.ru:5433/ivanvasil4'
    print("Warning: Using default DATABASE_URL from code")

# Проверяем, что значения не пустые
if not API_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

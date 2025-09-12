from main import DatabaseManager
from config import DATABASE_URL
import asyncio

db = DatabaseManager(DATABASE_URL)

async def create_user_async(telegram_id: int, user_name: str, echpoch_score: int = 0):
    return await db.create_user_async(telegram_id, user_name, echpoch_score)

async def get_user_by_telegram_id_async(telegram_id: int):
    return await db.get_user_by_telegram_id_async(telegram_id)

async def get_user_stats_async(telegram_id: int):
    return await db.get_user_stats_async(telegram_id)

# Синхронные методы для использования вне асинхронного контекста
def create_user(telegram_id: int, user_name: str, echpoch_score: int = 0):
    return db.create_user(telegram_id, user_name, echpoch_score)

def get_user_by_telegram_id(telegram_id: int):
    return db.get_user_by_telegram_id(telegram_id)

def get_user_stats(telegram_id: int):
    return db.get_user_stats(telegram_id)

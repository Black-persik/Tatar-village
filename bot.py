import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from main import DatabaseManager
from config import API_TOKEN, DATABASE_URL

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Инициализация базы данных
db = DatabaseManager(DATABASE_URL)

# Папки для медиа
VOICES_DIR = "voices"
IMAGES_DIR = "images"

# Создаем директории если их нет
os.makedirs(VOICES_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)


# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name

    # Проверяем или создаем пользователя
    user = await db.get_user_by_telegram_id_async(user_id)
    if not user:
        await db.create_user_async(user_id, user_name)

    await message.answer(f"Привет, {user_name}! Я бот с расширенными возможностями!\n"
                         "Доступные команды:\n"
                         "/voice - отправить голосовое сообщение\n"
                         "/image - отправить изображение\n"
                         "/model - взаимодействие с ML моделью\n"
                         "/stats - моя статистика")


# Отправка голосового сообщения
@dp.message(Command("voice"))
async def send_voice(message: types.Message):
    voice_path = os.path.join(VOICES_DIR, "example.ogg")
    try:
        voice = FSInputFile(voice_path)
        await message.answer_voice(voice=voice)
    except Exception as e:
        await message.answer("Ошибка отправки голосового сообщения")
        logging.error(e)


# Отправка изображения
@dp.message(Command("image"))
async def send_image(message: types.Message):
    image_path = os.path.join(IMAGES_DIR, "example.jpg")
    try:
        photo = FSInputFile(image_path)
        await message.answer_photo(photo=photo)
    except Exception as e:
        await message.answer("Ошибка отправки изображения")
        logging.error(e)


# Статистика пользователя
@dp.message(Command("stats"))
async def user_stats(message: types.Message):
    user_id = message.from_user.id
    stats = await db.get_user_stats_async(user_id)

    if stats:
        response = (f"📊 Ваша статистика:\n"
                    f"Решено задач: {stats['total_solved']}\n"
                    f"Общий счет: {stats['total_score']}")
        await message.answer(response)
    else:
        await message.answer("Статистика не найдена")


# Заглушка для ML модели
async def process_with_model(text: str):
    return f"Модель обработала текст: {text}"


# Взаимодействие с моделью
@dp.message(Command("model"))
async def model_interaction(message: types.Message):
    user_text = message.text.replace('/model', '').strip()
    if not user_text:
        await message.answer("Введите текст после команды /model")
        return

    response = await process_with_model(user_text)
    await message.answer(response)


# Обработка текстовых сообщений
@dp.message(F.text)
async def echo_message(message: types.Message):
    await message.answer("Получено текстовое сообщение")


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота
API_TOKEN = '8257412493:AAHBybb-RUcPs85NP-c78aXpQU4Z0M0_P3w'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Папки для медиа
VOICES_DIR = "voices"
IMAGES_DIR = "images"

# Создаем директории если их нет
os.makedirs(VOICES_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)


# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я бот с расширенными возможностями!\n"
                         "Доступные команды:\n"
                         "/voice - отправить голосовое сообщение\n"
                         "/image - отправить изображение\n"
                         "/model - взаимодействие с ML моделью")


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


# Заглушка для ML модели
async def process_with_model(text: str):
    # Здесь будет интеграция с вашей ML моделью
    # Пока возвращаем заглушку
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
    import asyncio

    asyncio.run(main())

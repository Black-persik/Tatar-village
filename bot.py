import os
import logging
import asyncio
import random
import requests
import hashlib
from functools import lru_cache
from typing import Optional
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramNetworkError

from main import DatabaseManager
from config import API_TOKEN, DATABASE_URL

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Инициализация базы данных
db = DatabaseManager(DATABASE_URL)

# Получаем абсолютные пути к папкам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOICES_DIR = os.path.join(BASE_DIR, "voices")
IMAGES_DIR = os.path.join(BASE_DIR, "images")

# Создаем директории если их нет
os.makedirs(VOICES_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# Пути к изображениям
WELCOME_IMAGE = os.path.join(IMAGES_DIR, "derevnya_vstuplenie_1.jpg")
DVOR_IMAGE = os.path.join(IMAGES_DIR, "pa_and_ma_dvor.jpg")
HOME_IMAGE = os.path.join(IMAGES_DIR, "home.jpg")
DOM_VNUTRI_IMAGE = os.path.join(IMAGES_DIR, "pa_and_ma_dom_vnutri.jpg")
BABULKA_IMAGE = os.path.join(IMAGES_DIR, "babulka.jpg")
SLOVARIK_IMAGE = os.path.join(IMAGES_DIR, "slovarik.jpg")
LIST_SLOV_IMAGE = os.path.join(IMAGES_DIR, "listslov.jpg")
DED_IMAGE = os.path.join(IMAGES_DIR, "ded.jpg")
DED_CHAK_IMAGE = os.path.join(IMAGES_DIR, "ded_chak.jpg")
GRUSTNII_BABULUA_IMAGE = os.path.join(IMAGES_DIR, "grustnii_babulya.jpg")
SAMOVAR_IMAGE = os.path.join(IMAGES_DIR, "samovar.jpg")
DOBRII_IMAGE = os.path.join(IMAGES_DIR, "dobrii.jpg")
FINAL_IMAGE = os.path.join(IMAGES_DIR, "final.jpg")

# Путь к голосовому сообщению
VOICE_MESSAGE = os.path.join(VOICES_DIR, "golos.ogg")

# Проверяем существование изображений и голосового сообщения
for img_path in [WELCOME_IMAGE, DVOR_IMAGE, HOME_IMAGE, DOM_VNUTRI_IMAGE, BABULKA_IMAGE, SLOVARIK_IMAGE,
                 LIST_SLOV_IMAGE, DED_IMAGE, DED_CHAK_IMAGE, GRUSTNII_BABULUA_IMAGE, SAMOVAR_IMAGE, DOBRII_IMAGE, FINAL_IMAGE]:
    if not os.path.exists(img_path):
        logger.warning(f"Изображение не найдено: {img_path}")

if not os.path.exists(VOICE_MESSAGE):
    logger.warning(f"Голосовое сообщение не найдено: {VOICE_MESSAGE}")


# Функция для создания спойлера
def create_spoiler(text: str) -> str:
    """Создает текст со скрытым содержимым под спойлером"""
    return f"<span class='tg-spoiler'>{text}</span>"


# Кэширование изображений
@lru_cache(maxsize=10)
def get_cached_image(image_path: str) -> Optional[FSInputFile]:
    """Кэширование изображений для ускорения доступа"""
    if os.path.exists(image_path):
        return FSInputFile(image_path)
    return None


def get_image_hash(image_path: str) -> str:
    """Создание хэша для пути изображения"""
    return hashlib.md5(image_path.encode()).hexdigest()


# Состояния для FSM
class DayScenario(StatesGroup):
    waiting_action = State()
    waiting_phrase_response = State()
    waiting_for_answer = State()
    waiting_text_response = State()
    waiting_tea_request = State()


# Объединенная глава со всеми заданиями
CHAPTERS = {
    "chapter1": {
        "title": "Глава 1",
        "parts": [
            {
                "type": "info",
                "image": DVOR_IMAGE,
                "text_tatar": "Әби (бабушка):\n\n— Исәнме, кунак! Безнең авылга рәхим ит!\n\n[Исэнme, куна́к! Безне́ng авылgá рэхи́m ит!]",
                "text_russian": "Привет,"f"{create_spoiler('гость! Добро пожаловать в нашу деревню!')} \n\nБабай (дедушка):\n\n— Әйдә, түрдән уз. Сине кайнар чәй белән чәк-чәк көтә.\n\n[Эйдэ́, турдэ́n uz. Сине́ кайна́r чэй беле́n чэк-чэ́k кэtэ́.]\n\n Проходи {create_spoiler('в дом. Тебя ждёт горячий чай с чак-чаком.')}",
                "next_button_text": "Зайти в дом",
                "next_image": HOME_IMAGE,
                "next_image1": DOM_VNUTRI_IMAGE,
                "next_text_tatar": "Бабай:\n\n— Безнең авыл тыныч һәм матур. Кичләрен без җырлибыз.\n\n[Безнэ́ng авы́l тыны́ч хэm мату́r. Кичлэ́rэн без жyrла́йбыz.]",
                "next_text_russian": f"У нас {create_spoiler('в деревне спокойно и красиво. Вечерами мы поём песни.')}",
                "next_image2": BABULKA_IMAGE,
                "next_text_babulka": f"Әби:\n\n — Утырыгыз, рәхим итегез! Чәй эчәрсезме?\n\n[Утырыгы́z, рэхи́m итеге́z! Чэй эчэрсезме́?]\n\nПрисаживайтесь, {create_spoiler('угощайтесь! Будете чай?')}",
                "next_text_babulka1": f"— Ай ты наверное плохо меня понимаешь..\n\n *Әбика взяла с полки старенькую потрепанную книгу. \n\n — Вот возьми словарик:  ",
                "next_image3": SLOVARIK_IMAGE,
                "take_button_text": "Алу (взять)",
            },
            {
                "type": "thanks_question",
                "question": "Поблагодарите бабушку:",
                "options": [
                    {"text": "Зур рахмат!", "correct": True, "response": "Правильно! Бабушка рада, что вы вежливы."},
                    {"text": "Рэхим итерегез!", "correct": False,
                     "response": "Неправильно. Это значит 'Добро пожаловать!'"},
                    {"text": "Хверле ирте!", "correct": False, "response": "Неправильно. Это значит 'Добрый день!'"},
                    {"text": "Бик яхшы куренегез!", "correct": False,
                     "response": "Неправильно. Это значит 'Очень приятно познакомиться!'"}
                ]
            },
            {
                "type": "ded_question",
                "image": DED_IMAGE,
                "text_tatar": "Бабай:\n\n— Сезгә чәй ошадымы?\n\n[Сезгэ́ чэй ошадымы́?]",
                "text_russian": "Чай вам понравился?",
                "hint": "Ответьте фразой: Әйе, бик тәмле чәй булды! Рәхмәт!",
                "correct_answer": "әйе бик тәмле чәй булды рәхмәт"
            },
            {
                "type": "tea_request",
                "text": "Татарский чай такой вкусный, что вы бы с удовольствием выпили еще. Используя әле (мягкое «пожалуйста») и лексику из словаря попросите дедушку налить вам еще одну кружку чая",
                "required_word": "әле"
            },
            {
                "type": "ded_chak_image",
                "image": DED_CHAK_IMAGE,
                "text": f"Бабай:\n\n — Менә чәк-чәк. Аласызмы? \n\n [Менэ́ чэк-чэк. Аласызмы́?]\n\nВот чак-чак.{create_spoiler('Возьмёте? / Будете?')}",
                "expected_responses": ["да", "конечно", "чак-чак"]
            },
            {
                "type": "info_image",
                "image": GRUSTNII_BABULUA_IMAGE,
                "text": f"Әби:\n\n — Әй, самоварда су бетте... Ләкин бу бәла түгел, {create_spoiler('нам')} ярдәм итәр дип уйлыйм.\n\n "
                        f"[Эй, самоварда́ су бетте́... Лэ-кин бу бэла́ тугель, {create_spoiler('нам')} ярдэм этэр дип уйла́ым.]\n\n Ой, вода"
                        f"{create_spoiler(' в самоваре закончилась... Но это не беда, нам поможет, думаю.')}"
            },
            {
                "type": "info_image",
                "image": SAMOVAR_IMAGE,
                "text": f"Проходите задания в течение дня и наполняй самовар пока бабушка печет свои пәрәмәч, чтобы к вечеру опять попить чай в теплой компании!☕️❤️"
            },
            {
                "type": "info_image",
                "image": DOBRII_IMAGE,
                "text": "— Балам, ашадынмы? Хәзер сиңа урын җәимме? \n [Ба́лам, ашады́нгмы? Хэзе́р, синга́ уры́н жэйи́мме?] Дитя мое, ты поел ? Постель постелить ?"
            },
            {
                "type": "info_image",
                "image": FINAL_IMAGE,
                "text": f"Бабай достал из сенцев тяжелый советский матрас. Әби принесла пару пуховых подушек и тяжелое-тяжелое одеяло. На полу вам соорудили просто царское ложе. Скрип половиц, запах влаги и посапывания кота. День подходит к концу..."
            }
        ]
    }
}


# Функция для получения ответа от GigaChat API с таймаутами
def get_llm_response(question: str, user_answer: str) -> str:
    """
    Получает ответ от GigaChat API с проверкой ответа пользователя.
    """
    try:
        # Получение токена
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': 'b15dc234-3503-40d5-ac09-c25453176832',
            'Authorization': 'Basic N2NlY2E4NjMtYjFhMi00N2MxLTkwYjAtNzc3NjVmOWVkY2U5OjA3OGE1NGE3LTRlMjс-NDMzMi05N2VlLWEyMWVkMzk5OT32NQ=='
        }
        payload = {
            'scope': 'GIGACHAT_API_PERS'
        }

        response_for_token = requests.post(url, headers=headers, data=payload, verify=False, timeout=10)

        if response_for_token.status_code != 200:
            return

        access_token = response_for_token.json()['access_token']

        # Формируем промпт для проверки ответа
        system_prompt = f"""Представь, что ты добрая и вежливая бабушка, которая говорит ТОЛЬКО ПО-РУССКИ!!!.
        Пользователю был задан вопрос: '{question}'
        Пользователь ответил: '{user_answer}'
        Если пользователь правильно ответил на вопрос - похвали пользователя.
        Если пользователь ответил не по теме - вежливо укажи на его ошибки.
        Будь доброй и поддерживающей. НЕ ОТВЕЧАЙ ПО_ТАТАРСКИ!!!
        Отвечай сплошным текстам - не отвечай по пунктам.
        Отвечай не больше двух предложений. Старайся ответь кратко и ясно
        Выводи только одну фразу!
        """

        url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        payload = {
            "model": "GigaChat",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Ответ: '{user_answer}'"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }

        resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)

        if resp.status_code != 200:
            return "Извините, произошла ошибка при проверке ответа."

        answer = resp.json()['choices'][0]['message']['content']
        return f"Русский вариант: {answer}\n\n(Перевод временно недоступен)"

    except Exception as e:
        logger.error(f"Ошибка при обращении к LLM: {e}")
        return


# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user_name = message.from_user.full_name

    try:
        user = await asyncio.wait_for(db.get_user_by_telegram_id_async(user_id), timeout=5.0)
        if not user:
            await asyncio.wait_for(db.create_user_async(user_id, user_name), timeout=5.0)
    except asyncio.TimeoutError:
        logger.error("Timeout accessing database")
        await message.answer("Извините, произошла ошибка при доступе к базе данных. Попробуйте позже.")
        return
    except Exception as e:
        logger.error(f"Ошибка при работе с базой данных: {e}")
        await message.answer("Извините, произошла ошибка при работе с базой данных.")
        return

    # Отправляем приветственное изображение
    if os.path.exists(WELCOME_IMAGE):
        try:
            photo = get_cached_image(WELCOME_IMAGE)
            if photo:
                await message.answer_photo(
                    photo,
                    caption="Tатар авылы.\n\nВоздух, густой и сладкий, пахнет полынью и свежим сеном. Из распахнутого окна соседнего дома доносится сдобный аромат свежеиспечённого икмәк. Первая вечерняя молитва —азан— плывёт над деревней, смешиваясь с вечерней тишиной. Здесь время течёт по-другому…"
                )
        except Exception as e:
            logger.error(f"Ошибка при отправке изображения: {e}")
            await message.answer("Tатар авылы.\n\nВоздух, густой и сладкий, пахнет полынью и свежим сеном...")
    else:
        await message.answer("Tатар авылы.\n\nВоздух, густой и сладкий, пахнет полынью и свежим сеном...")

    # Ждем и отправляем следующие сообщения
    await asyncio.sleep(5)
    await message.answer(
        "Вы наверное не совсем понимаете, где оказались)\n\n"
        "Приветствуем вас в интерактивном курсе по татарскому языку и культуре \"Татар жае\"!☀️\n\n"
        "На протяжении нескольких глав мы с вами будем погружаться в татарскую культуру, посмотрим быт и традиции. И прочувствуем эту загадочную татарскую душу❤️"
    )

    await asyncio.sleep(5)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👵 📖 Глава 1", callback_data="chapter_1")]
    ])
    await message.answer("Ну что, готовы начать?", reply_markup=keyboard)


# Обработчики для глав
@dp.callback_query(F.data == "chapter_1")
async def chapter_1_callback(callback: types.CallbackQuery, state: FSMContext):
    await start_chapter(callback, state, "chapter1")


# Функция запуска главы
async def start_chapter(callback: types.CallbackQuery, state: FSMContext, chapter_key):
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    chapter = CHAPTERS[chapter_key]
    await state.set_state(DayScenario.waiting_for_answer)
    await state.update_data(
        current_chapter=chapter_key,
        current_part=0,
        score=0,
        correct_answers=0,
        total_questions=0,
        shown_images=set(),
        has_dictionary=False
    )
    await send_chapter_content(callback.message, chapter, 0, state)


# Функция отправки содержания части главы
async def send_chapter_content(message: types.Message, chapter, part_index, state: FSMContext):
    part = chapter["parts"][part_index]
    data = await state.get_data()
    shown_images = data.get("shown_images", set())

    await state.update_data(current_question_type=part.get("type", "multiple_choice"))

    # Обработка вопроса деда
    if part.get("type") == "ded_question":
        caption = f"{part.get('text_tatar', '')}\n\n{part.get('text_russian', '')}\n\n💡 {part.get('hint', '')}"

        # Отправляем изображение деда
        if part.get("image") and os.path.exists(part["image"]):
            photo = get_cached_image(part["image"])
            if photo:
                await message.answer_photo(photo, caption=caption)

        # Устанавливаем состояние ожидания текстового ответа
        await state.set_state(DayScenario.waiting_text_response)
        await state.update_data(expected_words=part.get("expected_words", []))
        return

    # Обработка просьбы добавки чая
    if part.get("type") == "tea_request":
        text = part.get("text", "")
        await message.answer(text)

        # Устанавливаем состояние ожидания просьбы о чае
        await state.set_state(DayScenario.waiting_tea_request)
        await state.update_data(required_word=part.get("required_word", ""))
        return

    # Обработка изображения деда с чак-чаком
    if part.get("type") == "ded_chak_image":
        caption = part.get("text", "")

        if part.get("image") and os.path.exists(part["image"]):
            photo = get_cached_image(part["image"])
            if photo:
                await message.answer_photo(photo, caption=caption)

        # Устанавливаем состояние ожидания ответа
        await state.set_state(DayScenario.waiting_text_response)
        await state.update_data(expected_responses=part.get("expected_responses", []))
        return

    # Обработка информационных изображений (грустная бабушка, самовар, доброе изображение, финальное)
    if part.get("type") == "info_image":
        caption = part.get("text", "")

        if part.get("image") and os.path.exists(part["image"]):
            photo = get_cached_image(part["image"])
            if photo:
                await message.answer_photo(photo, caption=caption)

        # Если это изображение грустной бабушки, отправляем голосовое сообщение
        if part.get("image") == DOBRII_IMAGE and os.path.exists(VOICE_MESSAGE):
            await asyncio.sleep(2)
            try:
                voice = FSInputFile(VOICE_MESSAGE)
                await message.answer_voice(voice, caption="Голосовое сообщение от бабушки")
            except Exception as e:
                logger.error(f"Ошибка при отправке голосового сообщения: {e}")

        # Ждем 3 секунды и переходим к следующей части
        await asyncio.sleep(3)

        # Переходим к следующей части
        current_part = part_index + 1
        if current_part < len(chapter["parts"]):
            await state.update_data(current_part=current_part)
            await send_chapter_content(message, chapter, current_part, state)
        else:
            await finish_chapter(message, state, chapter)
        return

    # Формируем текст для подписи
    caption = ""
    if part.get("text_tatar"):
        caption += f"{part['text_tatar']}\n\n"
    if part.get("text_russian"):
        caption += f"{part['text_russian']}\n\n"

    # Отправляем первое изображение с текстом
    image_path = part.get("image")
    if image_path and os.path.exists(image_path):
        try:
            photo = get_cached_image(image_path)
            if photo:
                # Отправляем фото с подписью
                await message.answer_photo(photo, caption=caption.strip())

                # Ждем 3 секунды и отправляем кнопку
                await asyncio.sleep(3)
                if part.get("next_button_text"):
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text=part["next_button_text"], callback_data="next_part")]
                    ])
                    await message.answer("Нажмите кнопку, чтобы продолжить:", reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Ошибка при отправке изображения: {e}")
            if caption.strip():
                await message.answer(caption.strip())
    elif part.get("type") == "thanks_question":
        # Отправляем вопрос с вариантами ответа
        question = part.get("question", "")
        options = part.get("options", [])

        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for idx, option in enumerate(options):
            keyboard.inline_keyboard.append([InlineKeyboardButton(text=option["text"], callback_data=f"answer_{idx}")])

        await message.answer(question, reply_markup=keyboard)
    else:
        if caption.strip():
            await message.answer(caption.strip())


# Обработчик для перехода к следую части
@dp.callback_query(F.data == "next_part")
async def next_part_callback(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_chapter = data.get("current_chapter")
    current_part = data.get("current_part", 0)
    chapter = CHAPTERS[current_chapter]
    part = chapter["parts"][current_part]

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    # Отправляем HOME_IMAGE
    home_image_path = part.get("next_image")
    if home_image_path and os.path.exists(home_image_path):
        home_photo = get_cached_image(home_image_path)
        if home_photo:
            await callback.message.answer_photo(home_photo)

    # Ждем 5 секунд и отправляем DOM_VNUTRI_IMAGE
    await asyncio.sleep(5)

    dom_image_path = part.get("next_image1")
    if dom_image_path and os.path.exists(dom_image_path):
        dom_photo = get_cached_image(dom_image_path)
        if dom_photo:
            # Формируем подпись для второго изображения
            next_caption = ""
            if part.get("next_text_tatar"):
                next_caption += f"{part['next_text_tatar']}\n\n"
            if part.get("next_text_russian"):
                next_caption += f"{part['next_text_russian']}\n\n"

            await callback.message.answer_photo(dom_photo, caption=next_caption.strip())

    # Ждем 5 секунд и отправляем BABULKA_IMAGE
    await asyncio.sleep(5)

    babulka_image_path = part.get("next_image2")
    if babulka_image_path and os.path.exists(babulka_image_path):
        babulka_photo = get_cached_image(babulka_image_path)
        if babulka_photo:
            babulka_caption = part.get("next_text_babulka", "")
            await callback.message.answer_photo(babulka_photo, caption=babulka_caption.strip())

    # Ждем 5 секунд и отправляем текст
    await asyncio.sleep(5)
    babulka_text1 = part.get("next_text_babulka1", "")
    if babulka_text1:
        await callback.message.answer(babulka_text1)

    # Ждем 5 секунд и отправляем SLOVARIK_IMAGE
    await asyncio.sleep(5)
    slovarik_image_path = part.get("next_image3")
    if slovarik_image_path and os.path.exists(slovarik_image_path):
        slovarik_photo = get_cached_image(slovarik_image_path)
        if slovarik_photo:
            await callback.message.answer_photo(slovarik_photo)

    # Добавляем кнопку "Алу (взять)"
    await asyncio.sleep(3)
    if part.get("take_button_text"):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=part["take_button_text"], callback_data="take_dictionary")]
        ])
        await callback.message.answer("Хотите взять словарик?", reply_markup=keyboard)


# Обработчик для кнопки "Алу (взять)"
@dp.callback_query(F.data == "take_dictionary")
async def take_dictionary_callback(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    # Обновляем состояние - пользователь получил словарь
    await state.update_data(has_dictionary=True)

    # Создаем клавиатуру с кнопкой "Словарик"
    dictionary_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="👵 📖 Словарик")]],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    await callback.message.answer(
        "Вы взяли словарик! Теперь вы можете открыть его в любое время, нажав на кнопку \"📖 Словарик\" ниже.",
        reply_markup=dictionary_keyboard
    )

    # Переходим к следующей части
    data = await state.get_data()
    current_chapter = data.get("current_chapter")
    current_part = data.get("current_part", 0) + 1
    chapter = CHAPTERS[current_chapter]

    if current_part < len(chapter["parts"]):
        await state.update_data(current_part=current_part)
        await send_chapter_content(callback.message, chapter, current_part, state)
    else:
        await finish_chapter(callback.message, state, chapter)


# Обработчик для кнопки "Словарик"
@dp.message(F.text == "📖 Словарик")
async def show_dictionary(message: types.Message, state: FSMContext):
    data = await state.get_data()
    has_dictionary = data.get("has_dictionary", False)

    if has_dictionary and os.path.exists(LIST_SLOV_IMAGE):
        photo = get_cached_image(LIST_SLOV_IMAGE)
        if photo:
            await message.answer_photo(photo, caption="Вот ваш словарик! Используйте его для изучение татарских слов.")
        else:
            await message.answer("Словарик временно недоступен.")
    else:
        await message.answer("У вас еще нет словарика. Продолжайте обучение, чтобы получить его.")


# Обработчик ответа на вопрос
@dp.callback_query(DayScenario.waiting_for_answer, F.data.startswith("answer_"))
async def handle_answer(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_chapter = data.get("current_chapter")
    current_part = data.get("current_part", 0)
    chapter = CHAPTERS[current_chapter]
    part = chapter["parts"][current_part]

    # Проверяем, что это вопрос с благодарностью
    if part.get("type") != "thanks_question":
        await callback.answer("Это не вопрос с вариантами ответа")
        return

    option_index = int(callback.data.split("_")[1])
    option = part["options"][option_index]

    total_questions = data.get("total_questions", 0) + 1
    correct_answers = data.get("correct_answers", 0)
    score = data.get("score", 0)

    if option["correct"]:
        score += 5
        correct_answers += 1
        await callback.answer("Правильно! +5 баллов")
    else:
        await callback.answer("Неправильно")

    await state.update_data(score=score, correct_answers=correct_answers, total_questions=total_questions)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    await callback.message.answer(f"📝 {option['response']}")

    if option["correct"]:
        user_id = callback.from_user.id
        try:
            user = await asyncio.wait_for(db.get_user_by_telegram_id_async(user_id), timeout=5.0)
            if user:
                await asyncio.wait_for(db.increment_user_score_async(user[0], 5), timeout=5.0)
        except:
            pass

        # Переходим к следующей части только при правильном ответе
        next_part = current_part + 1
        if next_part < len(chapter["parts"]):
            await state.update_data(current_part=next_part)
            await asyncio.sleep(1)
            await send_chapter_content(callback.message, chapter, next_part, state)
        else:
            await finish_chapter(callback.message, state, chapter)
    else:
        # При неправильном ответе остаемся на том же вопросе
        await asyncio.sleep(1)
        await send_chapter_content(callback.message, chapter, current_part, state)


# Обработчик ответа на вопрос деда
@dp.message(DayScenario.waiting_text_response)
async def handle_ded_response(message: types.Message, state: FSMContext):
    user_answer = message.text.lower()
    data = await state.get_data()

    # Проверяем, это ответ на вопрос про чай или про чак-чак
    expected_responses = data.get("expected_responses", [])

    if expected_responses:  # Это вопрос про чак-чак
        if any(response in user_answer for response in expected_responses):
            await message.answer("✅ Отлично! Бабай рад, что вы взяли чак-чак!")

            # Обновляем статистику
            user_id = message.from_user.id
            try:
                user = await asyncio.wait_for(db.get_user_by_telegram_id_async(user_id), timeout=5.0)
                if user:
                    await asyncio.wait_for(db.increment_user_score_async(user[0], 5), timeout=5.0)
            except:
                pass

            # Переходим к следующей части
            current_chapter = data.get("current_chapter")
            current_part = data.get("current_part", 0) + 1
            chapter = CHAPTERS[current_chapter]

            if current_part < len(chapter["parts"]):
                await state.update_data(current_part=current_part)
                await send_chapter_content(message, chapter, current_part, state)
            else:
                await finish_chapter(message, state, chapter)
        else:
            await message.answer("❌ Попробуйте ответить: 'да', 'конечно' или 'чак-чак'")

    else:  # Это вопрос про чай (оригинальная логика)
        # Нормализуем ответ пользователя: убираем знаки препинания и лишние пробелы
        normalized_user_answer = ' '.join(user_answer.replace('!', '').replace(',', '').split())

        # Получаем правильный ответ из данных состояния
        current_chapter = data.get("current_chapter")
        current_part = data.get("current_part", 0)
        chapter = CHAPTERS[current_chapter]
        part = chapter["parts"][current_part]
        correct_answer = part.get("correct_answer", "")

        # Проверяем совпадение с правильным ответом (игнорируя регистр и знаки препинания)
        if normalized_user_answer == correct_answer:
            # Получаем ответ от LLM
            llm_response = get_llm_response("Понравился ли вам чай?", user_answer)

            await message.answer(f"✅ Отлично! Вы правильно ответили дедушке!\n\n{llm_response}")

            # Обновляем статистику
            user_id = message.from_user.id
            try:
                user = await asyncio.wait_for(db.get_user_by_telegram_id_async(user_id), timeout=5.0)
                if user:
                    await asyncio.wait_for(db.increment_user_score_async(user[0], 10), timeout=5.0)
            except:
                pass

            # Переходим к следующей части
            current_part = current_part + 1
            if current_part < len(chapter["parts"]):
                await state.update_data(current_part=current_part)
                await send_chapter_content(message, chapter, current_part, state)
            else:
                await finish_chapter(message, state, chapter)
        else:
            await message.answer("❌ Попробуйте еще раз. Ответ должен быть: Әйе, бик тәмле чәй булды! Рәхмәт!")


# Обработчик просьбы добавки чая
@dp.message(DayScenario.waiting_tea_request)
async def handle_tea_request(message: types.Message, state: FSMContext):
    user_answer = message.text.lower()
    data = await state.get_data()

    # Проверяем наличие обязательного слова "әле"
    if "әле" in user_answer:
        # Получаем ответ от LLM
        llm_response = get_llm_response("Попросите еще чаю, используя слово 'әле'", user_answer)

        await message.answer(f"✅ Отлично! Вы вежливо попросили добавки!\n\n{llm_response}")

        # Обновляем статистику
        user_id = message.from_user.id
        try:
            user = await asyncio.wait_for(db.get_user_by_telegram_id_async(user_id), timeout=5.0)
            if user:
                await asyncio.wait_for(db.increment_user_score_async(user[0], 8), timeout=5.0)
        except:
            pass

        # Переходим к следующей части
        current_chapter = data.get("current_chapter")
        current_part = data.get("current_part", 0) + 1
        chapter = CHAPTERS[current_chapter]

        if current_part < len(chapter["parts"]):
            await state.update_data(current_part=current_part)
            await send_chapter_content(message, chapter, current_part, state)
        else:
            await finish_chapter(message, state, chapter)
    else:
        await message.answer("❌ Попробуйте еще раз. Не забудьте использовать слово 'әле' (пожалуйста) в вашей просьбе!")


# Функция завершения главы
async def finish_chapter(message, state: FSMContext, chapter):
    data = await state.get_data()
    correct_answers = data.get("correct_answers", 0)
    total_questions = data.get("total_questions", 0)
    score = data.get("score", 0)

    success_rate = (correct_answers / total_questions * 100) if total_questions > 0 else 0

    user_id = message.from_user.id
    try:
        user = await asyncio.wait_for(db.get_user_by_telegram_id_async(user_id), timeout=5.0)
        stats = await asyncio.wait_for(db.get_user_stats_async(user_id), timeout=5.0) if user else None
    except:
        stats = None

    await message.answer(
        f"🎉 {chapter['title']} завершена!\n\n"
        f"📊 Ваши результаты:\n"
        f"• Правильных ответов: {correct_answers}/{total_questions}\n"
        f"• Процент успеха: {success_rate:.1f}%\n"
        f"• Заработано баллов: {score}\n"
        f"• Общий счет: {stats['total_score'] if stats else 0}\n\n"
        "Спасибо, что изучали татарский язык с нами!"
    )
    await state.clear()


# Обработка текстовых сообщений
@dp.message(F.text)
async def handle_text(message: types.Message, state: FSMContext):
    text = message.text.lower()
    current_state = await state.get_state()

    if current_state in [DayScenario.waiting_for_answer, DayScenario.waiting_text_response,
                         DayScenario.waiting_tea_request]:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👵 🔄 Начать заново", callback_data="chapter_1")]
        ])
        await message.answer("Вы находитесь в процессе обучения. Хотите начать заново?", reply_markup=keyboard)
        return

    if any(word in text for word in ['рәхмәт', 'рахмет', 'спасибо', 'thanks', 'thank']):
        responses = [
            "Зинһар! Әйбәт сүзләрегез өчен рәхмәт!",
            "Рәхмәт! Тагын да яңа фразлар өйрәнергә ярдәм итегез!",
            "Сезгә дә рәхмәт! Татар телен өйрәнүдә уңышлар телимен!"
        ]
        await message.answer(random.choice(responses))
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👵 📖 Глава 1", callback_data="chapter_1")]
        ])
        await message.answer(
            "Я пока понимаю только определенные команды. Для изучения татарского языка нажмите кнопку ниже:",
            reply_markup=keyboard
        )


# Запуск бота
async def main():
    try:
        await dp.start_polling(bot)
    except TelegramNetworkError as e:
        logger.error(f"Network error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())

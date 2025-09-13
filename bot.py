import os
import logging
import asyncio
import random
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

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
WELCOME_IMAGE = os.path.join(IMAGES_DIR, "welcome.jpg")
TEA_IMAGE = os.path.join(IMAGES_DIR, "tea.jpg")
GAMES_IMAGE = os.path.join(IMAGES_DIR, "games.jpg")
SLEEP_IMAGE = os.path.join(IMAGES_DIR, "sleep.jpg")

# Проверяем существование изображений
for img_path in [WELCOME_IMAGE, TEA_IMAGE, GAMES_IMAGE, SLEEP_IMAGE]:
    if not os.path.exists(img_path):
        logger.warning(f"Изображение не найдено: {img_path}")


# Состояния для FSM
class DayScenario(StatesGroup):
    waiting_action = State()
    waiting_phrase_response = State()
    waiting_for_answer = State()
    waiting_text_response = State()


# Словарь для хранения всех словарей из всех глав
FULL_DICTIONARY = {
    "Приветствие": {
        "рәхим ит(егез)": "добро пожаловать/угощайтесь (вежл. мн. ч.)",
        "әйдә": "давай/прошу",
        "менә": "вот/вот он",
        "чәй": "чай",
        "чәк-чәк": "чак-чак",
        "белән": "с/со",
        "утырыгыз": "садитесь (вежл.)",
        "эчәрсезме? / эчегез": "будете пить? / пейте (вежл.)",
        "тынч, матур": "спокойный, красивый",
        "исәнме": "привет",
        "кунак": "гость",
        "авыл": "деревня",
        "түр": "дом",
        "уз": "проходи",
        "кайнар": "горячий",
        "кичләрен": "вечерами",
        "җырлыйбыз": "поём"
    },
    "Еда": {
        "кунак күңеле": "душа гостя",
        "мәйдан": "площадь (здесь: широкий, желанный)",
        "туйган көн": "день рождения",
        "туйдырмыйча": "не накормив",
        "җибәрмәсләр": "не отпустят",
        "табын": "стол",
        "милли пешерм": "национальная выпечка",
        "өчпочмак": "эчпочмак (треугольник)",
        "кыстыбый": "кыстыбый (лепешка с начинкой)",
        "кәбәстә": "кабәртмә (жареный пирожок)",
        "тәмле булсын": "приятного аппетита",
        "аласызмы": "будете брать?",
        "рәхмәт": "спасибо",
        "тәмле": "вкусно",
        "әйбәт": "хорошо",
        "әле": "пожалуйста (мягкое)",
        "коегыз": "наливайте",
        "бераз": "немного",
        "гына": "только",
        "тагын": "еще",
        "алырга": "брать",
        "мөмкинме": "можно ли"
    },
    "Вечерние игры": {
        "кич": "вечер",
        "кояш байды": "солнце село",
        "урам": "улица",
        "чыгабыз": "выходим",
        "күрше": "соседский",
        "балалар": "дети",
        "уйныйбыз": "играем",
        "уеннар": "игры",
        "уйнарсыңмы": "будешь играть"
    },
    "Завершение дня": {
        "бүген": "сегодня",
        "күңелле": "весело",
        "киләсе тапкыр": "в следующий раз",
        "килерсең": "приедешь",
        "хәерле кич": "добрый вечер/спокойной ночи",
        "төшкә чаклы": "до обеда",
        "сау бул": "будь здоров",
        "йокы": "сон",
        "тәмле булсын": "пусть будет вкусным (сладким)"
    }
}

# Объединенная глава со всеми заданиями
CHAPTERS = {
    "chapter1": {
        "title": "Глава 1: Полное погружение в татарскую культуру",
        "character": "Әби һәм Бабай",
        "parts": [
            {
                "name": "Часть 1: Приветствие",
                "type": "info",
                "image": WELCOME_IMAGE,
                "text_tatar": "Исәнме, кунак! Безнең авылга рәхим ит! Әйдә, түрдән уз. Менә кайнар чәй, чәк-чәк белән. Чәй эчәрсезме? Утырыгыз, рәхим итегез! Безнең авыл тыныч һәм матур. Кичләрен без җырлыйбыз.",
                "text_russian": "Привет, гость! Добро пожаловать в нашу деревню! Проходи в дом. Вот горячий чай с чак-чаком. Будете чай? Присаживайтесь, угощайтесь! У нас в деревне спокойно и красиво. Вечерами мы поём песни.",
                "explanation": "Татарское гостеприимство известно - всегда готовы принять гостей и угостить их лучшим, что есть в доме.",
                "next_button_text": "📖 Посмотреть словарь",
            },
            {
                "name": "Часть 2: Задание 2.1",
                "type": "multiple_choice",
                "text_tatar": "",
                "text_russian": "",
                "explanation": "Выберите вежливую фразу-приглашение:",
                "question": "Выберите вежливую фразу-приглашение:",
                "options": [
                    {"text": "Рәхим итегез!", "correct": True,
                     "response": "Правильно! Это вежливая форма приглашения."},
                    {"text": "Чәй эчәсең?", "correct": False,
                     "response": "Не совсем. Это менее формальный вариант."},
                    {"text": "Чәй эч!", "correct": False,
                     "response": "Нет, это слишком неформально для гостя."}
                ],
                "image": TEA_IMAGE
            },
            {
                "name": "Часть 3: Задание 2.2",
                "type": "phrase_building",
                "text_tatar": "",
                "text_russian": "",
                "explanation": "Соберите фразу из предложенных слова:",
                "hint": "Токены: итегез · чәй · рәхим · Менә",
                "correct_phrases": ["Менә чәй, рәхим итегез!", "Менә чәй рәхим итегез"],
                "response": "Правильно! Вы составили вежливую фразу-приглашение.",
                "image": TEA_IMAGE
            },
            {
                "name": "Часть 4: Задание 2.3",
                "type": "text_response",
                "text_tatar": "",
                "text_russian": "",
                "explanation": "Скажите «Налейте, пожалуйста, совсем чуть-чуть.» по-татарски:",
                "hint": "Используйте слово 'әле' (мягкое «пожалуйста») и лексику из сцены.",
                "correct_responses": ["Әле бераз гына коегыз", "Әле бераз гына", "Әле бераз кына коегыз"],
                "response": "Правильно! Бабушка нальет вам чуть-чуть чая.",
                "image": TEA_IMAGE
            },
            {
                "name": "Часть 5: Диалог с Бабаем",
                "type": "text_response",
                "text_tatar": "Бабай: Рәхим итегез, чәй эчегез!",
                "text_russian": "Дедушка: Пожалуйста, пейте чай!",
                "explanation": "Ответьте благодарностью и оцените вкус:",
                "hint": "Скажите 'спасибо' и 'вкусно' по-татарски",
                "correct_responses": ["Рәхмәт, бик тәмле", "Рәхмәт, бик әйбәт"],
                "response": "Правильно! Бабай доволен вашей благодарностью.",
                "image": TEA_IMAGE
            },
            {
                "name": "Часть 6: Диалог с Әби",
                "type": "text_response",
                "text_tatar": "Әби: Менә чәк-чәк. Аласызмы?",
                "text_russian": "Бабушка: Вот чак-чак. Будете?",
                "explanation": "Вежливо примите угощение:",
                "hint": "Используйте 'менә', 'рәхим итегез' или 'белән'",
                "correct_responses": ["Менә чәк-чәк, рәхим итегез", "Рәхим итегез, чәк-чәк белән"],
                "response": "Правильно! Вы вежливо приняли угощение.",
                "image": TEA_IMAGE
            },
            {
                "name": "Часть 7: Просьба",
                "type": "text_response",
                "text_tatar": "",
                "text_russian": "",
                "explanation": "Попросите еще чуть-чуть чая:",
                "hint": "Спросите 'Можно еще чуть-чуть чая?' по-татарски",
                "correct_responses": ["Тагын бераз чәй алырга мөмкинме?", "Тагын бераз чәй мөмкинме?"],
                "response": "Правильно! Бабушка налила вам еще чаю.",
                "image": TEA_IMAGE
            },
            {
                "name": "Часть 8: Вечерние игры",
                "type": "info",
                "text_tatar": "Кич булды. Кояш байды. Әйдә, урамга чыгабыз. Күрше балалар белән уйныйбыз. Уйнарсыңмы?",
                "text_russian": "Наступил вечер. Солнце село. Давай выйдем на улицу. Поиграем с соседскими детьми. Будешь играть?",
                "explanation": "Вечерами в татарских деревнях дети часто собираются вместе для игр на улице.",
                "next_button_text": "▶️ Продолжить",
                "image": GAMES_IMAGE
            },
            {
                "name": "Часть 9: Завершение дня",
                "type": "info",
                "text_tatar": "Бүген бик күңелле булды. Кич белән сау бул! Йокыгыз тәмле булсын. Килерсең әле?",
                "text_russian": "Сегодня было очень весело. Доброй ночи! Пусть ваш сон будет сладким. Ты ещё приедешь?",
                "explanation": "Традиционные пожелания доброй ночи и сладких снов в татарской культуре.",
                "next_button_text": "🏁 Завершить главу",
                "image": SLEEP_IMAGE
            }
        ]
    }
}


# Функция для получения ответа от GigaChat API
def get_llm_response(question: str, user_answer: str) -> str:
    """
    Получает ответ от GigaChat API с проверкой ответа пользователя.
    """
    # Получение токена
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': 'b15dc234-3503-40d5-ac09-c25453176832',
        'Authorization': 'Basic N2NlY2E4NjMtYjFhMi00N2MxLTkwYjAtNzc3NjVmOWVkY2U5OjA3OGE1NGEzLTRlMjctNDMzMi05N2VlLWEyMWVkMzk5OTMyNQ=='
    }
    payload = {
        'scope': 'GIGACHAT_API_PERS'
    }

    try:
        response_for_token = requests.post(url, headers=headers, data=payload, verify=False)

        # Проверяем, что токен получен успешно
        if response_for_token.status_code != 200:
            return "Извините, сервис проверки ответов временно недоступен."

        access_token = response_for_token.json()['access_token']

        # Формируем промпт для проверки ответа
        system_prompt = f"""Представь, что ты добрая и вежливая бабушка, которая говорит ТОЛЬКО ПО-РУССКИ!!!.
        Пользователю был задан вопрос: '{question}'
        Пользователь ответил: '{user_answer}'
        Если пользователь правильно ответил на вопрос - похвали пользователя.
        Если пользователь ответил не по теме - вежливо укажи на его ошибки.
        Будь доброй и поддерживающей. НЕ ОТВЕЧАЙ ПО_ТАТАРСКИ!!!
        Отвечай сплошным текстом - не отвечай по пунктам.
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

        # Проверяем статус ответа
        if resp.status_code != 200:
            return "Извините, произошла ошибка при проверке ответа."

        # Извлекаем ответ
        answer = resp.json()['choices'][0]['message']['content']

        # Переводим ответ на татарский
        try:
            from gradio_client import Client
            client = Client("https://v2.api.translate.tatar/")
            total_answer = client.predict(
                lang="rus2tat",
                text=answer,
                api_name="/translate_interface"
            )
            return total_answer
        except:
            # Если перевод не удался, возвращаем ответ на русском
            return f"Русский вариант: {answer}\n\n(Перевод временно недоступен)"

    except Exception as e:
        logger.error(f"Ошибка при обращении к LLM: {e}")
        return "Извините, сервис проверки ответов временно недоступен."


# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user_name = message.from_user.full_name

    # Проверяем или создаем пользователя
    user = await db.get_user_by_telegram_id_async(user_id)
    if not user:
        await db.create_user_async(user_id, user_name)

    # Отправляем приветственное сообщение с кнопкой "Начать"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать", callback_data="show_main_menu")],
        [InlineKeyboardButton(text="📊 Моя статистика", callback_data="my_stats")],
        [InlineKeyboardButton(text="ℹ️ О проекте", callback_data="about")]
    ])

    # Отправляем приветственное изображение, если оно существует
    if os.path.exists(WELCOME_IMAGE):
        try:
            photo = FSInputFile(WELCOME_IMAGE)
            await message.answer_photo(photo,
                                       caption=f"Сәлам, {user_name}! Мин татар телен өйрәнү буенча ярдәмчи ботмын.\n\n"
                                               "Давайте проведем время в татарской деревне с бабушкой и дедушкой!",
                                       reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Ошибка при отправке изображения: {e}")
            await message.answer(
                f"Сәлам, {user_name}! Мин татар телен өйрәнү буенча ярдәмчи ботмын.\n\n"
                "Давайте проведем время в татарской деревне с бабушкой и дедушкой!",
                reply_markup=keyboard
            )
    else:
        await message.answer(
            f"Сәлам, {user_name}! Мин татар телен өйрәнү буенча ярдәмчи ботмын.\n\n"
            "Давайте проведем время в татарской деревне с бабушкой и дедушкой!",
            reply_markup=keyboard
        )


# Новый обработчик для показа главного меню
@dp.callback_query(F.data == "show_main_menu")
async def show_main_menu(callback: types.CallbackQuery):
    # Создаем клавиатуру с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Главы", callback_data="chapters_menu")],
        [InlineKeyboardButton(text="📊 Моя статистика", callback_data="my_stats")],
        [InlineKeyboardButton(text="ℹ️ О проекте", callback_data="about")]
    ])

    await callback.message.edit_text(
        "Выберите раздел:",
        reply_markup=keyboard
    )


# Обработчик для меню глав
@dp.callback_query(F.data == "chapters_menu")
async def chapters_menu_callback(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Глава 1: Полное погружение", callback_data="chapter_1")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="show_main_menu")]
    ])

    await callback.message.edit_text(
        "Выберите главу:",
        reply_markup=keyboard
    )


# Обработчики для глав
@dp.callback_query(F.data == "chapter_1")
async def chapter_1_callback(callback: types.CallbackQuery, state: FSMContext):
    await start_chapter(callback, state, "chapter1")


# Функция запуска главы
async def start_chapter(callback: types.CallbackQuery, state: FSMContext, chapter_key):
    await callback.message.edit_reply_markup(reply_markup=None)
    chapter = CHAPTERS[chapter_key]
    await callback.message.answer(f"Начинаем {chapter['title'].lower()}! 📖")
    await state.set_state(DayScenario.waiting_for_answer)
    await state.update_data(
        current_chapter=chapter_key,
        current_part=0,
        score=0,
        correct_answers=0,
        total_questions=0,
        shown_images=set()  # Множество для отслеживания показанных изображений
    )
    await send_chapter_content(callback.message, chapter, 0, state)


# Функция отправки содержания части главы
async def send_chapter_content(message: types.Message, chapter, part_index, state: FSMContext):
    part = chapter["parts"][part_index]
    data = await state.get_data()
    shown_images = data.get("shown_images", set())

    # Обновляем состояние с типом текущего задания
    await state.update_data(current_question_type=part.get("type", "multiple_choice"))

    # Отправляем изображение, если оно указано, существует и еще не было показано
    image_path = part.get("image")
    if image_path and os.path.exists(image_path) and image_path not in shown_images:
        try:
            photo = FSInputFile(image_path)
            await message.answer_photo(photo)
            # Добавляем изображение в множество показанных
            shown_images.add(image_path)
            await state.update_data(shown_images=shown_images)
        except Exception as e:
            logger.error(f"Ошибка при отправке изображения: {e}")

    response = f"👵👴 {chapter['character']} - {part['name']}:\n\n"

    if part["text_tatar"]:
        response += f"🇹🇳 {part['text_tatar']}\n\n"
    if part["text_russian"]:
        response += f"🇷🇺 {part['text_russian']}\n\n"
    if part["explanation"]:
        response += f"💡 {part['explanation']}\n\n"

    # Для информационного блока
    if part["type"] == "info":
        keyboard_buttons = []

        # Добавляем кнопку "Посмотреть словарь" только для первой части
        if part_index == 0:
            keyboard_buttons.append(
                [InlineKeyboardButton(text="📖 Посмотреть словарь", callback_data="show_dictionary_from_info")])

        keyboard_buttons.append([InlineKeyboardButton(text=part["next_button_text"], callback_data="next_part")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await message.answer(response, reply_markup=keyboard)

    # Для множественного выбора
    elif part["type"] == "multiple_choice":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=option["text"], callback_data=f"answer_{i}")]
            for i, option in enumerate(part["options"])
        ])
        response += f"❓ {part['question']}"
        await message.answer(response, reply_markup=keyboard)

    # Для составления фразы или текстового ответа
    elif part["type"] in ["phrase_building", "text_response"]:
        if "hint" in part:
            response += f"💡 {part['hint']}\n\n"
        await message.answer(response)
        # Устанавливаем состояние ожидания текстового ответа
        await state.set_state(DayScenario.waiting_text_response)
        await state.update_data(current_part=part_index)


# Обработчик для перехода к следующей части (для информационных блоков)
@dp.callback_query(F.data == "next_part")
async def next_part_callback(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_chapter = data.get("current_chapter")
    current_part = data.get("current_part", 0) + 1
    chapter = CHAPTERS[current_chapter]

    if current_part < len(chapter["parts"]):
        await state.update_data(current_part=current_part)
        await callback.message.edit_reply_markup(reply_markup=None)
        await send_chapter_content(callback.message, chapter, current_part, state)
    else:
        await finish_chapter(callback, state, chapter)


# Обработчик для показа словаря из информационного блока
@dp.callback_query(F.data == "show_dictionary_from_info")
async def show_dictionary_from_info(callback: types.CallbackQuery, state: FSMContext):
    # Получаем данные о текущей части
    data = await state.get_data()
    current_chapter = data.get("current_chapter")
    current_part = data.get("current_part", 0)
    chapter = CHAPTERS[current_chapter]
    part = chapter["parts"][current_part]

    # Собираем словарь для текущей категории
    category = "Приветствие"  # Для первой части
    words = FULL_DICTIONARY.get(category, {})

    dictionary_text = f"📖 <b>{category}</b>\n\n"
    dictionary_text += "\n".join([f"• <b>{key}</b> - {value}" for key, value in words.items()])

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"📚 Словарь к текущему уроку:\n\n{dictionary_text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад к уроку", callback_data="back_to_lesson")]
        ])
    )


# Обработчик для возврата из словаря к уроку
@dp.callback_query(F.data == "back_to_lesson")
async def back_to_lesson_callback(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_chapter = data.get("current_chapter")
    current_part = data.get("current_part", 0)
    chapter = CHAPTERS[current_chapter]

    await callback.message.edit_reply_markup(reply_markup=None)
    await send_chapter_content(callback.message, chapter, current_part, state)


# Обработчик текстовых ответов
@dp.message(DayScenario.waiting_text_response)
async def handle_text_response(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_chapter = data.get("current_chapter")
    current_part = data.get("current_part", 0)
    chapter = CHAPTERS[current_chapter]
    part = chapter["parts"][current_part]
    user_text = message.text.strip()

    # Проверяем ответ в зависимости от типа задания
    is_correct = False
    feedback = ""

    if part["type"] == "phrase_building":
        # Для составления фразы проверяем несколько возможных вариантов
        is_correct = any(phrase.lower() in user_text.lower() for phrase in part["correct_phrases"])
        if not is_correct:
            # Используем LLM для обратной связи
            question = f"Составьте фразу: {part['hint']}"
            feedback = await asyncio.to_thread(get_llm_response, question, user_text)

    elif part["type"] == "text_response":
        # Для текстового ответа проверяем несколько возможных вариантов
        is_correct = any(resp.lower() in user_text.lower() for resp in part["correct_responses"])
        if not is_correct:
            # Используем LLM для обратной связи
            question = f"Ответьте на фразу: {part.get('text_tatar', '')} - {part.get('explanation', '')}"
            feedback = await asyncio.to_thread(get_llm_response, question, user_text)

    # Обновляем статистику
    total_questions = data.get("total_questions", 0) + 1
    correct_answers = data.get("correct_answers", 0)
    score = data.get("score", 0)

    if is_correct:
        score += 5
        correct_answers += 1
        await message.answer(f"✅ Правильно! +5 баллов\n\n{part['response']}")

        # Начисляем баллы в базу данных
        user_id = message.from_user.id
        user = await db.get_user_by_telegram_id_async(user_id)
        if user:
            await db.increment_user_score_async(user[0], 5)
    else:
        # Показываем обратную связь от LLM
        if feedback:
            await message.answer(f"❌ Неправильно. Обратная связь:\n\n{feedback}")
        else:
            await message.answer("❌ Неправильно. Попробуйте еще раз.")
        # Не переходим к следующей части, ждем правильного ответа
        return

    await state.update_data(score=score, correct_answers=correct_answers, total_questions=total_questions)

    # Переходим к следующей части
    next_part = current_part + 1
    if next_part < len(chapter["parts"]):
        await state.update_data(current_part=next_part)
        await asyncio.sleep(1)
        await send_chapter_content(message, chapter, next_part, state)
    else:
        await finish_chapter(message, state, chapter)


# Функция завершения главы
async def finish_chapter(message, state: FSMContext, chapter):
    data = await state.get_data()
    correct_answers = data.get("correct_answers", 0)
    total_questions = data.get("total_questions", 0)
    score = data.get("score", 0)

    success_rate = (correct_answers / total_questions * 100) if total_questions > 0 else 0

    # Получаем статистику пользователя из базы данных
    user_id = message.from_user.id
    user = await db.get_user_by_telegram_id_async(user_id)
    stats = await db.get_user_stats_async(user_id) if user else None

    await message.answer(
        f"🎉 {chapter['title']} завершена!\n\n"
        f"📊 Ваши результаты:\n"
        f"• Правильных ответов: {correct_answers}/{total_questions}\n"
        f"• Процент успеха: {success_rate:.1f}%\n"
        f"• Заработано баллов: {score}\n"
        f"• Общий счет: {stats['total_score'] if stats else 0}\n\n"
        "Спасибо, что изучали татарский язык с нами!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Выбрать другую главу", callback_data="chapters_menu")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="my_stats")]
        ])
    )
    await state.clear()


# Обработчик ответа на вопрос в главе (для multiple_choice)
@dp.callback_query(DayScenario.waiting_for_answer, F.data.startswith("answer_"))
async def handle_answer(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_chapter = data.get("current_chapter")
    current_part = data.get("current_part", 0)
    chapter = CHAPTERS[current_chapter]
    part = chapter["parts"][current_part]

    option_index = int(callback.data.split("_")[1])
    option = part["options"][option_index]

    # Обновляем статистику
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

    # Показываем объяснение
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"📝 {option['response']}")

    # Начисляем баллы за правильный ответ в базу данных
    if option["correct"]:
        user_id = callback.from_user.id
        user = await db.get_user_by_telegram_id_async(user_id)
        if user:
            await db.increment_user_score_async(user[0], 5)

    # Переходим к следующей части
    next_part = current_part + 1
    if next_part < len(chapter["parts"]):
        await state.update_data(current_part=next_part)
        await asyncio.sleep(1)
        await send_chapter_content(callback.message, chapter, next_part, state)
    else:
        await finish_chapter(callback.message, state, chapter)


@dp.callback_query(F.data == "my_stats")
async def my_stats_callback(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    await user_stats(callback.message)


@dp.callback_query(F.data == "about")
async def about_callback(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "🇹🇷 Татарский язык с культурой\n\n"
        "Этот бот поможет вам изучить татарский язык через погружение в культуру и традиции.\n\n"
        "Вы посетите виртуальную татарскую деревню, где будете общаться с местными жителями, "
        "участвовать в повседневной жизни и изучать язык в контексте.\n\n"
        "Проject создан для сохранения и популяризации татарского языка и культуры.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="show_main_menu")]
        ])
    )


# Статистика пользователя
@dp.message(Command("stats"))
async def user_stats(message: types.Message):
    user_id = message.from_user.id
    user = await db.get_user_by_telegram_id_async(user_id)

    if user:
        stats = await db.get_user_stats_async(user_id)
        if stats:
            response = (f"📊 Ваша статистика:\n"
                        f"• Общий счет: {stats['total_score']}\n"
                        f"• Изучено фраз: {stats.get('phrases_learned', 0)}\n"
                        f"• Правильных ответов: {stats.get('correct_answers', 0)}\n"
                        f"• Всего вопросов: {stats.get('total_questions', 0)}\n\n"
                        f"✅ Продолжайте в том же духе!")
            await message.answer(response)
        else:
            await message.answer("Статистика не найдена. Попробуйте команду /start")
    else:
        await message.answer("Вы не зарегистрированы. Используйте команду /start")


# Обработка текстовых сообщений с благодарностью
@dp.message(F.text)
async def handle_text(message: types.Message, state: FSMContext):
    text = message.text.lower()
    current_state = await state.get_state()

    # Если пользователь в процессе сценария, предлагаем вернуться
    if current_state == DayScenario.waiting_for_answer or current_state == DayScenario.waiting_text_response:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Начать заново", callback_data="show_main_menu")]
        ])
        await message.answer("Вы находитесь в процессе обучения. Хотите начать заново?", reply_markup=keyboard)
        return

    # Ответы на благодарности
    if any(word in text for word in ['рәхмәт', 'рахмет', 'спасибо', 'thanks', 'thank']):
        responses = [
            "Зинһар! Әйбәт сүзләрегез өчен рәхмәт!",
            "Рәхмәт! Тагын да яңа фразлар өйрәнергә ярдәм итегез!",
            "Сезгә дә рәхмәт! Татар телен өйрәнүдә уңышлар телимен!"
        ]
        await message.answer(random.choice(responses))
    else:
        # Для других текстовых сообщений предлагаем начать обучение
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Начать", callback_data="show_main_menu")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="my_stats")]
        ])
        await message.answer(
            "Я пока понимаю только определенные команды. Для изучения татарского языка используйте кнопки ниже:",
            reply_markup=keyboard)


# Запуск бота
async def main():
    # Таблицы уже создаются автоматически при инициализации DatabaseManager
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

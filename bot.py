import os
import logging
import asyncio
import random
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

# Папки для медиа
VOICES_DIR = "voices"
IMAGES_DIR = "images"

# Создаем директории если их нет
os.makedirs(VOICES_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)


# Состояния для интерактивного сценария
class DayScenario(StatesGroup):
    waiting_morning_action = State()
    waiting_afternoon_action = State()
    waiting_evening_action = State()
    waiting_night_action = State()


# Фразы о татарской деревне с переводом и культурным контекстом
TATAR_VILLAGE_PHRASES = [
    {
        "tatar": "Әби пешерелгән чәй белән кунак кабул итә.",
        "russian": "Бабушка угощает гостей свежезаваренным чаем.",
        "explanation": "Чай - важная часть татарской культуры. Гостей всегда встречают чаепитием с традиционными угощениями."
    },
    {
        "tatar": "Бабай ярсу белән бакчада эшли.",
        "russian": "Дедушка усердно работает в огороде.",
        "explanation": "Сельское хозяйство традиционно важно для татар. Многие семьи имеют свои огороды и выращивают овощи."
    },
    {
        "tatar": "Кич белән бөтен гаилә җыенында җылы сузләр сөйләшеп утыралар.",
        "russian": "Вечером вся семья собирается за общим столом и ведет теплые беседы.",
        "explanation": "Семейные ценности занимают центральное место в татарской культуре."
    },
    {
        "tatar": "Әби печән бәлеше әзерли.",
        "russian": "Бабушка готовит эчпочмак (традиционный татарский пирог).",
        "explanation": "Татарская кухня славится своей выпечкой. Эчпочмак - треугольный пирог с начинкой из мяса и картофеля."
    },
    {
        "tatar": "Мәчеттән азан тавышы ишетелә.",
        "russian": "С мечети слышен звук азана (призыв к молитве).",
        "explanation": "Ислам является важной частью татарской культуры и повседневной жизни."
    },
    {
        "tatar": "Бабай атны аккалый, ә әби савыт-саба юа.",
        "russian": "Дедушка ухаживает за лошадью, а бабушка моет посуду.",
        "explanation": "Традиционное разделение обязанностей в татарской семье."
    },
    {
        "tatar": "Иртә белән мөәзиннең азан тавышы ишетелде.",
        "russian": "Утром слышен голос муэдзина, призывающего к молитве.",
        "explanation": "Религиозные традиции занимают важное место в жизни татарской деревни."
    }
]

# Интерактивный сценарий дня
DAY_SCENARIO = {
    "morning": {
        "character": "Әби",
        "text_tatar": "Иртә белән, балалар, кошлар сайрый, ә бакчада чәчәкләр ачыла. Бабай ярсу белән бакчада эшли, ә мин иртәнге аш әзерлим.",
        "text_russian": "Утром, детки, птицы поют, а в саду цветы распускаются. Дедушка усердно работает в огороде, а я готовлю завтрак.",
        "explanation": "В татарских деревнях принято рано вставать. Бабушка готовит традиционный завтрак - часто это каша (ботка), яйца и свежий деревенский хлеб.",
        "question": "Куда обычно идет дедушка утром?",
        "options": [
            {"text": "В огород", "correct": True,
             "response": "Правильно! Бабай идет работать в огород пока не наступила жара."},
            {"text": "На рыбалку", "correct": False,
             "response": "Не совсем. Хотя иногда дедушки ходят на рыбалку, обычно утром они работают в огороде."},
            {"text": "В мечеть", "correct": False, "response": "Утренняя молитва уже прошла, теперь время для работы."}
        ]
    },
    "afternoon": {
        "character": "Бабай",
        "text_tatar": "Көндезге аштан соң, өстәл янында кунаклар белән сөйләшеп утырабыз. Әбинең пешерелгән чәе һәм өчпочмаклары тәмле!",
        "text_russian": "После обеда мы сидим за столом и беседуем с гостями. Свежезаваренный чай бабушки и треугольные пирожки такие вкусные!",
        "explanation": "Обед - важное время дня, когда семья собирается вместе. Татарское гостеприимство известно - всегда готовы принять гостей и угостить их лучшим, что есть в доме.",
        "question": "Что традиционно подают к чаю в татарских семьях?",
        "options": [
            {"text": "Пироги и выпечку", "correct": True,
             "response": "Верно! Татарская кухня славится своей выпечкой: эчпочмак, бәлеш, кыстыбый."},
            {"text": "Шоколадные конфеты", "correct": False,
             "response": "Не совсем. Хотя сейчас иногда подают конфеты, традиционно это домашняя выпечка."},
            {"text": "Фрукты", "correct": False,
             "response": "Фрукты тоже подают, но главное угощение - это традиционная выпечка."}
        ]
    },
    "evening": {
        "character": "Әби",
        "text_tatar": "Кич белән бөтен гаилә җыенында җылы сүзләр сөйләшеп утырабыз. Яшьлектәге хикәяләр ишетәбез.",
        "text_russian": "Вечером вся семья собирается за общим столом и ведет теплые беседы. Мы слушаем истории из молодости.",
        "explanation": "Вечерние семейные собрания - традиция татарских семей. Старшие делятся воспоминаниями, передавая мудрость и историю семьи молодым поколениям.",
        "question": "О чем обычно рассказывают вечером?",
        "options": [
            {"text": "Истории из молодости", "correct": True,
             "response": "Правильно! Старшие делятся воспоминаниями и семейными историями."},
            {"text": "Новости из телевизора", "correct": False,
             "response": "Не совсем. Хотя иногда обсуждают новости, в основном рассказывают семейные истории."},
            {"text": "Сплетни о соседях", "correct": False,
             "response": "Нет, в татарских семьях ценят уважение к другим."}
        ]
    },
    "night": {
        "character": "Бабай",
        "text_tatar": "Төнлә йолдызлар ялтырап, җил ферәзәләр аша җылылык китерә. Иске татар җырын көйләп, балачакка кайтабыз.",
        "text_russian": "Ночью звезды сверкают, и ветер приносит тепло через окна. Напевая старую татарскую песню, мы возвращаемся в детство.",
        "explanation": "Татарские народные песни часто рассказывают о природе, любви к родной земле и ностальгии по детству. Они передаются из поколения в поколение.",
        "question": "О чем поют татарские народные песни?",
        "options": [
            {"text": "О природе и родной земле", "correct": True,
             "response": "Верно! Татарские песни прославляют красоту природы и любовь к родному краю."},
            {"text": "О современных технологиях", "correct": False,
             "response": "Нет, народные песни обычно о традиционных ценностях."},
            {"text": "О городской жизни", "correct": False,
             "response": "Не совсем. Народные песни чаще о деревне и природе."}
        ]
    }
}


# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name

    # Проверяем или создаем пользователя
    user = await db.get_user_by_telegram_id_async(user_id)
    if not user:
        await db.create_user_async(user_id, user_name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌅 Начать день в деревне", callback_data="start_day")],
        [InlineKeyboardButton(text="📚 Изучить фразы", callback_data="learn_phrases")],
        [InlineKeyboardButton(text="📊 Моя статистика", callback_data="my_stats")]
    ])

    await message.answer(
        f"Сәлам, {user_name}! Мин татар телен өйрәнү буенча ярдәмче ботмын.\n\n"
        "Давайте проведем день в татарской деревне с бабушкой и дедушкой!",
        reply_markup=keyboard
    )


# Обработчик команды /village
@dp.message(Command("village"))
async def start_village_day(message: types.Message, state: FSMContext):
    await message.answer("Давайте начнем день в татарской деревне! 🌅")
    await send_morning_scene(message, state)


# Обработчик инлайн кнопок
@dp.callback_query(F.data == "start_day")
async def start_day_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Давайте начнем день в татарской деревне! 🌅")
    await send_morning_scene(callback.message, state)


@dp.callback_query(F.data == "learn_phrases")
async def learn_phrases_callback(callback: types.CallbackQuery):
    await send_phrase(callback.message)


@dp.callback_query(F.data == "my_stats")
async def my_stats_callback(callback: types.CallbackQuery):
    await user_stats(callback.message)


# Утренняя сцена
async def send_morning_scene(message: types.Message, state: FSMContext):
    scene = DAY_SCENARIO["morning"]

    # Создаем клавиатуру с вариантами ответов
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=option["text"], callback_data=f"morning_{i}")]
        for i, option in enumerate(scene["options"])
    ])

    response = (f"🌅 Утро в татарской деревне:\n\n"
                f"👵 {scene['character']}:\n"
                f"🇹🇳 {scene['text_tatar']}\n"
                f"🇷🇺 {scene['text_russian']}\n\n"
                f"💡 {scene['explanation']}\n\n"
                f"❓ {scene['question']}")

    await message.answer(response, reply_markup=keyboard)
    await state.set_state(DayScenario.waiting_morning_action)


# Обработчик ответа на утреннюю сцену
@dp.callback_query(DayScenario.waiting_morning_action, F.data.startswith("morning_"))
async def handle_morning_answer(callback: types.CallbackQuery, state: FSMContext):
    option_index = int(callback.data.split("_")[1])
    scene = DAY_SCENARIO["morning"]
    option = scene["options"][option_index]

    # Начисляем баллы за правильный ответ
    if option["correct"]:
        user_id = callback.from_user.id
        user = await db.get_user_by_telegram_id_async(user_id)
        if user:
            await db.increment_user_score(user[0], 5)  # 5 баллов за правильный ответ

    await callback.message.edit_text(
        f"{option['response']}\n\n"
        f"💡 {scene['explanation']}\n\n"
        "Давайте продолжим день...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Перейти к обеду", callback_data="afternoon_scene")]
        ])
    )

    await state.set_state(DayScenario.waiting_afternoon_action)


# Обеденная сцена
@dp.callback_query(DayScenario.waiting_afternoon_action, F.data == "afternoon_scene")
async def send_afternoon_scene(callback: types.CallbackQuery, state: FSMContext):
    scene = DAY_SCENARIO["afternoon"]

    # Создаем клавиатуру с вариантами ответов
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=option["text"], callback_data=f"afternoon_{i}")]
        for i, option in enumerate(scene["options"])
    ])

    response = (f"☀️ День в татарской деревне:\n\n"
                f"👴 {scene['character']}:\n"
                f"🇹🇳 {scene['text_tatar']}\n"
                f"🇷🇺 {scene['text_russian']}\n\n"
                f"💡 {scene['explanation']}\n\n"
                f"❓ {scene['question']}")

    await callback.message.edit_text(response, reply_markup=keyboard)
    await state.set_state(DayScenario.waiting_afternoon_action)


# Обработчик ответа на обеденную сцену
@dp.callback_query(DayScenario.waiting_afternoon_action, F.data.startswith("afternoon_"))
async def handle_afternoon_answer(callback: types.CallbackQuery, state: FSMContext):
    option_index = int(callback.data.split("_")[1])
    scene = DAY_SCENARIO["afternoon"]
    option = scene["options"][option_index]

    # Начисляем баллы за правильный ответ
    if option["correct"]:
        user_id = callback.from_user.id
        user = await db.get_user_by_telegram_id_async(user_id)
        if user:
            await db.increment_user_score(user[0], 5)  # 5 баллов за правильный ответ

    await callback.message.edit_text(
        f"{option['response']}\n\n"
        f"💡 {scene['explanation']}\n\n"
        "Давайте продолжим день...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Перейти к вечеру", callback_data="evening_scene")]
        ])
    )

    await state.set_state(DayScenario.waiting_evening_action)


# Вечерняя сцена
@dp.callback_query(DayScenario.waiting_evening_action, F.data == "evening_scene")
async def send_evening_scene(callback: types.CallbackQuery, state: FSMContext):
    scene = DAY_SCENARIO["evening"]

    # Создаем клавиатуру с вариантами ответов
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=option["text"], callback_data=f"evening_{i}")]
        for i, option in enumerate(scene["options"])
    ])

    response = (f"🌇 Вечер в татарской деревне:\n\n"
                f"👵 {scene['character']}:\n"
                f"🇹🇳 {scene['text_tatar']}\n"
                f"🇷🇺 {scene['text_russian']}\n\n"
                f"💡 {scene['explanation']}\n\n"
                f"❓ {scene['question']}")

    await callback.message.edit_text(response, reply_markup=keyboard)
    await state.set_state(DayScenario.waiting_evening_action)


# Обработчик ответа на вечернюю сцену
@dp.callback_query(DayScenario.waiting_evening_action, F.data.startswith("evening_"))
async def handle_evening_answer(callback: types.CallbackQuery, state: FSMContext):
    option_index = int(callback.data.split("_")[1])
    scene = DAY_SCENARIO["evening"]
    option = scene["options"][option_index]

    # Начисляем баллы за правильный ответ
    if option["correct"]:
        user_id = callback.from_user.id
        user = await db.get_user_by_telegram_id_async(user_id)
        if user:
            await db.increment_user_score(user[0], 5)  # 5 баллов за правильный ответ

    await callback.message.edit_text(
        f"{option['response']}\n\n"
        f"💡 {scene['explanation']}\n\n"
        "Давайте завершим день...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Перейти к ночи", callback_data="night_scene")]
        ])
    )

    await state.set_state(DayScenario.waiting_night_action)


# Ночная сцена
@dp.callback_query(DayScenario.waiting_night_action, F.data == "night_scene")
async def send_night_scene(callback: types.CallbackQuery, state: FSMContext):
    scene = DAY_SCENARIO["night"]

    # Создаем клавиатуру с вариантами ответов
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=option["text"], callback_data=f"night_{i}")]
        for i, option in enumerate(scene["options"])
    ])

    response = (f"🌙 Ночь в татарской деревне:\n\n"
                f"👴 {scene['character']}:\n"
                f"🇹🇳 {scene['text_tatar']}\n"
                f"🇷🇺 {scene['text_russian']}\n\n"
                f"💡 {scene['explanation']}\n\n"
                f"❓ {scene['question']}")

    await callback.message.edit_text(response, reply_markup=keyboard)
    await state.set_state(DayScenario.waiting_night_action)


# Обработчик ответа на ночную сцену
@dp.callback_query(DayScenario.waiting_night_action, F.data.startswith("night_"))
async def handle_night_answer(callback: types.CallbackQuery, state: FSMContext):
    option_index = int(callback.data.split("_")[1])
    scene = DAY_SCENARIO["night"]
    option = scene["options"][option_index]

    # Начисляем баллы за правильный ответ
    if option["correct"]:
        user_id = callback.from_user.id
        user = await db.get_user_by_telegram_id_async(user_id)
        if user:
            await db.increment_user_score(user[0], 5)  # 5 баллов за правильный ответ

    # Завершаем день и показываем статистику
    user_id = callback.from_user.id
    stats = await db.get_user_stats_async(user_id)

    await callback.message.edit_text(
        f"{option['response']}\n\n"
        f"💡 {scene['explanation']}\n\n"
        "🎉 День в татарской деревне завершен!\n\n"
        f"📊 Вы заработали {stats['total_score'] if stats else 0} баллов\n"
        "Спасибо, что провели этот день с нами!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Начать заново", callback_data="start_day")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="my_stats")]
        ])
    )

    await state.clear()


# Команда для изучения отдельных фраз
@dp.message(Command("phrase"))
async def send_phrase(message: types.Message):
    # Выбираем 3 случайные фразы для изучения
    selected_phrases = random.sample(TATAR_VILLAGE_PHRASES, min(3, len(TATAR_VILLAGE_PHRASES)))

    response = "📚 Көннең татарча сүз тезмәсе:\n\n"
    for i, phrase in enumerate(selected_phrases, 1):
        response += f"{i}. <b>{phrase['tatar']}</b> - {phrase['russian']}\n\n"
        response += f"💡 {phrase['explanation']}\n\n"

    response += "✅ Для погружения в атмосферу используйте /village"
    await message.answer(response)

    # Увеличиваем счетчик изученных фраз в статистике
    user_id = message.from_user.id
    user = await db.get_user_by_telegram_id_async(user_id)
    if user:
        await db.increment_user_score(user[0], len(selected_phrases))


# Отправка голосового сообщения
@dp.message(Command("voice"))
async def send_voice(message: types.Message):
    voice_path = os.path.join(VOICES_DIR, "tatar_example.ogg")
    try:
        # Если файл существует, отправляем его
        if os.path.exists(voice_path):
            voice = FSInputFile(voice_path)
            await message.answer_voice(voice=voice, caption="Татар телендә сәламләшү")
        else:
            # Если файла нет, отправляем текстовое сообщение
            phrase = random.choice(TATAR_VILLAGE_PHRASES)
            await message.answer(f"🔊 Тавышлы язма:\n\n{phrase['tatar']}\n\n<i>{phrase['russian']}</i>")
    except Exception as e:
        await message.answer("Тавышлы хабар җибәрүдә хата килеп чыкты")
        logger.error(e)


# Отправка изображения
@dp.message(Command("image"))
async def send_image(message: types.Message):
    image_path = os.path.join(IMAGES_DIR, "tatar_culture.jpg")
    try:
        # Если файл существует, отправляем его
        if os.path.exists(image_path):
            photo = FSInputFile(image_path)
            await message.answer_photo(photo=photo, caption="Татар милли киемнәрендәге семья")
        else:
            # Если файла нет, отправляем текстовое сообщение
            phrase = random.choice(TATAR_VILLAGE_PHRASES)
            await message.answer(
                f"🖼️ Татар мәдәнияте:\n\n{phrase['explanation']}\n\n<b>{phrase['tatar']}</b>\n<i>{phrase['russian']}</i>")
    except Exception as e:
        await message.answer("Рәсем җибәрүдә хата килеп чыкты")
        logger.error(e)


# Статистика пользователя
@dp.message(Command("stats"))
async def user_stats(message: types.Message):
    user_id = message.from_user.id
    user = await db.get_user_by_telegram_id_async(user_id)

    if user:
        stats = await db.get_user_stats_async(user_id)
        if stats:
            response = (f"📊 Cезнең статистика:\n"
                        f"Өйрәнелгән фразлар: {stats['total_score']}\n"
                        f"Гомуми счет: {stats['total_score']}\n\n"
                        f"✅ Дәвам итегез! Яңа фразлар өйрәнү өчен /village боерыгын кулланыгыз")
            await message.answer(response)
        else:
            await message.answer("Статистика табылмады. /start боерыгын кулланып карагыз")
    else:
        await message.answer("Сез ботта теркәлмәгәнсез. /start боерыгын кулланыгыз")


# Обработка текстовых сообщений с благодарностью
@dp.message(F.text)
async def handle_text(message: types.Message):
    text = message.text.lower()

    # Ответы на благодарности
    if any(word in text for word in ['рәхмәт', 'рахмет', 'спасибо', 'thanks', 'thank']):
        responses = [
            "Зинһар! Әйбәт сүзләрегез өчен рәхмәт!",
            "Рәхмәт! Тагын да яңа фразлар өйрәнергә ярдәм итегез!",
            "Сезгә дә рәхмәт! Татар телен өйрәнүдә уңышлар телимен!"
        ]
        await message.answer(random.choice(responses))
    else:
        # Для других текстовых сообщений предлагаем изучить фразы
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌅 Начать день в деревне", callback_data="start_day")],
            [InlineKeyboardButton(text="📚 Изучить фразы", callback_data="learn_phrases")]
        ])
        await message.answer("Сезнең языгызны аңладым. Татар телен өйрәнү өчен түбәндәге вариантларны кулланыгыз:",
                             reply_markup=keyboard)


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

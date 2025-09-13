import os
import logging
import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

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


# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name

    # Проверяем или создаем пользователя
    user = await db.get_user_by_telegram_id_async(user_id)
    if not user:
        await db.create_user_async(user_id, user_name)

    await message.answer(f"Сәлам, {user_name}! Мин татар телен өйрәнү буенча ярдәмче ботмын.\n\n"
                         "Доступные команды:\n"
                         "/village - Татар авылында бер көн турында уйлану\n"
                         "/phrase - Татар телендәге сүз тезмәсе\n"
                         "/voice - татар телендәге тавышлы хабар\n"
                         "/image - татар мәдәниятеннән рәсем\n"
                         "/stats - минем статистика\n\n"
                         "Әйтик, /village боерыгы белән башлыйк!")


# Команда для отправки сообщений о татарской деревне
@dp.message(Command("village"))
async def send_village_phrase(message: types.Message):
    phrase = random.choice(TATAR_VILLAGE_PHRASES)

    response = (f"🎑 Татар авылында бер көн:\n\n"
                f"🇹🇳 Татарча: <b>{phrase['tatar']}</b>\n"
                f"🇷🇺 Русча: <i>{phrase['russian']}</i>\n\n"
                f"💡 {phrase['explanation']}")

    await message.answer(response)

    # Увеличиваем счетчик изученных фраз в статистике
    user_id = message.from_user.id
    user = await db.get_user_by_telegram_id_async(user_id)
    if user:
        await db.increment_user_score(user[0], 1)  # user[0] - это user_id


# Команда для изучения отдельных фраз
@dp.message(Command("phrase"))
async def send_phrase(message: types.Message):
    # Выбираем 3 случайные фразы для изучения
    selected_phrases = random.sample(TATAR_VILLAGE_PHRASES, min(3, len(TATAR_VILLAGE_PHRASES)))

    response = "📚 Көннең татарча сүз тезмәсе:\n\n"
    for i, phrase in enumerate(selected_phrases, 1):
        response += f"{i}. <b>{phrase['tatar']}</b> - {phrase['russian']}\n"

    response += "\n✅ Ярдәм өчен /village боерыгын кулланыгыз"
    await message.answer(response)

    # Увеличиваем счетчик изученных фраз в статистике
    user_id = message.from_user.id
    user = await db.get_user_by_telegram_id_async(user_id)
    if user:
        await db.increment_user_score(user[0], len(selected_phrases))


# Отправка голосового сообщения (модифицирована для татарского языка)
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


# Отправка изображения (модифицирована для татарской культуры)
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
                        f"Гомуми счет: {stats['total_score']}\n"
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
        await message.answer(
            "Сезнең языгызны аңладым. Татар телен өйрәнү өчен /village яки /phrase боерыгын кулланыгыз!")


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

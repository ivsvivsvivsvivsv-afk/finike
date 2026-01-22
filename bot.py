"""
🎮 Telegram Bot для Игрового Дня — v3.3 WEBHOOK FIX
Регистрация на игры: Катан, Каркассон, D&D
Работает на Amvera с правильным HTTPS вебхуком

ВЕРСИЯ 3.3:
✅ Исправлена ошибка IndentationError (отступы)
✅ Кнопки "Подробнее" имеют уникальные эмодзи (🎲, 🏰, 🐉)
✅ Кнопки "Записаться" имеют общий эмодзи (📝)
✅ Исправлен ID админа для получения заявок
"""

import logging
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# ═══════════════════════════════════════════════════════════════════════════════════
# 🔧 КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════════

load_dotenv()

# Критические переменные
BOT_TOKEN = os.getenv("BOT_TOKEN", "8522444294:AAFAdm3c_5NnnLSVV4-h6R0iutmGJI2Q1bw")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://finike-zhurkinigor.amvera.io/webhook")

# Параметры бота
ADMIN_ID = 190421400  # Обновил на твой ID из логов (secereon)
GROUP_LINK = "https://t.me/+fgNNmx1VlntiMGUy"
WEBHOOK_PATH = "/webhook"
WEBHOOK_HOST = "0.0.0.0"
WEBHOOK_PORT = 8000

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════════
# 🎮 ИНИЦИАЛИЗАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════════

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Данные игр с описаниями
GAMES = {
    "catan": {
        "name": "🎲 Катан",
        "emoji": "🎲",
        "short": "Стратегическая игра про колонизацию. Собирай ресурсы и строй!"
    },
    "carcassonne": {
        "name": "🏰 Каркассон",
        "emoji": "🏰",
        "short": "Тактическая игра про построение средневекового ландшафта. Размещай плитки и получай очки!"
    },
    "dnd": {
        "name": "🐉 D&D",
        "emoji": "🐉",
        "short": "Ролевая игра приключений. Создавай персонажа и отправляйся в квест!"
    }
}

# Полные описания игр
GAME_DESCRIPTIONS = {
    "catan": """
🎲 КАТАН — ПОЛНЫЕ ПРАВИЛА

Катан — экономическая стратегическая игра для 2-4 игроков.

📋 СУТЬ ИГРЫ:
Ты колонизатор, который строит поселения, города и дороги на острове Катан. Цель — первым набрать 10 очков победы.

🎯 ЧТО НУЖНО ДЕЛАТЬ:
1. Размещай поселения (стоит 1 лесоматериал + 1 овца + 1 пшеница + 1 кирпич)
2. Строй города для большего дохода (стоит 3 руды + 2 пшеницы)
3. Строй дороги между поселениями (стоит 1 лесоматериал + 1 кирпич)
4. Каждый ход ты бросаешь кубики — выпавшее число дает ресурсы

📊 РЕСУРСЫ:
🌲 Лесоматериал, 🌾 Пшеница, 🪨 Руда, 🧱 Кирпич, 🐑 Овцы

⏱️ ВРЕМЯ: 45-60 минут
👥 ИГРОКИ: 2-4 человека
🎮 СЛОЖНОСТЬ: Средняя (легко учится, глубокая стратегия)

Первый, кто получит 10 очков — побеждает! 🏆
""",
    
    "carcassonne": """
🏰 КАРКАССОН — ПОЛНЫЕ ПРАВИЛА

Каркассон — тактическая игра про построение средневекового ландшафта для 2-5 игроков.

📋 СУТЬ ИГРЫ:
Вы вместе строите огромный пейзаж, добавляя квадратные плитки. Затем размещаете своих фермеров на города, дороги, поля и монастыри, чтобы получить очки.

🎯 ЧТО НУЖНО ДЕЛАТЬ:
1. Каждый ход ты берешь одну плитку ландшафта
2. Размещаешь её так, чтобы она подходила к уже построенным
3. На плитке ты можешь разместить одного из своих фермеров
4. Когда дорога/город/монастырь/поле завершены — считаются очки

🏘️ ЭЛЕМЕНТЫ НА ПЛИТКАХ:
🏰 Города, 🛣️ Дороги, ⛪ Монастыри, 🌾 Поля

⏱️ ВРЕМЯ: 30-45 минут
👥 ИГРОКИ: 2-5 человек
🎮 СЛОЖНОСТЬ: Легкая (просто правила, интересная тактика)

Самое крутое: все строят вместе, но каждый за себя! Никогда не знаешь, что получится в итоге 😄
""",
    
    "dnd": """
🐉 D&D (DUNGEONS & DRAGONS) — ПОЛНЫЕ ПРАВИЛА

D&D — кооперативная ролевая игра приключений. Один мастер ведет историю, другие игроки управляют персонажами.

📋 СУТЬ ИГРЫ:
Ты — герой в фантастическом мире. Мастер описывает ситуацию, ты говоришь, что хочешь сделать, и вместе вы создаете невероятную историю приключений.

🎯 ЧТО НУЖНО ДЕЛАТЬ:
1. Создаешь персонажа (раса, класс, характер, умения)
2. Мастер говорит: "Вы в темной подземелье. Впереди слышны звуки..."
3. Ты решаешь: "Я крадусь вперед и смотрю, что там"
4. Бросаешь кубик — результат определяет успех/неудачу
5. История развивается на основе ваших решений

🗺️ ПЕРСОНАЖИ:
⚔️ Воин, 🏹 Лучник, 🧙 Маг, ⛩️ Священник, 🐱 Плут и многие другие!

⏱️ ВРЕМЯ: 1-4 часа (зависит от приключения)
👥 ИГРОКИ: 3-6 человек (+ 1 мастер)
🎮 СЛОЖНОСТЬ: Средняя (много правил, но просто начать)

D&D — это про рассказывание историй, воображение и веселье с друзьями! Никогда не знаешь, что произойдет дальше 🎲✨
"""
}

# Временные слоты
TIME_SLOTS = [
    "12:00-14:00",
    "14:00-16:00",
    "16:00-18:00",
    "18:00-21:00"
]

# Названия картинок (должны быть в корне)
IMAGES = {
    "welcome": "bot_welcome_banner.png",
    "atmosphere": "bot_event_atmosphere.png",
    "catan": "bot_catan_visual.png",
    "carcassonne": "bot_carcassonne_visual.png",
    "dnd": "bot_dnd_visual.png",
    "confirmation": "bot_confirmation_scroll.png"
}

# ═══════════════════════════════════════════════════════════════════════════════════
# 🛠️  УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════════════════════════

def image_exists(name: str) -> bool:
    """Проверяет существование файла картинки"""
    return os.path.exists(name)

# ═══════════════════════════════════════════════════════════════════════════════════
# 🎮 ОБРАБОТЧИКИ КОМАНД И КНОПОК
# ═══════════════════════════════════════════════════════════════════════════════════

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start — приветствие"""
    user = message.from_user
    logger.info(f"🎮 /start от {user.username or user.first_name} (ID: {user.id})")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Зарегистрироваться", callback_data="register")]
    ])
    
    welcome_text = f"""
🎮 ДОБРО ПОЖАЛОВАТЬ, {user.first_name}!

Ты в боте регистрации на 🎮 ИГРОВОЙ ДЕНЬ! 

Доступны три эпические игры:
🎲 Катан
🏰 Каркассон
🐉 D&D

Выбери удобное для тебя время и присоединяйся! 🚀
"""
    
    if image_exists(IMAGES["welcome"]):
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=types.FSInputFile(IMAGES["welcome"]),
            caption=welcome_text,
            reply_markup=keyboard
        )
    else:
        await message.answer(welcome_text, reply_markup=keyboard)


@dp.callback_query(F.data == "register")
async def cb_register(query: types.CallbackQuery):
    """Нажата кнопка 'Зарегистрироваться' — показываем описание игр"""
    logger.info(f"📋 Регистрация начата: {query.from_user.username or query.from_user.first_name}")
    
    # Создаем описание всех трех игр с кнопками
    text = """
🎮 ВЫБЕРИ ИГРУ И УЗНАЙ БОЛЬШЕ

Вот краткое описание каждой игры. Нажми "Подробнее" для полных правил, или сразу "Записаться" чтобы выбрать время!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎲 КАТАН
{catan_short}

🏰 КАРКАССОН
{carcassonne_short}

🐉 D&D
{dnd_short}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".format(
        catan_short=GAMES["catan"]["short"],
        carcassonne_short=GAMES["carcassonne"]["short"],
        dnd_short=GAMES["dnd"]["short"]
    )
    
    # ИСПРАВЛЕННЫЕ КНОПКИ С РАЗНЫМИ ЭМОДЗИ
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎲 Подробнее", callback_data="info_catan"),
            InlineKeyboardButton(text="📝 Записаться", callback_data="game_catan")
        ],
        [
            InlineKeyboardButton(text="🏰 Подробнее", callback_data="info_carcassonne"),
            InlineKeyboardButton(text="📝 Записаться", callback_data="game_carcassonne")
        ],
        [
            InlineKeyboardButton(text="🐉 Подробнее", callback_data="info_dnd"),
            InlineKeyboardButton(text="📝 Записаться", callback_data="game_dnd")
        ]
    ])
    
    try:
        if image_exists(IMAGES["atmosphere"]):
            await bot.send_photo(
                chat_id=query.message.chat.id,
                photo=types.FSInputFile(IMAGES["atmosphere"]),
                caption=text,
                reply_markup=keyboard
            )
        else:
            await query.message.answer(text, reply_markup=keyboard)
    except Exception as e:
        logger.warning(f"⚠️  Ошибка отправки сообщения: {e}")
        await query.message.answer(text, reply_markup=keyboard)
    
    await query.answer()


# Обработчики для "Подробнее"
@dp.callback_query(F.data == "info_catan")
async def cb_info_catan(query: types.CallbackQuery):
    await handle_game_info(query, "catan")


@dp.callback_query(F.data == "info_carcassonne")
async def cb_info_carcassonne(query: types.CallbackQuery):
    await handle_game_info(query, "carcassonne")


@dp.callback_query(F.data == "info_dnd")
async def cb_info_dnd(query: types.CallbackQuery):
    await handle_game_info(query, "dnd")


async def handle_game_info(query: types.CallbackQuery, game: str):
    """Показ полного описания игры"""
    logger.info(f"📖 Информация о игре: {game}")
    
    game_info = GAMES[game]
    description = GAME_DESCRIPTIONS[game]
    emoji = game_info["emoji"]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="register")],
        [InlineKeyboardButton(text=f"{emoji} Записаться на {game_info['name']}", callback_data=f"game_{game}")]
    ])
    
    try:
        if image_exists(IMAGES[game]):
            await bot.send_photo(
                chat_id=query.message.chat.id,
                photo=types.FSInputFile(IMAGES[game]),
                caption=description,
                reply_markup=keyboard
            )
        else:
            await query.message.answer(description, reply_markup=keyboard)
    except Exception as e:
        logger.warning(f"⚠️  Ошибка отправки информации: {e}")
        await query.message.answer(description, reply_markup=keyboard)
    
    await query.answer()


# Обработчики выбора игры (прямой выбор)
@dp.callback_query(F.data == "game_catan")
async def cb_game_catan(query: types.CallbackQuery):
    await handle_game_selection(query, "catan")


@dp.callback_query(F.data == "game_carcassonne")
async def cb_game_carcassonne(query: types.CallbackQuery):
    await handle_game_selection(query, "carcassonne")


@dp.callback_query(F.data == "game_dnd")
async def cb_game_dnd(query: types.CallbackQuery):
    await handle_game_selection(query, "dnd")


async def handle_game_selection(query: types.CallbackQuery, game: str):
    """Обработка выбора игры — показ времени"""
    logger.info(f"🎮 Выбрана игра: {game}")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⏰ {slot}", callback_data=f"time_{game}_{i}")]
        for i, slot in enumerate(TIME_SLOTS)
    ])
    
    game_info = GAMES[game]
    text = f"⏰ Выбери время для игры {game_info['name']}:"
    
    try:
        await query.message.answer(text, reply_markup=keyboard)
    except Exception as e:
        logger.warning(f"⚠️  Ошибка отправки времени: {e}")
        await query.message.answer(text, reply_markup=keyboard)
    
    await query.answer()


@dp.callback_query(F.data.startswith("time_"))
async def cb_time_selected(query: types.CallbackQuery):
    """Время выбрано — регистрация и отправка заявки админу"""
    # Парсим callback: time_game_timeindex
    parts = query.data.split("_")
    game = parts[1]
    time_index = int(parts[2])
    time_slot = TIME_SLOTS[time_index]
    
    user = query.from_user
    game_info = GAMES[game]
    
    logger.info(f"✅ Регистрация: {user.username or user.first_name} ({user.id}) на {game_info['name']} в {time_slot}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 📤 ОТПРАВЛЯЕМ ЗАЯВКУ АДМИНИСТРАТОРУ
    # ═══════════════════════════════════════════════════════════════════════════════
    
    admin_message = f"""
🎮 НОВАЯ ЗАЯВКА НА РЕГИСТРАЦИЮ!

👤 Игрок: @{user.username or user.first_name}
🆔 ID: {user.id}

🎯 Выбранная игра: {game_info['name']}
⏰ Временной слот: {time_slot}
📅 Время регистрации: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

✅ Статус: Новая заявка
"""
    
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_message
        )
        logger.info(f"✅ Заявка отправлена админу: {user.username or user.first_name}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки заявки админу: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 📤 ПОКАЗЫВАЕМ ПОДТВЕРЖДЕНИЕ ПОЛЬЗОВАТЕЛЮ
    # ═══════════════════════════════════════════════════════════════════════════════
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Перейти в группу", url=GROUP_LINK)],
        [InlineKeyboardButton(text="✅ Готово", callback_data="done")]
    ])
    
    confirmation_text = f"""
✅ СПАСИБО ЗА РЕГИСТРАЦИЮ!

🎯 Ты зарегистрирован на:
   {game_info['name']} в {time_slot}

🔔 ПОДПИШИСЬ НА НАШУ ГРУППУ
Там все организационные вопросы и обновления! 👇
"""
    
    try:
        if image_exists(IMAGES["confirmation"]):
            await bot.send_photo(
                chat_id=query.message.chat.id,
                photo=types.FSInputFile(IMAGES["confirmation"]),
                caption=confirmation_text,
                reply_markup=keyboard
            )
        else:
            await query.message.answer(confirmation_text, reply_markup=keyboard)
    except Exception as e:
        logger.warning(f"⚠️  Ошибка отправки подтверждения: {e}")
        await query.message.answer(confirmation_text, reply_markup=keyboard)
    
    await query.answer("✅ Заявка успешно отправлена администратору!")


@dp.callback_query(F.data == "done")
async def cb_done(query: types.CallbackQuery):
    """Кнопка 'Готово'"""
    await query.answer("🎮 Увидимся на игровом дне! 🎲🏰🐉")

# ═══════════════════════════════════════════════════════════════════════════════════
# 🌐 WEBHOOK КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════════

async def handle_webhook(request: web.Request):
    """Обработчик вебхука от Telegram"""
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot, update)
    except Exception as e:
        logger.error(f"❌ Ошибка обработки вебхука: {e}")
    return web.Response(text="OK")


async def on_startup(app):
    """Запуск — регистрируем вебхук"""
    logger.info("🚀 Бот запускается...")
    logger.info(f"📡 WEBHOOK_URL: {WEBHOOK_URL}")
    
    try:
        # Удаляем старый вебхук
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Старый вебхук удалён")
    except Exception as e:
        logger.warning(f"⚠️  При удалении старого вебхука: {e}")
    
    # Устанавливаем новый вебхук
    try:
        await bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"✅ Вебхук установлен: {WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"❌ ОШИБКА установки вебхука: {e}")
        logger.info(f"💡 Проверь WEBHOOK_URL в переменных окружения Amvera")


async def on_shutdown(app):
    """Остановка бота"""
    logger.info("🛑 Бот останавливается...")
    try:
        await bot.session.close()
    except Exception as e:
        logger.warning(f"⚠️  При закрытии сессии: {e}")


async def main():
    """Главная функция — запуск вебсервера"""
    logger.info("🎮 Telegram Bot для Игрового Дня v3.3")
    logger.info("Режим: WEBHOOK (Amvera compatible)")
    
    # Создаём веб-приложение
    app = web.Application()
    
    # Маршруты
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    
    # События
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    # Запускаем вебсервер
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBHOOK_HOST, WEBHOOK_PORT)
    await site.start()
    
    logger.info(f"✅ Веб-сервер запущен на {WEBHOOK_HOST}:{WEBHOOK_PORT}")
    logger.info(f"📡 Вебхук слушает на {WEBHOOK_PATH}")
    logger.info("🎮 БОТ ГОТОВ К РАБОТЕ! Ожидаю сообщения от Telegram...")
    
    # Держим приложение живым
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("⌨️  Получена команда выхода")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

"""
🎮 Telegram Bot для Игрового Дня — v3.0 WEBHOOK
Регистрация на игры: Катан, Каркассон, D&D
Работает на Amvera с правильным HTTPS вебхуком

ВЕРСИЯ 3.0:
✅ WEBHOOK режим (работает 24/7 на Amvera)
✅ Отправка заявок администратору (БЕЗ JSON сохранения)
✅ Все картинки загружены
✅ Просьба подписаться на группу с кнопкой
✅ Production Ready
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
ADMIN_ID = 5906447819  # @secereon
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

# Данные игр
GAMES = {
    "catan": {"name": "🎲 Катан", "emoji": "🎲"},
    "carcassonne": {"name": "🏰 Каркассон", "emoji": "🏰"},
    "dnd": {"name": "🐉 D&D", "emoji": "🐉"}
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
    """Нажата кнопка 'Зарегистрироваться' — выбор игры"""
    logger.info(f"📋 Регистрация начата: {query.from_user.username or query.from_user.first_name}")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Катан", callback_data="game_catan")],
        [InlineKeyboardButton(text="🏰 Каркассон", callback_data="game_carcassonne")],
        [InlineKeyboardButton(text="🐉 D&D", callback_data="game_dnd")]
    ])
    
    text = "🎮 Выбери игру для регистрации:"
    
    try:
        if image_exists(IMAGES["atmosphere"]):
            await bot.edit_message_media(
                chat_id=query.message.chat.id,
                message_id=query.message.message_id,
                media=types.InputMediaPhoto(
                    media=types.FSInputFile(IMAGES["atmosphere"])
                )
            )
            await bot.edit_message_caption(
                chat_id=query.message.chat.id,
                message_id=query.message.message_id,
                caption=text,
                reply_markup=keyboard
            )
        else:
            await query.message.edit_text(text, reply_markup=keyboard)
    except Exception as e:
        logger.warning(f"⚠️  Ошибка редактирования сообщения: {e}")
        await query.message.answer(text, reply_markup=keyboard)
    
    await query.answer()


# Обработчики выбора игры
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
        if image_exists(IMAGES[game]):
            await bot.edit_message_media(
                chat_id=query.message.chat.id,
                message_id=query.message.message_id,
                media=types.InputMediaPhoto(
                    media=types.FSInputFile(IMAGES[game])
                )
            )
            await bot.edit_message_caption(
                chat_id=query.message.chat.id,
                message_id=query.message.message_id,
                caption=text,
                reply_markup=keyboard
            )
        else:
            await query.message.edit_text(text, reply_markup=keyboard)
    except Exception as e:
        logger.warning(f"⚠️  Ошибка редактирования сообщения: {e}")
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
            await bot.edit_message_media(
                chat_id=query.message.chat.id,
                message_id=query.message.message_id,
                media=types.InputMediaPhoto(
                    media=types.FSInputFile(IMAGES["confirmation"])
                )
            )
            await bot.edit_message_caption(
                chat_id=query.message.chat.id,
                message_id=query.message.message_id,
                caption=confirmation_text,
                reply_markup=keyboard
            )
        else:
            await query.message.edit_text(confirmation_text, reply_markup=keyboard)
    except Exception as e:
        logger.warning(f"⚠️  Ошибка редактирования сообщения: {e}")
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
    logger.info("🎮 Telegram Bot для Игрового Дня v3.0")
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

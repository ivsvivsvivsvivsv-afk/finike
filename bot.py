"""
🎮 TELEGRAM БОТ ДЛЯ ИГРОВОГО ДНЯ v2.1
Полнофункциональный бот с регистрацией и уведомлениями администратору
"""

import logging
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ═══════════════════════════════════════════════════════════════
# 📋 КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '8522444294:AAFAdm3c_5NnnLSVV4-h6R0iutmGJI2Q1bw')
ADMIN_ID = 5906447819  # 👈 ЗАМЕНИ НА СВОЙ ID (@secereon)
GROUP_LINK = 'https://t.me/+fgNNmx1VlntiMGUy'

# Данные реестра
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
REGISTRATIONS_FILE = DATA_DIR / 'registrations.json'

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 🎮 СОСТОЯНИЯ FSM
# ═══════════════════════════════════════════════════════════════

class RegistrationStates(StatesGroup):
    choosing_game = State()
    choosing_time = State()
    confirmation = State()

# ═══════════════════════════════════════════════════════════════
# 🎨 КЛАВИАТУРЫ
# ═══════════════════════════════════════════════════════════════

def get_main_menu():
    """Главное меню"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Зарегистрироваться")],
            [KeyboardButton(text="ℹ️ Об событии")],
            [KeyboardButton(text="🎲 О трёх играх")],
            [KeyboardButton(text="❓ Вопросы-ответы")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_games_menu():
    """Выбор игры"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏗️ Катан", callback_data="game_catan")],
            [InlineKeyboardButton(text="🏰 Каркассон", callback_data="game_carcassonne")],
            [InlineKeyboardButton(text="🐉 D&D", callback_data="game_dnd")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")],
        ]
    )
    return keyboard

def get_time_slots_menu():
    """Выбор времени"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕐 12:00-14:00", callback_data="time_12-14")],
            [InlineKeyboardButton(text="🕑 14:00-16:00", callback_data="time_14-16")],
            [InlineKeyboardButton(text="🕖 16:00-18:00", callback_data="time_16-18")],
            [InlineKeyboardButton(text="🕘 18:00-21:00", callback_data="time_18-21")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_games")],
        ]
    )
    return keyboard

def get_confirmation_menu():
    """Подтверждение"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📱 Перейти в группу", url=GROUP_LINK)],
            [InlineKeyboardButton(text="✅ Готово", callback_data="done")],
        ]
    )
    return keyboard

# ═══════════════════════════════════════════════════════════════
# 💾 РАБОТА С ДАННЫМИ
# ═══════════════════════════════════════════════════════════════

def load_registrations():
    """Загрузить регистрации"""
    if REGISTRATIONS_FILE.exists():
        with open(REGISTRATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_registration(data):
    """Сохранить новую регистрацию"""
    registrations = load_registrations()
    registrations.append(data)
    with open(REGISTRATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(registrations, f, ensure_ascii=False, indent=2)

# ═══════════════════════════════════════════════════════════════
# 📤 ОТПРАВКА КАРТИНКИ (С FALLBACK)
# ═══════════════════════════════════════════════════════════════

async def send_photo_or_text(bot: Bot, chat_id: int, image_name: str, caption: str, reply_markup=None):
    """
    Отправить картинку, если она есть, иначе только текст
    """
    image_path = Path(image_name)
    
    if image_path.exists():
        try:
            photo = FSInputFile(image_path)
            await bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return True
        except Exception as e:
            logger.warning(f"Ошибка отправки картинки {image_name}: {e}")
            # Fallback на текст
            await bot.send_message(
                chat_id=chat_id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return False
    else:
        # Картинка не найдена, отправляем только текст
        await bot.send_message(
            chat_id=chat_id,
            text=caption,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return False

# ═══════════════════════════════════════════════════════════════
# 👤 ИНФОРМАЦИЯ ОБ ИГРОКЕ (ДЛЯ АДМИНИСТРАТОРА)
# ═══════════════════════════════════════════════════════════════

def create_player_card(user_id, username, game, time_slot):
    """
    Создать карточку игрока для администратора
    """
    game_names = {
        'catan': '🏗️ Катан',
        'carcassonne': '🏰 Каркассон',
        'dnd': '🐉 D&D'
    }
    
    timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    
    card = f"""
🎮 <b>НОВАЯ РЕГИСТРАЦИЯ НА ИГРОВОЙ ДЕНЬ!</b>

👤 <b>Игрок:</b> @{username} (ID: {user_id})

🎯 <b>Выбранная игра:</b> {game_names.get(game, game)}

⏰ <b>Временной слот:</b> {time_slot}

📅 <b>Время регистрации:</b> {timestamp}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ <b>Статус:</b> Зарегистрирован
📊 <b>Всего игроков:</b> {len(load_registrations())}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    
    return card.strip()

# ═══════════════════════════════════════════════════════════════
# 🤖 ОБРАБОТЧИКИ КОМАНД
# ═══════════════════════════════════════════════════════════════

async def start(message: types.Message, state: FSMContext):
    """Команда /start"""
    await state.clear()
    
    welcome_text = """
<b>🎮 ДОБРО ПОЖАЛОВАТЬ НА ИГРОВОЙ ДЕНЬ В ФИНИКЕ!</b>

Суббота — первое официальное мероприятие русскоговорящего комьюнити! 🎉

<b>📍 Кафе Марина Джим, Финика</b>
<b>⏰ 12:00 - 20:00</b>
<b>💰 БЕСПЛАТНО!</b>

Три стола, три уникальных игры, множество новых знакомств! ✨

👇 <b>Выбери действие:</b>
    """
    
    await send_photo_or_text(
        bot=message.bot,
        chat_id=message.chat.id,
        image_name='bot_welcome_banner.png',
        caption=welcome_text,
        reply_markup=get_main_menu()
    )
    logger.info(f"👤 Пользователь {message.from_user.username} (ID: {message.from_user.id}) запустил бот")

async def help_command(message: types.Message):
    """Команда /help"""
    help_text = """
<b>❓ СПРАВКА:</b>

<b>📋 Зарегистрироваться</b>
Зарегистрируйся на свою любимую игру и выбери удобное время!

<b>ℹ️ Об событии</b>
Полная информация о мероприятии, месте и времени.

<b>🎲 О трёх играх</b>
Узнай о каждой игре подробнее.

<b>❓ Вопросы-ответы</b>
Ответы на частые вопросы.

━━━━━━━━━━━━━━━━━━━━━━

<b>Команды:</b>
/start - Главное меню
/help - Эта справка
/register - Быстрая регистрация
    """
    
    await message.reply(help_text, parse_mode='HTML')

async def handle_main_menu(message: types.Message, state: FSMContext):
    """Обработчик главного меню"""
    text = message.text
    
    if text == "📋 Зарегистрироваться":
        await state.set_state(RegistrationStates.choosing_game)
        await send_photo_or_text(
            bot=message.bot,
            chat_id=message.chat.id,
            image_name='bot_event_atmosphere.png',
            caption="<b>🎮 Выбери игру, на которую хочешь записаться:</b>",
            reply_markup=get_games_menu()
        )
    
    elif text == "ℹ️ Об событии":
        event_text = """
<b>🎮 ПЕРВЫЙ ИГРОВОЙ ДЕНЬ РУССКОГОВОРЯЩЕГО КОМЬЮНИТИ</b>

📍 <b>Место:</b> Кафе Марина Джим, Финика

📅 <b>Дата:</b> Суббота

⏰ <b>Время:</b> 12:00 - 20:00 (свободный вход/выход)

💰 <b>Стоимость:</b> БЕСПЛАТНО!

☕ Поддержка: Закажи чай или кофе в кафе

━━━━━━━━━━━━━━━━━━━━━━

<b>3 СТОЛА, 3 ИГРЫ:</b>

🏗️ <b>Стол 1: КАТАН</b> (симулятор экономики)
Уникальная версия с гигантской картой и AI балансировкой!

🏰 <b>Стол 2: КАРКАССОН</b> (конструктор ландшафта)
Быстрые партии, легко учиться!

🐉 <b>Стол 3: D&D</b> (эпические приключения)
Демо-погружение в фэнтази мир!

━━━━━━━━━━━━━━━━━━━━━━

✨ Не нужен опыт — всё объясним!
✨ Свободный формат — приходи когда угодно
✨ Новые знакомства и крутая атмосфера

👇 Зарегистрируйся и присоединяйся!
        """
        await message.reply(event_text, parse_mode='HTML')
    
    elif text == "🎲 О трёх играх":
        games_text = """
<b>🎲 ПОДРОБНО О КАЖДОЙ ИГРЕ:</b>

━━━━━━━━━━━━━━━━━━━━━━

🏗️ <b>КАТАН — "Экономический тренажёр"</b>

Ты поселенец на острове. Собираешь ресурсы, строишь города, торгуешься с соперниками.

Партии: 60-90 минут
Игроков: до 8 одновременно
Стратегия: ✅ Дипломатия: ✅ Азарт: ✅

🌟 На нашем столе: УНИКАЛЬНАЯ версия с гигантской картой и AI балансировкой!

━━━━━━━━━━━━━━━━━━━━━━

🏰 <b>КАРКАССОН — "Конструктор средневековья"</b>

Как LEGO для средневекового ландшафта! Тянешь плитку, раскладываешь её, строишь города и дороги.

Партии: 30-45 минут
Игроков: до 6
Сложность: Простая!

✅ За 5 минут выучить правила
✅ За 10 минут сыграть первую партию
✅ Можно играть несколько партий подряд

Идеально для первого знакомства с настолками!

━━━━━━━━━━━━━━━━━━━━━━

🐉 <b>D&D — "Эпическое приключение"</b>

Это не игра, это РАССКАЗ, который вы создаёте вместе!

Ты создаёшь персонажа и входишь в подземелье. Мастер описывает мир, ты решаешь, что делать. Кубики определяют удачу. История развивается в реальном времени.

🎭 Это рольевая игра. Это творчество!

На столе в субботу:
✅ Подержишь фигурки и кубики
✅ Посмотришь листы персонажей
✅ Услышишь сценки от мастера
✅ Поймёшь, нравится ли тебе этот мир

📢 Первый раз = долгое объяснение. Но оно того стоит! 🗡️

━━━━━━━━━━━━━━━━━━━━━━

👇 Готов записаться? Жми "Зарегистрироваться"!
        """
        await message.reply(games_text, parse_mode='HTML')
    
    elif text == "❓ Вопросы-ответы":
        faq_text = """
<b>❓ ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ:</b>

<b>Q: Нужен ли опыт в настольных играх?</b>
A: Нет! Мы расскажем всё с нуля. Даже если ты никогда не играл.

<b>Q: Сколько это стоит?</b>
A: БЕСПЛАТНО! Только поддержи кафе заказом чая или кофе.

<b>Q: Я могу прийти на час?</b>
A: Да! Свободный вход/выход с 12:00 до 20:00.

<b>Q: Сколько человек будет?</b>
A: Неизвестно. Зависит от регистраций. Но будет весело! 😄

<b>Q: Какие игры подходят детям?</b>
A: Каркассон (от 7 лет). Катан (от 10 лет). D&D (от 12 лет).

<b>Q: Я новичок в D&D. Смогу ли я?</b>
A: Да! Мы сделаем демо-сценарий специально для новичков.

<b>Q: Где это? Как туда добраться?</b>
A: Кафе Марина Джим в Финике. Спроси в Гугл Картах.

<b>Q: Что брать с собой?</b>
A: Только себя! Всё остальное есть.

━━━━━━━━━━━━━━━━━━━━━━

Остались вопросы? Напиши в Telegram группу! 👇
https://t.me/+fgNNmx1VlntiMGUy
        """
        await message.reply(faq_text, parse_mode='HTML')

# ═══════════════════════════════════════════════════════════════
# 🎮 ОБРАБОТЧИКИ CALLBACK (РЕГИСТРАЦИЯ)
# ═══════════════════════════════════════════════════════════════

async def process_game_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора игры"""
    
    if callback.data == "back_to_menu":
        await state.clear()
        await callback.message.delete()
        await callback.message.answer(
            "Вернулся в главное меню 👇",
            reply_markup=get_main_menu()
        )
        return
    
    game = callback.data.replace("game_", "")
    game_names = {
        'catan': '🏗️ Катан',
        'carcassonne': '🏰 Каркассон',
        'dnd': '🐉 D&D'
    }
    
    await state.update_data(game=game)
    await state.set_state(RegistrationStates.choosing_time)
    
    await callback.message.delete()
    
    image_names = {
        'catan': 'bot_catan_visual.png',
        'carcassonne': 'bot_carcassonne_visual.png',
        'dnd': 'bot_dnd_visual.png'
    }
    
    await send_photo_or_text(
        bot=callback.bot,
        chat_id=callback.from_user.id,
        image_name=image_names.get(game, ''),
        caption=f"<b>Отлично! Ты выбрал {game_names.get(game, game)}</b>\n\n"
                f"Теперь выбери удобное время 👇",
        reply_markup=get_time_slots_menu()
    )
    
    logger.info(f"👤 {callback.from_user.username} выбрал игру: {game}")

async def process_time_selection(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора времени"""
    
    if callback.data == "back_to_games":
        await state.set_state(RegistrationStates.choosing_game)
        await callback.message.delete()
        await send_photo_or_text(
            bot=callback.bot,
            chat_id=callback.from_user.id,
            image_name='bot_event_atmosphere.png',
            caption="<b>🎮 Выбери игру, на которую хочешь записаться:</b>",
            reply_markup=get_games_menu()
        )
        return
    
    time_slot = callback.data.replace("time_", "").replace("-", ":") + ":00"
    # Форматирование времени
    time_display = callback.data.replace("time_", "").replace("-", ":") + "-" + callback.data.replace("time_", "").split("-")[1] + ":00"
    
    user_data = await state.get_data()
    user_data['time_slot'] = time_display
    
    # Сохраняем регистрацию
    registration_data = {
        'user_id': callback.from_user.id,
        'username': callback.from_user.username or 'unknown',
        'game': user_data.get('game'),
        'time_slot': time_display,
        'timestamp': datetime.now().isoformat()
    }
    
    save_registration(registration_data)
    
    # Отправляем карточку администратору
    admin_card = create_player_card(
        callback.from_user.id,
        callback.from_user.username or 'unknown',
        user_data.get('game'),
        time_display
    )
    
    try:
        await callback.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_card,
            parse_mode='HTML'
        )
        logger.info(f"📊 Уведомление администратору отправлено для {callback.from_user.username}")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления администратору: {e}")
    
    # Подтверждение для пользователя
    await callback.message.delete()
    
    confirmation_text = f"""
<b>✅ СПАСИБО ЗА РЕГИСТРАЦИЮ!</b>

📋 <b>Детали вашей регистрации:</b>

🎮 <b>Игра:</b> {user_data.get('game')}
⏰ <b>Время:</b> {time_display}
👤 <b>Игрок:</b> @{callback.from_user.username}

━━━━━━━━━━━━━━━━━━━━━━

<b>🔔 ВАЖНО:</b>

Присоединись к группе для обсуждения деталей и координации:

👇 Жми кнопку ниже 👇
    """
    
    await send_photo_or_text(
        bot=callback.bot,
        chat_id=callback.from_user.id,
        image_name='bot_confirmation_scroll.png',
        caption=confirmation_text,
        reply_markup=get_confirmation_menu()
    )
    
    logger.info(f"✅ {callback.from_user.username} зарегистрирован на {user_data.get('game')} на {time_display}")

async def process_done(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Готово'"""
    await state.clear()
    await callback.message.delete()
    
    final_text = """
<b>🎉 ВСЁ ГОТОВО!</b>

Ты записан на игровой день! 🎮

Увидимся в субботу в кафе Марина Джим! ⚔️

📍 Кафе Марина Джим, Финика
⏰ 12:00 - 20:00
🎲 Катан | Каркассон | D&D

Если вопросы — напиши в группе! 👇
    """
    
    await callback.message.answer(
        final_text,
        reply_markup=get_main_menu(),
        parse_mode='HTML'
    )

# ═══════════════════════════════════════════════════════════════
# 🚀 ИНИЦИАЛИЗАЦИЯ БОТА
# ═══════════════════════════════════════════════════════════════

async def main():
    """Главная функция"""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    bot = Bot(token=BOT_TOKEN)
    
    # Регистрация обработчиков команд
    dp.message.register(start, Command("start"))
    dp.message.register(help_command, Command("help"))
    
    # Регистрация обработчиков текста
    dp.message.register(handle_main_menu)
    
    # Регистрация callback обработчиков
    dp.callback_query.register(process_game_selection, F.data.startswith("game_") | F.data == "back_to_menu")
    dp.callback_query.register(process_time_selection, F.data.startswith("time_") | F.data == "back_to_games")
    dp.callback_query.register(process_done, F.data == "done")
    
    try:
        logger.info("🎮 Бот запущен!")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

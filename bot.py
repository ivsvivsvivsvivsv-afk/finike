import logging
import json
import os
from pathlib import Path
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.command import Command
import asyncio
from datetime import datetime

# ============= КОНФИГУРАЦИЯ И ЗАГРУЗКА ДАННЫХ =============
class Config:
    def __init__(self):
        self.config_path = Path("config.json")
        self.texts_path = Path("texts.json")
        
        # Загружаем конфиг
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        
        # Загружаем тексты
        with open(self.texts_path, "r", encoding="utf-8") as f:
            self.texts = json.load(f)
        
        self.BOT_TOKEN = self.config["bot"]["token"]
        self.IMAGES = self.config["images"]
        self.EVENT = self.config["event"]
        self.STORAGE_FILE = self.config["storage"]["file"]
    
    def get_text(self, key, **kwargs):
        """Получить текст по ключу с подставлением переменных"""
        try:
            text = self.texts[key]["text"]
            # Заменяем переменные в формате {NAME}, {GAMES} и т.д.
            for placeholder, value in kwargs.items():
                text = text.replace(f"{{{placeholder}}}", str(value))
            return text
        except KeyError:
            return f"[Текст не найден: {key}]"
    
    def reload(self):
        """Перезагрузить конфиг и тексты (для hot-reload)"""
        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)
        with open(self.texts_path, "r", encoding="utf-8") as f:
            self.texts = json.load(f)
        logger.info("✅ Конфиг и тексты перезагружены!")

config = Config()

# ============= ЛОГИРОВАНИЕ =============
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============= ИНИЦИАЛИЗАЦИЯ БОТА =============
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# ============= СОСТОЯНИЯ (FSM) =============
class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_game_choice = State()
    waiting_for_confirmation = State()

# ============= ХРАНИЛИЩЕ ДАННЫХ =============
class RegistrationStorage:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text(json.dumps([], ensure_ascii=False, indent=2), encoding="utf-8")
    
    def add(self, registration):
        """Добавить регистрацию"""
        registrations = self.get_all()
        registrations.append(registration)
        self.file_path.write_text(json.dumps(registrations, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def get_all(self):
        """Получить все регистрации"""
        try:
            return json.loads(self.file_path.read_text(encoding="utf-8"))
        except:
            return []

storage = RegistrationStorage(config.STORAGE_FILE)

# ============= КЛАВИАТУРЫ =============
def get_main_menu_keyboard():
    """Главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ℹ️ Об игровом дне", callback_data="about")],
        [InlineKeyboardButton(text="📋 Зарегистрироваться", callback_data="register")],
        [InlineKeyboardButton(text="🎲 О трёх играх", callback_data="games_list")],
        [InlineKeyboardButton(text="❓ Вопросы и ответы", callback_data="faq")],
    ])

def get_gender_keyboard():
    """Выбор пола"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")],
            [KeyboardButton(text="Предпочитаю не указывать")]
        ],
        resize_keyboard=True
    )

def get_games_keyboard():
    """Выбор игры"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏗️ Катан (Catan)", callback_data="game_catan")],
        [InlineKeyboardButton(text="🏰 Каркассон (Carcassonne)", callback_data="game_carcassonne")],
        [InlineKeyboardButton(text="🐉 D&D (Dungeons & Dragons)", callback_data="game_dnd")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])

def get_confirmation_keyboard():
    """Подтверждение регистрации"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить регистрацию", callback_data="confirm_registration")],
        [InlineKeyboardButton(text="🔄 Начать заново", callback_data="restart")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
    ])

def get_game_selection_keyboard():
    """Клавиатура для выбора игр во время регистрации"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏗️ Катан", callback_data="select_catan")],
        [InlineKeyboardButton(text="🏰 Каркассон", callback_data="select_carcassonne")],
        [InlineKeyboardButton(text="🐉 D&D", callback_data="select_dnd")],
        [InlineKeyboardButton(text="✅ Готово, давай дальше", callback_data="games_selected")]
    ])

# ============= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =============
async def send_photo_with_fallback(message_or_query, image_key, caption, reply_markup=None, parse_mode="Markdown", is_edit=False):
    """Отправить фото с fallback на текст"""
    try:
        image_path = config.IMAGES.get(image_key)
        if image_path and os.path.exists(image_path):
            image = FSInputFile(image_path)
            if hasattr(message_or_query, 'message'):  # callback_query
                await message_or_query.message.delete()
                await message_or_query.message.chat.send_photo(
                    photo=image,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            else:  # message
                await message_or_query.answer_photo(
                    photo=image,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
        else:
            raise FileNotFoundError(f"Изображение не найдено: {image_path}")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка при отправке фото: {e}. Отправляю текст.")
        if hasattr(message_or_query, 'message'):  # callback_query
            await message_or_query.message.edit_text(caption, reply_markup=reply_markup, parse_mode=parse_mode)
        else:  # message
            await message_or_query.answer(caption, reply_markup=reply_markup, parse_mode=parse_mode)

# ============= КОМАНДЫ =============
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start"""
    text = config.get_text("welcome")
    await send_photo_with_fallback(
        message,
        "welcome",
        text,
        reply_markup=get_main_menu_keyboard()
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Команда /help"""
    text = config.get_text("help")
    await message.answer(text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")

@dp.message(Command("reload"))
async def cmd_reload(message: types.Message):
    """Команда /reload (только для тестирования)"""
    config.reload()
    await message.answer("✅ Конфиг и тексты перезагружены!")

# ============= CALLBACK-ОБРАБОТЧИКИ =============
@dp.callback_query(F.data == "about")
async def callback_about(query: types.CallbackQuery):
    """Об игровом дне"""
    text = config.get_text("about")
    await send_photo_with_fallback(
        query,
        "event_atmosphere",
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ])
    )
    await query.answer()

@dp.callback_query(F.data == "games_list")
async def callback_games_list(query: types.CallbackQuery):
    """Список игр"""
    text = config.get_text("games_list")
    await query.message.edit_text(text, reply_markup=get_games_keyboard(), parse_mode="Markdown")
    await query.answer()

@dp.callback_query(F.data == "game_catan")
async def callback_game_catan(query: types.CallbackQuery):
    """Описание Катана"""
    text = config.get_text("catan")
    await send_photo_with_fallback(
        query,
        "catan",
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Зарегистрироваться на Катан", callback_data="register_catan")],
            [InlineKeyboardButton(text="🔙 Назад к играм", callback_data="games_list")]
        ])
    )
    await query.answer()

@dp.callback_query(F.data == "game_carcassonne")
async def callback_game_carcassonne(query: types.CallbackQuery):
    """Описание Каркассона"""
    text = config.get_text("carcassonne")
    await send_photo_with_fallback(
        query,
        "carcassonne",
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Зарегистрироваться на Каркассон", callback_data="register_carcassonne")],
            [InlineKeyboardButton(text="🔙 Назад к играм", callback_data="games_list")]
        ])
    )
    await query.answer()

@dp.callback_query(F.data == "game_dnd")
async def callback_game_dnd(query: types.CallbackQuery):
    """Описание D&D"""
    text = config.get_text("dnd")
    await send_photo_with_fallback(
        query,
        "dnd",
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Зарегистрироваться на D&D", callback_data="register_dnd")],
            [InlineKeyboardButton(text="🔙 Назад к играм", callback_data="games_list")]
        ])
    )
    await query.answer()

@dp.callback_query(F.data == "faq")
async def callback_faq(query: types.CallbackQuery):
    """FAQ"""
    text = config.get_text("faq")
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]), parse_mode="Markdown")
    await query.answer()

# ============= РЕГИСТРАЦИЯ =============
@dp.callback_query(F.data == "register")
async def callback_register(query: types.CallbackQuery, state: FSMContext):
    """Начало регистрации"""
    text = config.get_text("registration_start")
    await query.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(RegistrationStates.waiting_for_name)
    await query.answer()

@dp.message(RegistrationStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    """Получаем имя"""
    await state.update_data(name=message.text, telegram_username=message.from_user.username or "не указан")
    text = config.get_text("registration_age")
    await message.answer(text, reply_markup=types.ReplyKeyboardRemove(), parse_mode="Markdown")
    await state.set_state(RegistrationStates.waiting_for_age)

@dp.message(RegistrationStates.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    """Получаем возраст"""
    try:
        age = int(message.text)
        if 1 <= age <= 120:
            await state.update_data(age=age)
            text = config.get_text("registration_gender")
            await message.answer(text, reply_markup=get_gender_keyboard(), parse_mode="Markdown")
            await state.set_state(RegistrationStates.waiting_for_gender)
        else:
            await message.answer(config.get_text("alerts", key="age_error"), parse_mode="Markdown")
    except ValueError:
        await message.answer(config.get_text("alerts", key="invalid_age_format"), parse_mode="Markdown")

@dp.message(RegistrationStates.waiting_for_gender)
async def process_gender(message: types.Message, state: FSMContext):
    """Получаем пол"""
    gender = message.text
    if gender not in ["Мужской", "Женский", "Предпочитаю не указывать"]:
        await message.answer(config.get_text("alerts", key="invalid_gender"), parse_mode="Markdown")
        return
    
    await state.update_data(gender=gender)
    text = config.get_text("registration_games")
    await message.answer(
        text,
        reply_markup=get_game_selection_keyboard(),
        parse_mode="Markdown",
    )
    await state.set_state(RegistrationStates.waiting_for_game_choice)
    await state.update_data(selected_games=[])

@dp.callback_query(RegistrationStates.waiting_for_game_choice, F.data == "select_catan")
async def select_catan(query: types.CallbackQuery, state: FSMContext):
    """Выбор Катана"""
    data = await state.get_data()
    games = data.get("selected_games", [])
    if "Катан" not in games:
        games.append("Катан")
        await state.update_data(selected_games=games)
        alert_text = config.get_text("alerts", key="game_added", GAME="Катан")
        await query.answer(text=alert_text, show_alert=False)
    else:
        alert_text = config.get_text("alerts", key="game_already_added", GAME="Катан")
        await query.answer(text=alert_text, show_alert=False)

@dp.callback_query(RegistrationStates.waiting_for_game_choice, F.data == "select_carcassonne")
async def select_carcassonne(query: types.CallbackQuery, state: FSMContext):
    """Выбор Каркассона"""
    data = await state.get_data()
    games = data.get("selected_games", [])
    if "Каркассон" not in games:
        games.append("Каркассон")
        await state.update_data(selected_games=games)
        alert_text = config.get_text("alerts", key="game_added", GAME="Каркассон")
        await query.answer(text=alert_text, show_alert=False)
    else:
        alert_text = config.get_text("alerts", key="game_already_added", GAME="Каркассон")
        await query.answer(text=alert_text, show_alert=False)

@dp.callback_query(RegistrationStates.waiting_for_game_choice, F.data == "select_dnd")
async def select_dnd(query: types.CallbackQuery, state: FSMContext):
    """Выбор D&D"""
    data = await state.get_data()
    games = data.get("selected_games", [])
    if "D&D" not in games:
        games.append("D&D")
        await state.update_data(selected_games=games)
        alert_text = config.get_text("alerts", key="game_added", GAME="D&D")
        await query.answer(text=alert_text, show_alert=False)
    else:
        alert_text = config.get_text("alerts", key="game_already_added", GAME="D&D")
        await query.answer(text=alert_text, show_alert=False)

@dp.callback_query(RegistrationStates.waiting_for_game_choice, F.data == "games_selected")
async def games_selected(query: types.CallbackQuery, state: FSMContext):
    """Проверка, выбраны ли игры"""
    data = await state.get_data()
    games = data.get("selected_games", [])
    
    if not games:
        await query.answer(text=config.get_text("alerts", key="no_games_selected"), show_alert=True)
        return
    
    games_str = "\n".join([f"• {g}" for g in games])
    confirmation_text = f"""
✅ *ПОДТВЕРДИ РЕГИСТРАЦИЮ ГЕРОЯ!*

⚔️ *Имя/Ник:* {data['name']}
📅 *Возраст:* {data['age']}
👤 *Пол:* {data['gender']}
📱 *Telegram:* @{data['telegram_username']}

🎲 *Выбранные игры:*
{games_str}

Всё правильно? Или нужны изменения?
"""
    await query.message.edit_text(confirmation_text, reply_markup=get_confirmation_keyboard(), parse_mode="Markdown")
    await state.set_state(RegistrationStates.waiting_for_confirmation)
    await query.answer()

@dp.callback_query(RegistrationStates.waiting_for_confirmation, F.data == "confirm_registration")
async def confirm_registration(query: types.CallbackQuery, state: FSMContext):
    """Подтверждение регистрации"""
    data = await state.get_data()
    
    registration_record = {
        "name": data['name'],
        "age": data['age'],
        "gender": data['gender'],
        "telegram": data['telegram_username'],
        "user_id": query.from_user.id,
        "games": data['selected_games'],
        "timestamp": datetime.now().isoformat()
    }
    storage.add(registration_record)
    
    success_text = config.get_text("registration_success", NAME=data['name'].upper(), GAMES=", ".join(data['selected_games']))
    
    await send_photo_with_fallback(
        query,
        "confirmation",
        success_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Главное меню", callback_data="back_to_main")]
        ])
    )
    
    await state.clear()
    await query.answer()

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(query: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    text = config.get_text("welcome")
    await send_photo_with_fallback(
        query,
        "welcome",
        text,
        reply_markup=get_main_menu_keyboard()
    )
    await state.clear()
    await query.answer()

@dp.callback_query(F.data == "restart")
async def restart_registration(query: types.CallbackQuery, state: FSMContext):
    """Перезагрузка регистрации"""
    await state.clear()
    text = config.get_text("registration_start")
    await query.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(RegistrationStates.waiting_for_name)
    await query.answer()

# ============= ПРОЧИЕ СООБЩЕНИЯ =============
@dp.message()
async def echo_message(message: types.Message):
    """Обработка неизвестных сообщений"""
    text = config.get_text("unknown_command")
    await message.answer(text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")

# ============= ЗАПУСК БОТА =============
async def main():
    """Запуск бота"""
    logger.info("🤖 Бот запущен! Токен: " + config.BOT_TOKEN[:20] + "...")
    logger.info("📁 Хранилище регистраций: " + config.STORAGE_FILE)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())

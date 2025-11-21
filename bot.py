import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Импортируем наш класс работы с файлами
from database import DataManager

# --- НАСТРОЙКИ ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_DIR = os.getenv("DATA_DIR")

# Проверка переменных
if not BOT_TOKEN or not DATA_DIR:
    print("CRITICAL ERROR: .env file is missing or incomplete!")
    print("Please check BOT_TOKEN and DATA_DIR variables.")
    sys.exit(1)

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = DataManager(DATA_DIR)

# Клавиатура капчи
def get_captcha_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="3", callback_data="wrong"),
        InlineKeyboardButton(text="4", callback_data="correct"),
        InlineKeyboardButton(text="5", callback_data="wrong")
    ]])

# --- ХЕНДЛЕР 1: Входящая заявка ---
@dp.chat_join_request()
async def handle_join(update: ChatJoinRequest):
    user_id = update.from_user.id
    lang = update.from_user.language_code or 'en'
    
    # 1. Фильтр по языку (Гео-фильтр)
    # Отсекаем Индонезию, Вьетнам, Арабские страны, Индию, Иран
    if lang in ['id', 'vi', 'ar', 'hi', 'fa']:
        return 

    # 2. Принимаем заявку в канал (Approve)
    try:
        await update.approve()
    except Exception as e:
        print(f"Approve error for {user_id}: {e}")
        return

    # 3. Достаем хеш ссылки и ищем YCLID
    try:
        full_link = update.invite_link.invite_link
        # Берем всё что после последнего + или /
        invite_hash = full_link.split('+')[-1] if '+' in full_link else full_link.split('/')[-1]
    except:
        invite_hash = "unknown"

    # Ищем в файле leads.txt
    yclid = db.find_yclid_by_hash(invite_hash)
    
    if yclid:
        # Если нашли - запоминаем во временный файл
        db.save_temp_link(user_id, yclid)
    else:
        print(f"⚠️ User {user_id} joined, but Hash {invite_hash} not found in leads.txt")
    
    # 4. Отправляем капчу в личку
    try:
        await bot.send_message(
            chat_id=user_id,
            text="👋 Добро пожаловать! Чтобы подтвердить, что вы человек, решите пример:\n\n<b>Сколько будет 2 + 2?</b>",
            reply_markup=get_captcha_kb(),
            parse_mode="HTML"
        )
    except Exception as e:
        # Юзер мог заблокировать бота или настройки приватности
        print(f"Could not send captcha to {user_id}: {e}")

# --- ХЕНДЛЕР 2: Правильный ответ ---
@dp.callback_query(F.data == "correct")
async def captcha_correct(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # Убираем кнопки
    await callback.message.edit_text("✅ Проверка пройдена! Приятного чтения.")
    
    # Достаем YCLID из временного файла
    yclid = db.get_yclid_from_temp(user_id)
    
    if yclid:
        # Сохраняем в список для отправки в Яндекс
        db.save_verified_user(user_id, yclid)
        print(f"✅ VERIFIED: User {user_id} -> Yclid {yclid} -> Saved to queue.")
    else:
        print(f"⚠️ WARNING: User {user_id} solved captcha, but YCLID is missing.")

# --- ХЕНДЛЕР 3: Неправильный ответ ---
@dp.callback_query(F.data == "wrong")
async def captcha_wrong(callback: CallbackQuery):
    await callback.answer("Ошибка! Попробуйте еще раз.", show_alert=True)

# --- ЗАПУСК ---
async def main():
    print("--- Bot Started ---")
    print(f"Watching data dir: {DATA_DIR}")
    # Сбрасываем старые апдейты (чтобы не отвечать на старые нажатия при рестарте)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

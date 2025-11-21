import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database import DataManager

# --- КОНФИГ ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_DIR = os.getenv("DATA_DIR")

if not BOT_TOKEN or not DATA_DIR:
    print("ERROR: Check .env file!")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = DataManager(DATA_DIR)

def get_captcha_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="3", callback_data="wrong"),
        InlineKeyboardButton(text="4", callback_data="correct"),
        InlineKeyboardButton(text="5", callback_data="wrong")
    ]])

# --- Хендлер 1: Вступление ---
@dp.chat_join_request()
async def handle_join(update: ChatJoinRequest):
    user_id = update.from_user.id
    lang = update.from_user.language_code or 'en'
    
    # 1. Фильтр языка (Опционально, можно убрать для теста)
    if lang in ['id', 'vi', 'ar', 'hi', 'fa']:
        return 

    # 2. Принимаем
    try: await update.approve()
    except: return

    # 3. Ищем YCLID
    try:
        full_link = update.invite_link.invite_link
        invite_hash = full_link.split('+')[-1] if '+' in full_link else full_link.split('/')[-1]
    except:
        invite_hash = "unknown"

    yclid = db.find_yclid_by_hash(invite_hash)
    
    if yclid:
        db.save_temp_link(user_id, yclid) # Запоминаем связку
    else:
        print(f"⚠️ Yclid not found for hash {invite_hash}")

    # 4. Шлем капчу
    try:
        await bot.send_message(
            chat_id=user_id,
            text="👋 Добро пожаловать! Чтобы подтвердить, что вы человек, решите пример:\n\n<b>Сколько будет 2 + 2?</b>",
            reply_markup=get_captcha_kb(),
            parse_mode="HTML"
        )
    except: pass

# --- Хендлер 2: Успех ---
@dp.callback_query(F.data == "correct")
async def captcha_correct(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # Убираем кнопки
    await callback.message.edit_text("✅ Проверка пройдена! Приятного чтения.")
    
    # Достаем YCLID
    yclid = db.get_yclid_from_temp(user_id)
    
    if yclid:
        # !!! СРАЗУ ПИШЕМ В ФАЙЛ НА ОТПРАВКУ (Без ожидания 2 часов) !!!
        db.save_verified_user(user_id, yclid)
        print(f"✅ VERIFIED: User {user_id} -> Yclid {yclid} -> Saved to queue.")
    else:
        print(f"⚠️ User {user_id} solved captcha, but YCLID missing.")

# --- Хендлер 3: Ошибка ---
@dp.callback_query(F.data == "wrong")
async def captcha_wrong(callback: CallbackQuery):
    await callback.answer("Ошибка! Попробуйте еще раз.", show_alert=True)

async def main():
    print("--- Bot Started (Lite Version) ---")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

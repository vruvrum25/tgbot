import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import DataManager

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_DIR = os.getenv("DATA_DIR")

if not BOT_TOKEN or not DATA_DIR:
    print("ERROR: .env is empty!")
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

@dp.chat_join_request()
async def handle_join(update: ChatJoinRequest):
    user_id = update.from_user.id
    lang = update.from_user.language_code or 'en'
    
    # Фильтр гео
    if lang in ['id', 'vi', 'ar', 'hi', 'fa']: return 

    try: await update.approve()
    except: return

    try:
        full_link = update.invite_link.invite_link
        invite_hash = full_link.split('+')[-1] if '+' in full_link else full_link.split('/')[-1]
    except: invite_hash = "unknown"

    yclid = db.find_yclid_by_hash(invite_hash)
    if yclid:
        db.save_temp_link(user_id, yclid)
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text="👋 Добро пожаловать! Чтобы подтвердить, что вы человек, решите пример:\n\n<b>Сколько будет 2 + 2?</b>",
            reply_markup=get_captcha_kb(),
            parse_mode="HTML"
        )
    except: pass

@dp.callback_query(F.data == "correct")
async def captcha_correct(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text("✅ Проверка пройдена! Приятного чтения.")
    
    yclid = db.get_yclid_from_temp(user_id)
    if yclid:
        # СРАЗУ СОХРАНЯЕМ ДЛЯ ЯНДЕКСА (БЕЗ ЗАДЕРЖКИ)
        db.save_verified_user(user_id, yclid)
        print(f"✅ VERIFIED: User {user_id} -> Yclid {yclid}")
    else:
        print(f"⚠️ User {user_id} solved captcha, but no YCLID found.")

@dp.callback_query(F.data == "wrong")
async def captcha_wrong(callback: CallbackQuery):
    await callback.answer("Ошибка!", show_alert=True)

async def main():
    print("--- Bot Started (Lite) ---")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

import asyncio
import sqlite3
import datetime
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

BOT_TOKEN = "8908688672:AAEqIbuLWciJJ_ahyLf4PekqqIsjrymUcUw" 
ADMIN_ID = 8870374351
WEB_APP_URL = "https://turayev9201-hue.github.io/JT-VPN/"
BANNER_FILE = "/root/banner_id.txt"

CARDS = [
    ("Uzcard", "20,000 so'm", "5614 6818 5290 5201"),
    ("Visa", "2$", "4231 2000 9704 3946"),
    ("Sberbank", "250₽", "2202 2023 2406 6681")
]

conn = sqlite3.connect('/root/vpn_users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, username TEXT, sub_end TEXT)''')
conn.commit()

class PaymentState(StatesGroup):
    waiting_for_chek = State()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("setbanner"))
async def set_banner(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    if not message.photo:
        await message.answer("⚠️ Rasmni yuborib, izohiga `/setbanner` deb yozing.")
        return
    with open(BANNER_FILE, 'w') as f:
        f.write(message.photo[-1].file_id)
    await message.answer("✅ Banner muvaffaqiyatli saqlandi!")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 To'lov qilish va Sotib Olish", callback_data="buy_vpn")],
        [InlineKeyboardButton(text="ℹ️ Ma'lumot va Yordam", callback_data="info")]
    ])
    
    text = (f"Assalomu alaykum, <b>{message.from_user.first_name}</b>! 👋\n\n"
            "🌟 <b>JT VPN</b> — Tezkor, xavfsiz va cheklovlarsiz internet dunyosi.\n\n"
            "✅ <b>Afzalliklar:</b>\n"
            "⚡️ Yuqori tezlik\n"
            "🛡️ To'liq xavfsizlik\n"
            "🌍 Niderlandiya serverlari\n"
            "📱 Barcha qurilmalarda ishlaydi\n\n"
            "👇 Boshlash uchun tugmani bosing:")

    if os.path.exists(BANNER_FILE):
        with open(BANNER_FILE, 'r') as f:
            banner_id = f.read().strip()
        try:
            await message.answer_photo(photo=banner_id, caption=text, reply_markup=kb, parse_mode="HTML")
            return
        except: pass
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "info")
async def show_info(callback: types.CallbackQuery):
    text = ("ℹ️ <b>JT VPN haqida</b>\n\n"
            "To'lovni amalga oshirib, shaxsiy VPN kalitingizni oling.\n\n"
            "💰 <b>Tarif:</b> 1 oylik — 20,000 so'm (2$ / 250₽)\n\n"
            "Savollar: @Asoschi_JT")
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "buy_vpn")
async def process_buy(callback: types.CallbackQuery, state: FSMContext):
    text = "💳 <b>To'lov qilish (1 oylik)</b>\n\nKartalardan biriga o'tkazing:\n━━━━━━━━━━━━━━━\n"
    for name, amount, card in CARDS:
        text += f"🏦 <b>{name}:</b> {amount}\n<code>{card}</code>\n━━━━━━━━━━━━━━━\n"
        
    text += "\n⚠️ <b>MUHIM:</b> Chekni (skrinshot) <b>shu chatga yuboring</b>. Admin tasdiqlashi bilan VPN kalitingiz beriladi."
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_start")]])
    await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(PaymentState.waiting_for_chek)
    await callback.answer()

@dp.callback_query(F.data == "back_start")
async def back_to_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await cmd_start(callback.message)

@dp.message(PaymentState.waiting_for_chek, F.photo)
async def handle_receipt(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "Noma'lum"
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{user_id}"),
         InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")]
    ])
    await bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id,
        caption=f"💰 <b>Yangi to'lov!</b>\n👤 @{username} (ID: <code>{user_id}</code>)", reply_markup=admin_kb, parse_mode="HTML")
    await message.answer("⏳ Chekingiz qabul qilindi. Admin tasdiqlashini kuting.")
    await state.clear()

@dp.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n⏳ <i>Tasdiqlanmoqda...</i>", parse_mode="HTML")
    
    try:
        sub_end_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT OR REPLACE INTO users (user_id, username, sub_end) VALUES (?, ?, ?)", (user_id, "mijoz", sub_end_date))
        conn.commit()

        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚀 Mening VPN'imni ochish", web_app=WebAppInfo(url=WEB_APP_URL))]])
        await bot.send_message(chat_id=user_id, text="🎉 <b>To'lovingiz tasdiqlandi!</b>\n\n1 oylik VPN faollashtirildi. Quyidagi tugma orqali kalitingizni oling.", reply_markup=kb, parse_mode="HTML")
        await callback.message.edit_caption(caption=callback.message.caption.replace("⏳ <i>Tasdiqlanmoqda...</i>", "✅ <i>Tasdiqlandi!</i>"), parse_mode="HTML")
    except Exception as e:
        await callback.message.answer(f"❌ Xatolik: {e}")
    await callback.answer()

@dp.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await bot.send_message(user_id, "❌ To'lovingiz tasdiqlanmadi. Admin bilan bog'laning.")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ <i>Rad etildi</i>", parse_mode="HTML")
    await callback.answer()

async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

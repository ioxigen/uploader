import asyncio
import random
import string
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiohttp import ClientConnectionError

# -------------------- تنظیمات --------------------
API_TOKEN = os.getenv("TOKEN")  # توکن ربات خودت
ADMIN_ID = os.getenv("ADMIN_ID")      # آیدی عددی ادمین

BASE_DIR = os.path.dirname(__file__)
JSON_FILE = os.path.join(BASE_DIR, "file_store.json")  # مسیر کامل برای JSON

# -------------------- آماده سازی JSON --------------------
if not os.path.exists(JSON_FILE):
    try:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    except Exception as e:
        print("❌ خطا در ایجاد فایل JSON:", e)

# بارگذاری اطلاعات قبلی
try:
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        file_store = json.load(f)
except Exception as e:
    print("❌ خطا در بارگذاری فایل JSON:", e)
    file_store = {}

# ذخیره فایل‌ها در JSON با مدیریت خطا
def save_json():
    try:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(file_store, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("❌ خطا هنگام ذخیره JSON:", e)

# -------------------- تولید کد تصادفی --------------------
def generate_key():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# -------------------- راه‌اندازی ربات --------------------
bot = Bot(token=API_TOKEN, timeout=30)  # timeout برای جلوگیری از قطع شبکه
dp = Dispatcher(bot)

# -------------------- حذف فایل و تغییر کپشن بعد از زمان --------------------
async def delete_file_after_delay(sent_file, sent_text, delay=15):
    await asyncio.sleep(delay)
    try:
        await sent_file.delete()
    except:
        pass
    try:
        await sent_text.edit_text(
            "❌ فایل پاک شد! برای دریافت مجدد روی دکمه زیر کلیک کنید.",
            reply_markup=sent_text.reply_markup
        )
    except:
        pass

# -------------------- دریافت ویدیو توسط ادمین --------------------
@dp.message_handler(content_types=['video'])
async def handle_admin_video(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        file_id = message.video.file_id
        key = generate_key()
        file_store[key] = {"file_id": file_id, "type": "video"}
        save_json()

        link = f"https://t.me/{(await bot.get_me()).username}?start={key}"
        await message.reply(f"✅ لینک ویدیو ساخته شد:\n{link}")
    except Exception as e:
        await message.reply(f"❌ خطا در دریافت ویدیو: {e}")

# -------------------- دریافت عکس توسط ادمین --------------------
@dp.message_handler(content_types=['photo'])
async def handle_admin_photo(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        file_id = message.photo[-1].file_id
        key = generate_key()
        file_store[key] = {"file_id": file_id, "type": "photo"}
        save_json()

        link = f"https://t.me/{(await bot.get_me()).username}?start={key}"
        await message.reply(f"✅ لینک عکس ساخته شد:\n{link}")
    except Exception as e:
        await message.reply(f"❌ خطا در دریافت عکس: {e}")

# -------------------- استارت با لینک توسط کاربر --------------------
@dp.message_handler(commands=['start'])
async def start_with_key(message: types.Message):
    args = message.get_args()
    if not args:
        return

    keys = args.split(",")
    for key in keys:
        if key in file_store:
            f = file_store[key]

            try:
                if f["type"] == "video":
                    sent_file = await message.answer_video(f["file_id"])
                else:
                    sent_file = await message.answer_photo(f["file_id"])

                kb = InlineKeyboardMarkup()
                kb.add(InlineKeyboardButton("🔁 دریافت مجدد فایل", callback_data=f"retry_{key}"))

                sent_text = await message.answer(
                    "⏳ این فایل تا ۱۵ ثانیه دیگر پاک می‌شود\nلطفاً این پیام را ذخیره کنید.",
                    reply_markup=kb
                )

                asyncio.create_task(delete_file_after_delay(sent_file, sent_text))
            except ClientConnectionError:
                await message.reply("❌ خطای شبکه! لطفاً دوباره تلاش کنید.")
            except Exception as e:
                await message.reply(f"❌ خطا در ارسال فایل: {e}")

# -------------------- دکمه دریافت مجدد --------------------
@dp.callback_query_handler(lambda c: c.data.startswith("retry_"))
async def retry_file(callback: types.CallbackQuery):
    key = callback.data.split("_")[1]

    if key in file_store:
        f = file_store[key]

        try:
            if f["type"] == "video":
                sent_file = await callback.message.answer_video(f["file_id"])
            else:
                sent_file = await callback.message.answer_photo(f["file_id"])

            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🔁 دریافت مجدد فایل", callback_data=f"retry_{key}"))

            sent_text = await callback.message.answer(
                "⏳ این فایل تا ۱۵ ثانیه دیگر پاک می‌شود\nلطفاً این پیام را ذخیره کنید.",
                reply_markup=kb
            )

            asyncio.create_task(delete_file_after_delay(sent_file, sent_text))
        except ClientConnectionError:
            await callback.message.answer("❌ خطای شبکه! لطفاً دوباره تلاش کنید.")
        except Exception as e:
            await callback.message.answer(f"❌ خطا در ارسال فایل: {e}")

    await callback.answer()

# -------------------- اجرای ربات --------------------
if __name__ == "__main__":
    print("🤖 Bot is running...")
    executor.start_polling(dp, skip_updates=True)

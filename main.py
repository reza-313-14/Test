import os
from pyrogram import Client, filters
from pyrogram.types import Message
from file_part import split_file
from rubika_client import rubika

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# for test
# proxy = {
#     "scheme": "http",
#     "hostname": "192.168.49.1",
#     "port": "8282"
# }

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOAD_PATH = "./downloads/"


@app.on_message(
    filters.document
    | filters.video
    | filters.photo
    | filters.audio
    | filters.voice
    | filters.video_note
    | filters.animation
    | filters.sticker
)
async def handle_file(client: Client, message: Message):

    try:
        status_msg = await message.reply("⏳ در حال دریافت فایل... لطفاً صبر کنید.")

        print(f"[DOWNLOAD] شروع دانلود فایل...")
        file_path = await message.download(file_name=DOWNLOAD_PATH)

        if file_path:
            print(f"[DOWNLOAD] فایل با موفقیت در {file_path} ذخیره شد.")

            await status_msg.edit_text(
                "✅ فایل دانلود شد. در حال ارسال به تابع upload..."
            )

            parts_list = split_file(file_path)
            for i in parts_list:
                rubika.send_file(i, "File")

    except Exception as e:
        print(f"[ERROR] خطا در پردازش فایل: {e}")
        await message.reply(f"❌ متأسفانه خطایی رخ داد:\n`{str(e)}`")


@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    welcome_text = (
        "👋 سلام! من ربات دانلود و آپلود فایل هستم.\n\n"
        "📎 هر فایلی برام بفرستی، دانلودش می‌کنم و برای آپلود به سرور ارسال می‌کنم.\n\n"
        "📂 فرمت‌های پشتیبانی شده:\n"
        "• اسناد (Document)\n"
        "• ویدیو (Video)\n"
        "• عکس (Photo)\n"
        "• صدا (Audio)\n"
        "• گیف (Animation)\n"
        "• استیکر (Sticker)\n"
        "• پیام صوتی (Voice)\n"
        "• ویدیو مسیج (Video Note)"
    )
    await message.reply(welcome_text)


@app.on_message()
async def other_messages(client: Client, message: Message):
    await message.reply("⚠️ لطفاً یک فایل ارسال کنید تا پردازش کنم.")


if name == "__main__":
    if not os.path.exists(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH)
        print(f"📁 پوشه {DOWNLOAD_PATH} ساخته شد.")

    print("🤖 ربات در حال اجرا...")
    app.run()

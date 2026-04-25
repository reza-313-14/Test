import os
import asyncio
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

# ایجاد صف برای مدیریت فایل‌ها
file_queue = asyncio.Queue()
is_processing = False


async def process_queue():
    """پردازش فایل‌های موجود در صف یکی یکی"""
    global is_processing

    while True:
        try:
            # گرفتن آیتم از صف
            task_data = await file_queue.get()

            if task_data is None:  # سیگنال توقف
                break

            client, message = task_data
            is_processing = True

            try:
                status_msg = await message.reply(
                    "⏳ در حال دریافت فایل... لطفاً صبر کنید."
                )

                print(f"[DOWNLOAD] شروع دانلود فایل از {message.from_user.id}...")
                file_path = await message.download(file_name=DOWNLOAD_PATH)

                if file_path:
                    print(f"[DOWNLOAD] فایل با موفقیت در {file_path} ذخیره شد.")

                    await status_msg.edit_text(
                        "✅ فایل دانلود شد. در حال ارسال به تابع upload..."
                    )

                    parts_list = split_file(file_path)
                    for i, part in enumerate(parts_list):
                        print(f"[UPLOAD] در حال آپلود بخش {i+1}/{len(parts_list)}...")
                        rubika.send_file(part, "File")

                    await status_msg.edit_text("✅ فایل با موفقیت پردازش و آپلود شد!")

                    # پاک کردن فایل موقت
                    try:
                        os.remove(file_path)
                        print(f"[CLEANUP] فایل موقت {file_path} پاک شد.")
                    except:
                        pass

            except Exception as e:
                print(f"[ERROR] خطا در پردازش فایل: {e}")
                try:
                    await message.reply(f"❌ متأسفانه خطایی رخ داد:\n`{str(e)}`")
                except:
                    pass

            # علامت‌گذاری آیتم به عنوان پردازش شده
            file_queue.task_done()
            is_processing = False

            # مکث کوتاه بین پردازش فایل‌ها
            await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[ERROR] خطا در پردازش صف: {e}")
            is_processing = False


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
    """اضافه کردن فایل به صف پردازش"""
    try:
        # اضافه کردن به صف
        await file_queue.put((client, message))

        # محاسبه موقعیت در صف
        queue_position = file_queue.qsize()

        if is_processing:
            await message.reply(
                f"📥 فایل شما دریافت شد و در صف قرار گرفت.\n"
                f"📍 موقعیت در صف: {queue_position}\n"
                f"⏳ لطفاً صبر کنید تا نوبت پردازش فایل شما برسد..."
            )
        else:
            await message.reply("📥 فایل شما دریافت شد و به زودی پردازش می‌شود...")

    except Exception as e:
        print(f"[ERROR] خطا در افزودن به صف: {e}")
        await message.reply(f"❌ خطا در افزودن فایل به صف:\n`{str(e)}`")


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
        "• ویدیو مسیج (Video Note)\n\n"
        "📊 وضعیت صف:"
    )

    # نمایش وضعیت صف
    queue_size = file_queue.qsize()
    if queue_size > 0:
        welcome_text += f"\n🔴 {queue_size} فایل در صف پردازش"
    else:
        welcome_text += "\n🟢 صف خالی است"

    if is_processing:
        welcome_text += "\n⚙️ در حال پردازش یک فایل..."

    await message.reply(welcome_text)


@app.on_message(filters.command("queue"))
async def queue_status(client: Client, message: Message):
    """نمایش وضعیت صف"""
    queue_size = file_queue.qsize()

    status_text = "📊 وضعیت صف پردازش:\n\n"

    if is_processing:
        status_text += "⚙️ وضعیت: در حال پردازش یک فایل\n"
    else:
        status_text += "⏸️ وضعیت: آماده دریافت فایل\n"

    status_text += f"📥 تعداد فایل‌های در صف: {queue_size}\n"

    if queue_size == 0:
        status_text += "\n🟢 صف خالی است و می‌توانید فایل ارسال کنید."
    elif queue_size <= 5:
        status_text += "\n🟡 صف نسبتاً شلوغ است، ممکن است کمی طول بکشد."
    else:
        status_text += "\n🔴 صف شلوغ است، لطفاً صبور باشید."

    await message.reply(status_text)


@app.on_message(filters.command("cancel"))
async def cancel_tasks(client: Client, message: Message):
    """خالی کردن صف (فقط برای مدیر)"""
    # می‌توانید محدودیت دسترسی اضافه کنید
    while not file_queue.empty():
        try:
            file_queue.get_nowait()
            file_queue.task_done()
        except:
            break

    await message.reply("🗑️ تمام فایل‌های در صف پاک شدند.")


@app.on_message()
async def other_messages(client: Client, message: Message):
    await message.reply("⚠️ لطفاً یک فایل ارسال کنید تا پردازش کنم.")


async def main():
    """تابع اصلی برای اجرای ربات و پردازش صف"""
    if not os.path.exists(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH)
        print(f"📁 پوشه {DOWNLOAD_PATH} ساخته شد.")

    print("🤖 ربات در حال اجرا...")

    # شروع پردازش صف در پس‌زمینه
    queue_processor = asyncio.create_task(process_queue())

    try:
        # اجرای ربات
        await app.start()
        print("✅ ربات با موفقیت راه‌اندازی شد!")

        # منتظر ماندن تا ربات متوقف شود
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        print("\n🛑 در حال توقف ربات...")
    finally:
        # توقف پردازش صف
        queue_processor.cancel()
        # قرار دادن None در صف برای توقف graceful
        await file_queue.put(None)

        await app.stop()
        print("👋 ربات متوقف شد.")


if __name__ == "__main__":
    app.run()
  

import json
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import os

# إعدادات البوت
BOT_TOKEN = "8388967054:AAGtPxQFGGPRGJzdnGyBSzNrF6DDSZlsJeA"
CHANNEL_ID = "@qd3qd"  # غيّرها لمعرف قناتك
SERVICE_ID = 9183
API_KEY = "5be3e6f7ef37395377151dba9cdbd552"
DEFAULT_VIEWS = 250
COOLDOWN_HOURS = 2
ADMIN_ID = 5581457665

# تحميل المستخدمين
try:
    with open("users.json", "r") as f:
        users = json.load(f)
except:
    users = {}

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

# التحقق من الاشتراك
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    if user_id not in users:
        users[user_id] = {"last_time": None}
        save_users()
        msg = f"📢 😂مستخدم جديد:\nالاسم: {user.full_name}\nالايدي: {user.id}\n@{user.username if user.username else 'لا يوجد'}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    keyboard = [[InlineKeyboardButton("🔼 زيادة المشاهدات", callback_data="increase")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"أهلاً {user.full_name}! لازم تشترك بالقناة: {CHANNEL_ID} قبل أي زيادة.",
        reply_markup=reply_markup
    )

# الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    if not await is_subscribed(context.bot, user_id):
        await query.edit_message_text(f"⚠️ لازم تشترك أولاً بالقناة: {CHANNEL_ID}")
        return

    last_time = users.get(user_id, {}).get("last_time")
    if last_time:
        last_time_dt = datetime.fromisoformat(last_time)
        if datetime.now() < last_time_dt + timedelta(hours=COOLDOWN_HOURS):
            remaining = (last_time_dt + timedelta(hours=COOLDOWN_HOURS)) - datetime.now()
            await query.edit_message_text(
                f"⏳ تعيد الطلب بعد {remaining.seconds//3600} ساعة و {(remaining.seconds%3600)//60} دقيقة."
            )
            return

    await query.edit_message_text("✍️ أرسل رابط المنشور:")
    context.user_data['step'] = "link"

# استقبال الرابط
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    step = context.user_data.get('step')
    if step != "link":
        return
    link = update.message.text

    data = {
        "key": API_KEY,
        "action": "add",
        "service": SERVICE_ID,
        "link": link,
        "quantity": DEFAULT_VIEWS
    }
    try:
        r = requests.post("https://kd1s.com/api/v2", data=data)
        res = r.json()
        if "order" in res:
            await update.message.reply_text(f"✅ تم زيادة {DEFAULT_VIEWS} مشاهدة!\nرقم الطلب: {res['order']}")
            users[user_id]["last_time"] = datetime.now().isoformat()
            save_users()
        else:
            await update.message.reply_text(f"❌ فشل بالزيادة.\nالرد: {res}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

    context.user_data.pop('step', None)

# تشغيل البوت
app_bot = Application.builder().token(BOT_TOKEN).build()
app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(CallbackQueryHandler(button_handler))
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook لـ Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    URL = os.environ.get("RENDER_EXTERNAL_URL", "https://senbotnew.onrender.com")
    app_bot.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="webhook",
        webhook_url=f"{URL}/webhook"
    )

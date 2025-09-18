import json
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from fastapi import FastAPI
import threading
import uvicorn

# -------------------------
# الإعدادات
# -------------------------
BOT_TOKEN = "8388967054:AAG0zsdXGrsjTXDTZ37OcjdMGbJc7UWlRfM"
API_KEY = "5be3e6f7ef37395377151dba9cdbd552"
CHANNEL_ID = "@Qd3Qd"   # ضع معرف القناة هنا
SERVICE_ID = 9183
DEFAULT_VIEWS = 250
COOLDOWN_HOURS = 2
ADMIN_ID = 5581457665
API_URL = "https://kd1s.com/api/v2"

# -------------------------
# المستخدمين
# -------------------------
try:
    with open("users.json", "r") as f:
        users = json.load(f)
except:
    users = {}

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

# -------------------------
# التحقق من الاشتراك
# -------------------------
def is_subscribed(bot, user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member','administrator','creator']
    except:
        return False

# -------------------------
# /start
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    if user_id not in users:
        users[user_id] = {"last_time": None}
        save_users()

        # إشعار المالك
        msg = f"""تم دخول نفـرر جديد إلى بوتك 😎
-----------------------
• الاسم🩵: {user.full_name}
• معرف🦾: @{user.username if user.username else 'لا يوجد'}
• الايدي🆔: {user.id}
-----------------------
• عدد مشتركينك الأبطال: {len(users)}
"""
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    keyboard = [[InlineKeyboardButton("🔼 زيادة المشاهدات", callback_data="increase")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"أهلاً {user.full_name}! 👋\n حبيبي البوت مخصص لزيادة تفاعل قناتك: {CHANNEL_ID}",
        reply_markup=reply_markup
    )

# -------------------------
# التعامل مع الأزرار
# -------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    if not is_subscribed(context.bot, user_id):
        await query.edit_message_text(f"⚠️ اشترك حبيبي، وأرسل /start : {CHANNEL_ID}")
        return

    last_time = users.get(user_id, {}).get("last_time")
    if last_time:
        last_time_dt = datetime.fromisoformat(last_time)
        if datetime.now() < last_time_dt + timedelta(hours=COOLDOWN_HOURS):
            remaining = (last_time_dt + timedelta(hours=COOLDOWN_HOURS)) - datetime.now()
            await query.edit_message_text(
                f"🤯⏳ يمكنك إعادة الطلب بعد {remaining.seconds//3600} ساعة و {(remaining.seconds%3600)//60} دقيقة."
            )
            return

    await query.edit_message_text("😑✍️ أرسل رابط منشـورك:")
    context.user_data['step'] = "link"

# -------------------------
# استقبال رابط المنشور
# -------------------------
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
        r = requests.post(API_URL, data=data)
        res = r.json()
        if "order" in res:
            await update.message.reply_text(
                f"😂✅ تم زيادة {DEFAULT_VIEWS} مشاهدة للمنشور!\nرقم الطلب: {res['order']}"
            )
            users[user_id]["last_time"] = datetime.now().isoformat()
            save_users()
        else:
            await update.message.reply_text(f"❗️❌ فشل في زيادة المشاهدات.\nالرد: {res}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

    context.user_data.pop('step', None)

# -------------------------
# إعداد البوت
# -------------------------
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# -------------------------
# Web server صغير للـ UptimeRobot
# -------------------------
web_app = FastAPI()

@web_app.get("/")
def home():
    return {"status": "ok", "bot": "running"}

def run_web():
    uvicorn.run(web_app, host="0.0.0.0", port=10000, log_level="error")

threading.Thread(target=run_web, daemon=True).start()

# -------------------------
# تشغيل البوت
# -------------------------
app.run_polling()

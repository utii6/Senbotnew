import json
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from fastapi import FastAPI, Request
import uvicorn

# -------------------------
# الإعدادات
# -------------------------
BOT_TOKEN = "8388967054:AAGtPxQFGGPRGJzdnGyBSzNrF6DDSZlsJeA"
API_KEY = "5be3e6f7ef37395377151dba9cdbd552"
CHANNEL_ID = "@Qd3Qd"
SERVICE_ID = 9183
DEFAULT_VIEWS = 300
COOLDOWN_HOURS = 2
ADMIN_ID = 5581457665
API_URL = "https://kd1s.com/api/v2"
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"

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
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
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
        msg = f"""تم دخول نفـرر جديد إلى بوتك  😎
-----------------------
• الاسم🤯: {user.full_name}
• معرف🦾: @{user.username if user.username else 'لا يوجد'}
• الايدي🆔: {user.id}
-----------------------
• عدد مشتركينك الأبطال: {len(users)}
"""
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    keyboard = [[InlineKeyboardButton("🔼 زيادة المشاهدات", callback_data="increase")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"أهلاً {user.full_name}! 👋\n حبيبي البوت مختص لزيادة تفاعل قناتك ومجانا↗: {CHANNEL_ID}",
        reply_markup=reply_markup
    )

# -------------------------
# التعامل مع الأزرار
# -------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    if not await is_subscribed(context.bot, user_id):
        await query.edit_message_text(f"⚠️ اشتـرك حبيبي، وأرسل /start : {CHANNEL_ID}")
        return

    last_time = users.get(user_id, {}).get("last_time")
    if last_time:
        last_time_dt = datetime.fromisoformat(last_time)
        if datetime.now() < last_time_dt + timedelta(hours=COOLDOWN_HOURS):
            remaining = (last_time_dt + timedelta(hours=COOLDOWN_HOURS)) - datetime.now()
            await query.edit_message_text(
                f"😑⏳ يمكنك إعادة الطلب بعد {remaining.seconds//3600} ساعة و {(remaining.seconds%3600)//60} دقيقة."
            )
            return

    await query.edit_message_text("💎✍️ أرسل رابط منشـورك الجميل:")
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
                f"😂✅ تم زيادة {DEFAULT_VIEWS} مشاهدة للمنشور!\nرقم الطلب🆔: {res['order']}"
            )
            users[user_id]["last_time"] = datetime.now().isoformat()
            save_users()
        else:
            await update.message.reply_text(f"❌❗️ فشل في زيادة المشاهدات.\nالرد: {res}")
    except Exception as e:
        await update.message.reply_text(f"!❌ خطأ: {e}")

    context.user_data.pop('step', None)

# -------------------------
# إعداد البوت مع Webhook
# -------------------------
app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
app_bot.add_handler(CommandHandler("start", start))
app_bot.add_handler(CallbackQueryHandler(button_handler))
app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# -------------------------
# FastAPI للـ Webhook
# -------------------------
web_app = FastAPI()

@web_app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, app_bot.bot)
    await app_bot.update_queue.put(update)
    return {"status": "ok"}

@web_app.get("/")
def home():
    return {"status": "ok", "bot": "running"}

# -------------------------
# تشغيل Uvicorn
# -------------------------
if __name__ == "__main__":
    # قبل أي شيء، نسجل Webhook عند رفع البوت
    import asyncio
    import telegram
    bot = telegram.Bot(BOT_TOKEN)
    import os
    URL = os.environ.get("RENDER_EXTERNAL_URL")  # Render يعطي هذا الرابط
    if URL:
        webhook_url = f"{URL}{WEBHOOK_PATH}"
        asyncio.run(bot.set_webhook(webhook_url))

    uvicorn.run(web_app, host="0.0.0.0", port=10000)

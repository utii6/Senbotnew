from telegram.ext import Application, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes
import os

BOT_TOKEN = "8388967054:AAGtPxQFGGPRGJzdnGyBSzNrF6DDSZlsJeA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅😂 البوت يشتغل تمام!")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    url = os.environ.get("RENDER_EXTERNAL_URL", "https://senbotnew.onrender.com")

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="webhook",
        webhook_url=f"{url}/webhook"
    )

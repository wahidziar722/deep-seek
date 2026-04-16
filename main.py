import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from flask import Flask, request, jsonify

# ==================== تنظیمات ====================
# د Render چاپیریال متغیرونه
TELEGRAM_TOKEN = os.environ.get("8633473710:AAHpVLtBeMbz0x7twey5HM89Ns05wc4Uf1M")
DEEPSEEK_API_KEY = os.environ.get("sk-e96e824fdc9642c4aed97d823bf11fbd")

# Flask ایپ (د Render Health Check لپاره)
app = Flask(__name__)

# د DeepSeek کلاینټ
deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# لاګونه
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# د کاروونکو د خبرو تاریخ
user_sessions = {}

# ==================== د بوټ دندې ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
🌟 **سلام {user.first_name}!** 🌟

زه د **DeepSeek AI** پواسطه پرمخ وړل شوی هوښیار بوټ یم!

💡 **ما ته هر څه واستوئ**، زه به هوښیار ځواب درکړم.

⚡ **کمانډونه:**
/start - بوټ پیلول
/help - مرسته
/clear - د خبرو تاریخ پاکول
    """
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📖 **لارښود:**
• ما ته مستقیم خپل متن واستوئ
• /clear - د خبرو تاریخ پاکول

**بېلګې:**
• "د پښتو یو شعر وایه"
• "په پایتون کې د کیلکولیټر کوډ وليکه"
    """
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in user_sessions:
        del user_sessions[user_id]
        await update.message.reply_text("🧹 ستاسو د خبرو تاریخ پاک شو!")
    else:
        await update.message.reply_text("📭 کوم تاریخ نشته چې پاک شي.")

async def get_deepseek_response(user_id: str, prompt: str) -> str:
    if user_id not in user_sessions:
        user_sessions[user_id] = [
            {"role": "system", "content": "ته یو ګټور مرستیال یې چې په پښتو، دری او انګلیسي خبرې کوی."}
        ]
    
    user_sessions[user_id].append({"role": "user", "content": prompt})
    
    if len(user_sessions[user_id]) > 20:
        user_sessions[user_id] = user_sessions[user_id][:1] + user_sessions[user_id][-10:]
    
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=user_sessions[user_id],
            temperature=0.7,
            max_tokens=2000
        )
        reply = response.choices[0].message.content
        user_sessions[user_id].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        logger.error(f"DeepSeek تېروتنه: {e}")
        return "😔 بخښنه غواړم، یوه ستونزه رامنځته شوه. بیا هڅه وکړئ."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = str(update.effective_user.id)
    
    await update.message.chat.send_action(action="typing")
    reply = await get_deepseek_response(user_id, user_message)
    await update.message.reply_text(reply)

# ==================== د Telegram بوټ ترتیب ====================

def setup_telegram_bot():
    """د Telegram بوټ جوړول او تنظیمول"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return application

# ==================== Flask Webhook (د Render لپاره) ====================

telegram_app = setup_telegram_bot()

@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
async def webhook():
    """د Telegram څخه د تازه معلوماتو ترلاسه کول"""
    try:
        update_data = request.get_json()
        if update_data:
            update = Update.de_json(update_data, telegram_app.bot)
            await telegram_app.process_update(update)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Webhook تېروتنه: {e}")
        return jsonify({"status": "error"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """د Render Health Check لپاره"""
    return jsonify({"status": "healthy", "bot": "running"}), 200

@app.route("/", methods=["GET"])
def index():
    """د اصلي پاڼې لپاره"""
    return jsonify({"message": "DeepSeek Telegram Bot is running!", "status": "active"}), 200

# ==================== د Webhook ثبتول ====================

async def set_webhook():
    """په Telegram کې د Webhook آدرس ثبتول"""
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook/{TELEGRAM_TOKEN}"
    
    async with telegram_app:
        await telegram_app.bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        logger.info(f"Webhook په دې آدرس ثبت شو: {webhook_url}")

# ==================== اصلي دنده ====================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    
    # د Webhook ثبتول (یو ځل)
    asyncio.run(set_webhook())
    
    # Flask سرور پیل کړئ
    logger.info(f"بوټ په پورټ {port} روان دی...")
    app.run(host="0.0.0.0", port=port)

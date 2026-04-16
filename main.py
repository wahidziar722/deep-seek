import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# ==================== تنظیمات ====================
TELEGRAM_TOKEN = "8633473710:AAHpVLtBeMbz0x7twey5HM89Ns05wc4Uf1M"
DEEPSEEK_API_KEY = "sk-e96e824fdc9642c4aed97d823bf11fbd"

# د DeepSeek کلاینټ
deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# لاګونه
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# د کاروونکو د خبرو تاریخ ساتلو لپاره
user_sessions = {}

# ==================== د بوټ دندې ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ښکلی /start پیغام"""
    user = update.effective_user
    welcome_text = f"""
🌟 **سلام {user.first_name}!** 🌟

زه د **DeepSeek AI** پواسطه پرمخ وړل شوی هوښیار بوټ یم!

🔮 **زه څه کولی شم؟**
• هر ډول پوښتنو ته ځواب ووایم
• لیکنې، شعرونه، کیسې جوړې کړم
• د پروګرام کولو مرسته وکړم
• ژباړه او لنډیز جوړ کړم

💡 **یوازې خپل پیغام ماته واستوه!**

⚡️ فوري ځوابونه - ۲۴ ساعته
    """
    
    # ښکلي کیبورډ بټنونه
    keyboard = [
        [InlineKeyboardButton("📢 زما چینل", url="https://t.me/ProTech43")],
        [InlineKeyboardButton("👨‍💻 پر مخ پر مختګ", url="https://t.me/WahidModeX")],
        [InlineKeyboardButton("❓ مرسته", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def get_deepseek_response(user_id: str, prompt: str) -> str:
    """د DeepSeek څخه هوښیار ځواب ترلاسه کول"""
    
    # د کارونکي د خبرو تاریخ
    if user_id not in user_sessions:
        user_sessions[user_id] = [
            {"role": "system", "content": "ته یو ګټور، دوستانه او هوښیار مرستیال یې چې په پښتو، دری او انګلیسي ژبو پوهیږې. په ښه اخلاقو سره ځواب ورکوه."}
        ]
    
    # د کارونکي پیغام اضافه کول
    user_sessions[user_id].append({"role": "user", "content": prompt})
    
    # که تاریخ ډېر اوږد شو، لنډ یې کړو
    if len(user_sessions[user_id]) > 20:
        user_sessions[user_id] = user_sessions[user_id][:1] + user_sessions[user_id][-10:]
    
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=user_sessions[user_id],
            temperature=0.7,  # تخلیقي کچه
            max_tokens=2000
        )
        
        bot_reply = response.choices[0].message.content
        user_sessions[user_id].append({"role": "assistant", "content": bot_reply})
        
        return bot_reply
        
    except Exception as e:
        logger.error(f"DeepSeek تېروتنه: {e}")
        return "😔 بخښنه غواړم، یوه تخنیکي ستونزه رامنځته شوه. مهرباني وکړه بیا هڅه وکړه!"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د کارونکي د پیغام پروسس"""
    user_message = update.message.text
    user_id = str(update.effective_user.id)
    
    # ټایپ کولو انیمیشن
    await update.message.chat.send_action(action="typing")
    
    # ځواب ترلاسه کول
    reply = await get_deepseek_response(user_id, user_message)
    
    # ښکلی ځواب لیږل (اوږد ځوابونه پرې کول)
    if len(reply) > 4000:
        for i in range(0, len(reply), 4000):
            await update.message.reply_text(reply[i:i+4000])
    else:
        await update.message.reply_text(reply)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د خبرو تاریخ پاکول"""
    user_id = str(update.effective_user.id)
    if user_id in user_sessions:
        del user_sessions[user_id]
    await update.message.reply_text("🧹 ستاسو د خبرو تاریخ پاک شو! اوس نوی خبرې پیل کړئ.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د مرستې کمانډ"""
    help_text = """
🤖 **د بوټ لارښود**

📝 **بنسټیز کمانډونه:**
• /start - بوټ پیلول
• /help - دا لارښود
• /clear - د خبرو تاریخ پاکول

💬 **څنګه وکاروم؟**
یوازې ماته هر ډول پوښتنه یا متن واستوه!

🎯 **بېلګې:**
• "د پښتو په اړه یو شعر وایه"
• "په پایتون کې د فیبوناچي سری څنګه جوړوم؟"
• "د افغانستان تاریخ لنډ کړه"

⚡ **ځانګړتیاوې:**
• د خبرو تاریخ یاد ساتي
• په پښتو، دري، انګليسي خبرې کوي
• ۲۴ ساعته فعال
    """
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د بټنونو مدیریت"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        help_text = """
📖 **مرسته:**
ما ته هر ډول پوښتنه واستوه!
زه ستاسو د خبرو تاریخ یاد ساتم.

کمانډونه:
/clear - تاریخ پاکول
/help - لارښود
        """
        await query.edit_message_text(help_text)

# ==================== اصلي دنده ====================

def main():
    """بوټ پیلول"""
    # بوټ جوړول
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # کمانډونه
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    
    # د پیغامونو مدیریت
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # د بټنونو مدیریت
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # پیلول
    print("🚀 بوټ روان دی...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# ==================== دلته خپل ټوکنونه دننه کړئ ====================
TELEGRAM_TOKEN = "8633473710:AAHpVLtBeMbz0x7twey5HM89Ns05wc4Uf1M"
DEEPSEEK_API_KEY = "sk-e96e824fdc9642c4aed97d823bf11fbd"
# ====================================================================

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

# د کاروونکو د خبرو تاریخ ساتلو لپاره
user_sessions = {}

# ==================== د بوټ دندې ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د /start کمانډ"""
    user = update.effective_user
    welcome_text = f"""
🌟 **سلام {user.first_name}!** 🌟

زه د **DeepSeek AI** پواسطه پرمخ وړل شوی هوښیار بوټ یم!

💡 **ما ته هر څه واستوئ**، زه به هوښیار ځواب درکړم.

⚡ **کمانډونه:**
/start - بوټ پیلول
/help - مرسته
/clear - د خبرو تاریخ پاکول

📝 **زه کولی شم:**
• هرې پوښتنې ته ځواب ووایم
• لیکنې، شعرونه جوړ کړم
• د پروګرام کولو مرسته وکړم
• ژباړه وکړم
    """
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د /help کمانډ"""
    help_text = """
📖 **لارښود:**

• ما ته مستقیم خپل متن واستوئ
• زه به تاسو ته هوښیار ځواب درکړم

**کمانډونه:**
/start - بوټ پیلول
/help - دا لارښود
/clear - د خبرو تاریخ پاکول

**بېلګې:**
• "د پښتو یو شعر وایه"
• "په پایتون کې د کیلکولیټر کوډ وليکه"
• "د افغانستان تاریخ لنډ کړه"
    """
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د /clear کمانډ - د خبرو تاریخ پاکول"""
    user_id = str(update.effective_user.id)
    if user_id in user_sessions:
        del user_sessions[user_id]
        await update.message.reply_text("🧹 ستاسو د خبرو تاریخ په بریالیتوب سره پاک شو!")
    else:
        await update.message.reply_text("📭 ستاسو لپاره کوم تاریخ نشته چې پاک شي.")

async def get_deepseek_response(user_id: str, prompt: str) -> str:
    """د DeepSeek API څخه هوښیار ځواب ترلاسه کول"""
    
    # که نوی کاروونکی وي، د هغه لپاره نوی تاریخ پیل کړئ
    if user_id not in user_sessions:
        user_sessions[user_id] = [
            {"role": "system", "content": "ته یو ګټور، دوستانه او هوښیار مرستیال یې. ته په پښتو، دری او انګلیسي ژبو پوهیږې. تل په ښه اخلاقو سره ځواب ورکوه."}
        ]
    
    # د کارونکي پیغام تاریخ ته اضافه کړئ
    user_sessions[user_id].append({"role": "user", "content": prompt})
    
    # که تاریخ ډېر اوږد شو (۲۰ پیغامونو څخه زیات)، نو لنډ یې کړئ
    if len(user_sessions[user_id]) > 20:
        user_sessions[user_id] = user_sessions[user_id][:1] + user_sessions[user_id][-10:]
    
    try:
        # د DeepSeek API ته غوښتنه
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=user_sessions[user_id],
            temperature=0.7,  # تخلیقي کچه (0 = کم، 1 = ډېر)
            max_tokens=2000
        )
        
        # د API څخه ځواب ترلاسه کړئ
        bot_reply = response.choices[0].message.content
        
        # د بوټ ځواب تاریخ ته اضافه کړئ
        user_sessions[user_id].append({"role": "assistant", "content": bot_reply})
        
        return bot_reply
        
    except Exception as e:
        logger.error(f"DeepSeek API تېروتنه: {e}")
        return "😔 بخښنه غواړم، یوه تخنیکي ستونزه رامنځته شوه. مهرباني وکړئ بیا هڅه وکړئ."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د کارونکي د متن پیغام پروسس کول"""
    user_message = update.message.text
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    
    # کارونکي ته خبر ورکړئ چې بوټ ځواب لیکي
    await update.message.chat.send_action(action="typing")
    
    # د DeepSeek څخه ځواب ترلاسه کړئ
    bot_reply = await get_deepseek_response(user_id, user_message)
    
    # ځواب کارونکي ته واستوئ
    await update.message.reply_text(bot_reply)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """د ناپېژندل شویو کمانډونو لپاره"""
    await update.message.reply_text("❓ بخښنه غواړم، زه دا کمانډ نه پوهیږم. د مرستې لپاره /help وکاروئ.")

# ==================== اصلي دنده ====================

def main():
    """بوټ پیل کړئ"""
    print("🚀 بوټ روان دی...")
    print("📡 د پیغامونو اوریدلو ته چمتو دی...")
    print("⏹️ د بندولو لپاره Ctrl+C فشار کړئ")
    
    # د بوټ غوښتنلیک جوړ کړئ
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # کمانډونه اضافه کړئ
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    
    # د متن پیغامونو لپاره (چې کمانډ نه وي)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # د ناپېژندل شویو کمانډونو لپاره
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # بوټ پیل کړئ (polling طریقه)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

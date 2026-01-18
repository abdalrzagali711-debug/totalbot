import os
import logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

# --- [ الإعدادات - ضع بياناتك هنا ] ---
# نصيحة: استخدم توكن جديد من @BotFather لحل مشكلة الـ Conflict نهائياً
TOKEN = "8413672647:AAG5uR0yQHgs8s6X9VxdWcWF_4ifKeiLxCk" 
MONGO_URL = "mongodb+srv://abdalrzagDB:10010207966##@cluster0.fighoyv.mongodb.net/?retryWrites=true&w=majority"
ADMIN_ID = 5524416062  # ضع الآيدي الخاص بك هنا

# --- [ نظام Flask للبقاء حياً على Render ] ---
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is Online and Connected to MongoDB!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- [ الاتصال بقاعدة بيانات MongoDB ] ---
# تم تفعيل خيارات الأمان لتجنب أخطاء SSL Handshake
client = MongoClient(MONGO_URL, tlsAllowInvalidCertificates=True)
db = client['EmpireBot_DB']
users_col = db['users']

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- [ وظائف البوت ] ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        # تسجيل المستخدم أو تحديث بياناته في MongoDB
        if not users_col.find_one({"user_id": user.id}):
            users_col.insert_one({
                "user_id": user.id, 
                "name": user.first_name, 
                "username": user.username
            })
        
        keyboard = [
            [InlineKeyboardButton("🎬 قسم التحميل", callback_data='dl'), 
             InlineKeyboardButton("🤖 ذكاء اصطناعي", callback_data='ai')],
            [InlineKeyboardButton("📊 إحصائياتي", callback_data='stats')]
        ]
        
        if user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("⚙️ لوحة المطور", callback_data='admin')])

        await update.message.reply_text(
            f"🚀 أهلاً بك يا {user.first_name}!\nتم ربط حسابك بقاعدة البيانات بنجاح وبدون أخطاء.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logging.error(f"خطأ في قاعدة البيانات: {e}")
        await update.message.reply_text("⚠️ عذراً، هناك مشكلة فنية في الاتصال بالسيرفر حالياً.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'admin':
        total = users_col.count_documents({})
        await query.edit_message_text(f"⚙️ لوحة التحكم\n\n👥 عدد المشتركين في القاعدة: {total}")

# --- [ تشغيل البوت ] ---
def main():
    # 1. تشغيل Flask في الخلفية لإرضاء Render ومنع الـ Port Timeout
    Thread(target=run_flask).start()
    
    # 2. بناء التطبيق
    application = Application.builder().token(TOKEN).build()
    
    # 3. إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    print("🚀 البوت انطلق وجاهز للرد...")
    
    # ميزة drop_pending_updates تحذف الرسائل القديمة التي كانت تسبب تعليق البوت (Conflict)
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()

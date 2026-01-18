import os
import logging
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

# --- إعداداتك الخاصة (قم بتغييرها) ---
TOKEN = "8413672647:AAG5uR0yQHgs8s6X9VxdWcWF_4ifKeiLxCk" 
MONGO_URL = "mongodb+srv://abdalrzagDB:10010207966##@cluster0.fighoyv.mongodb.net/?retryWrites=true&w=majority"
ADMIN_ID = 5524416062 # ضع الآيدي الخاص بك هنا (تحصل عليه من بوت @userinfobot)

# --- إعداد Flask لإبقاء البوت حياً على Render ---
server = Flask('')

@server.route('/')
def home():
    return "✅ البوت يعمل بنجاح 24/7!"

def run_flask():
    # Render يطلب الاستماع لمنفذ معين (بشكل افتراضي 10000)
    port = int(os.environ.get("PORT", 10000))
    server.run(host='0.0.0.0', port=port)

# --- الاتصال بقاعدة بيانات MongoDB ---
client = MongoClient(MONGO_URL)
db = client['EmpireBot_DB']
users_col = db['users']

# إعداد السجلات البرمجية (Logs)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- وظائف البوت ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # تسجيل المستخدم في قاعدة البيانات للأبد
    if not users_col.find_one({"user_id": user.id}):
        users_col.insert_one({
            "user_id": user.id, 
            "name": user.first_name, 
            "username": user.username,
            "status": "active"
        })
    
    keyboard = [
        [InlineKeyboardButton("🎬 تحميل فيديو", callback_data='dl'), 
         InlineKeyboardButton("🤖 ذكاء اصطناعي", callback_data='ai')],
        [InlineKeyboardButton("📊 إحصائياتي", callback_data='my_stats')]
    ]
    
    # يظهر فقط لك كمطور
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة التحكم الكاملة", callback_data='admin_panel')])

    await update.message.reply_text(
        f"🚀 مرحباً بك {user.first_name} في بوت الإمبراطورية!\nلقد تم ربط حسابك بقاعدة بيانات MongoDB بنجاح.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == 'admin_panel':
        total = users_col.count_documents({})
        text = f"⚙️ لوحة تحكم المطور\n\n👥 عدد المشتركين: {total}\n🛡 حالة السيرفر: مستقر"
        keyboard = [[InlineKeyboardButton("📢 إذاعة (Broadcast)", callback_data='broadcast')],
                    [InlineKeyboardButton("🔙 عودة", callback_data='back_home')]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == 'dl':
        await query.edit_message_text("📥 أرسل الآن رابط الفيديو (YouTube, TikTok, Instagram) وسأقوم بتحميله لك.")

# --- تشغيل البوت بنظام Polling نظيف ---
def main():
    # 1. تشغيل Flask في الخلفية
    Thread(target=run_flask).start()
    
    # 2. بناء تطبيق التلجرام
    application = Application.builder().token(TOKEN).build()
    
    # 3. إضافة الأوامر (Handlers)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_buttons))
    
    # 4. تشغيل البوت وحل مشكلة الـ Conflict
    print("🔥 البوت الآن في وضع الاستعداد...")
    
    # إعداد polling مع حذف أي رسائل قديمة لمنع تعليق البوت
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
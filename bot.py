from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)

import requests
from bs4 import BeautifulSoup

TOKEN = "8696215470:AAFuMSgWY9WRCbiIcN-eEkh-wPcl_t3vzXE"

USERNAME, PASSWORD = range(2)

# ---------------- LOGIN FUNCTION ---------------- #
def login_wisenet(username, password):
    session = requests.Session()
    login_url = "https://wisenet.spjimr.org/login/index.php"

    # Step 1: Get login page
    response = session.get(login_url)
    soup = BeautifulSoup(response.text, "html.parser")

    token_tag = soup.find("input", {"name": "logintoken"})
    if not token_tag:
        return None

    token = token_tag["value"]

    # Step 2: Login
    payload = {
        "username": username,
        "password": password,
        "logintoken": token
    }

    login_response = session.post(login_url, data=payload)

    # Check success
    if "dashboard" in login_response.url:
        return session
    else:
        return None


# ---------------- START LOGIN FLOW ---------------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter your Wisenet Username:")
    return USERNAME


async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["username"] = update.message.text
    await update.message.reply_text("Enter your Password:")
    return PASSWORD


async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = context.user_data["username"]
    password = update.message.text

    await update.message.reply_text("Logging in... ⏳")

    session = login_wisenet(username, password)

    if session:
        context.user_data["session"] = session

        # Show menu
        keyboard = [
            [InlineKeyboardButton("📊 Grades", callback_data='grades')],
            [InlineKeyboardButton("📚 Pre-readings", callback_data='readings')],
            [InlineKeyboardButton("🔄 Refresh", callback_data='refresh')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Login successful ✅\nChoose an option 👇",
            reply_markup=reply_markup
        )

        return ConversationHandler.END
    else:
        await update.message.reply_text("Login failed ❌ Try again with /start")
        return ConversationHandler.END


# ---------------- BUTTON HANDLER ---------------- #
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "grades":
        await query.edit_message_text("📊 Fetching your grades... (next step)")

    elif query.data == "readings":
        await query.edit_message_text("📚 Fetching pre-readings... (next step)")

    elif query.data == "refresh":
        await query.edit_message_text("🔄 Refreshing data...")


# ---------------- MAIN APP ---------------- #
app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
        PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
    },
    fallbacks=[]
)

app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(button_handler))

app.run_polling()

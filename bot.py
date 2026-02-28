import imaplib
import email
import re
import random
from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# ================= CONFIG =================
BOT_TOKEN = "8517596492:AAEl0BHLz3CH44Ar3436BBb8g9cdw_ZOJoA"

CHANNEL_ID = "@TeamOFDark1"
CHANNEL_LINK = "https://t.me/TeamOFDark1"

VIDEO_FILE_ID = "BAACAgUAAxkBAAICommcz32xjKaBJ1VOdh6qDs3Le-M6AAJ0GwACmLToVHyU1IVg8Gt3OgQ"
# ==========================================


# -------- FORCE JOIN --------
async def is_user_joined(context, user_id):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# -------- OTP FETCH --------
def fetch_latest_otp(user_email, app_pass):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user_email, app_pass)
        mail.select("INBOX")

        status, messages = mail.search(None, "ALL")
        ids = messages[0].split()

        for mail_id in reversed(ids[-15:]):
            _, data = mail.fetch(mail_id, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])

            if "telegram" not in msg.get("From", "").lower():
                continue

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            otp = re.search(r"\b\d{5,6}\b", body)
            if otp:
                return f"🔐 *Latest Telegram OTP*\n\n`{otp.group()}`"

        return "❌ No OTP found yet."

    except Exception as e:
        return f"⚠️ Error: {e}"


# -------- KEYBOARD --------
def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📧 Add Gmail"), KeyboardButton("🔑 Set App Password")],
        [KeyboardButton("✨ Generate Email"), KeyboardButton("📩 Get OTP")],
        [KeyboardButton("📺 How To Use")]
    ], resize_keyboard=True)


# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if await is_user_joined(context, update.effective_user.id):
        await update.message.reply_text(
            "✨ *Welcome to Premium Mail Generator Bot*\n\n"
            "Generate unlimited email variations & receive OTP instantly.",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
    else:
        btn = [[InlineKeyboardButton("✅ Join Channel", url=CHANNEL_LINK)]]
        await update.message.reply_text(
            "Access restricted.\nPlease join our official channel first.",
            reply_markup=InlineKeyboardMarkup(btn)
        )


# -------- MAIL GENERATOR --------
def generate_mail(base, ud):

    name, domain = base.split("@")
    ud.setdefault("generated", set())

    while True:
        rn = "".join(
            c.upper() if random.choice([True, False]) else c.lower()
            for c in name
        )

        rd = "".join(
            c.upper() if random.choice([True, False]) else c.lower()
            for c in domain
        )

        mail = f"{rn}@{rd}"

        if mail not in ud["generated"]:
            ud["generated"].add(mail)
            return mail


# -------- MESSAGE HANDLER --------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    if not await is_user_joined(context, update.effective_user.id):
        btn=[[InlineKeyboardButton("Join Channel",url=CHANNEL_LINK)]]
        await update.message.reply_text(
            "Please join channel first.",
            reply_markup=InlineKeyboardMarkup(btn))
        return

    text = update.message.text
    ud = context.user_data

    if text == "📧 Add Gmail":
        ud["step"] = "mail"
        await update.message.reply_text("Please send your Gmail address.")

    elif text == "🔑 Set App Password":
        ud["step"] = "pass"
        await update.message.reply_text("Send your Gmail App Password.")

    elif ud.get("step") == "mail":
        ud["email"] = text.strip()
        ud["step"] = None
        await update.message.reply_text("✅ Gmail successfully saved.")

    elif ud.get("step") == "pass":
        ud["pass"] = text.replace(" ", "")
        ud["step"] = None
        await update.message.reply_text("✅ App password saved securely.")

    # EMAIL GENERATE
    elif text == "✨ Generate Email":

        if not ud.get("email"):
            await update.message.reply_text("Add Gmail first.")
            return

        mail = generate_mail(ud["email"], ud)

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Generate New Email",
                                  callback_data="new_mail")]
        ])

        await update.message.reply_text(
            f"📧 *Generated Email*\n\n`{mail}`",
            parse_mode="Markdown",
            reply_markup=kb
        )

    # OTP
    elif text == "📩 Get OTP":

        if not ud.get("email") or not ud.get("pass"):
            await update.message.reply_text("Setup Gmail & App Password first.")
            return

        msg = await update.message.reply_text("🔎 Checking mailbox...")

        otp = fetch_latest_otp(ud["email"], ud["pass"])

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh OTP",
                                  callback_data="refresh_otp")]
        ])

        await msg.edit_text(
            otp,
            parse_mode="Markdown",
            reply_markup=kb
        )

    elif text == "📺 How To Use":
        await update.message.reply_video(
            VIDEO_FILE_ID,
            caption="Follow this guide to setup the bot."
        )


# -------- BUTTON CALLBACK --------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    ud = context.user_data

    if query.data == "new_mail":

        mail = generate_mail(ud["email"], ud)

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Generate New Email",
                                  callback_data="new_mail")]
        ])

        await query.edit_message_text(
            f"📧 *Generated Email*\n\n`{mail}`",
            parse_mode="Markdown",
            reply_markup=kb
        )

    elif query.data == "refresh_otp":

        otp = fetch_latest_otp(ud["email"], ud["pass"])

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh OTP",
                                  callback_data="refresh_otp")]
        ])

        await query.edit_message_text(
            otp,
            parse_mode="Markdown",
            reply_markup=kb
        )


# -------- MAIN --------
def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.add_handler(CallbackQueryHandler(buttons))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

import os
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ======================
# ENV
# ======================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
AFFILIATE_ID = os.getenv("APP_ID")  # your af_siteid

# ======================
# EXTRACT LINKS
# ======================
def extract_links(text):
    return re.findall(r"https?://[^\s]+", text or "")

# ======================
# EXPAND SHORT LINKS
# ======================
def expand_link(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=10)
        return r.url
    except:
        return url

# ======================
# ADD AFFILIATE TAG
# ======================
def make_affiliate(url):
    if "af_siteid" in url:
        return url

    connector = "&" if "?" in url else "?"
    return f"{url}{connector}af_siteid={AFFILIATE_ID}"

# ======================
# PROCESS
# ======================
def process(text):
    links = extract_links(text)
    results = []

    for link in links[:5]:
        expanded = expand_link(link)
        affiliate = make_affiliate(expanded)
        results.append(affiliate)

    return results

# ======================
# HANDLERS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me Shopee links and I’ll convert them 🔗")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    links = extract_links(text)

    if not links:
        await update.message.reply_text("Please send a Shopee link.")
        return

    results = process(text)

    await update.message.reply_text("\n\n".join(results))

# ======================
# MAIN
# ======================
def main():
    print("TOKEN:", TELEGRAM_TOKEN)
    print("APP_ID:", AFFILIATE_ID)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()

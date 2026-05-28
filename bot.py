import os
import re
import requests
import time
import hmac
import hashlib
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# =====================
# ENV
# =====================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")

API_URL = "https://affiliate.shopee.sg/open_api/graphql"

# =====================
# EXTRACT LINKS
# =====================
def extract_links(text):
    return re.findall(r"https?://[^\s]+", text or "")

# =====================
# RESOLVE SHORT LINK
# =====================
def resolve(url):
    try:
        r = requests.get(url, allow_redirects=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        return r.url
    except:
        return url

# =====================
# SIGNATURE
# =====================
def sign(timestamp: int):
    base = f"{APP_ID}{timestamp}"
    return hmac.new(
        APP_SECRET.encode(),
        base.encode(),
        hashlib.sha256
    ).hexdigest()

# =====================
# SHOPEE SHORT LINK API
# =====================
def generate_short_link(url: str):
    try:
        ts = int(time.time())
        signature = sign(ts)

        query = f"""
        mutation {{
          generateShortLink(originUrl: "{url}") {{
            shortLink
          }}
        }}
        """

        headers = {
            "Content-Type": "application/json",
            "AppId": APP_ID,
            "Timestamp": str(ts),
            "Signature": signature
        }

        r = requests.post(API_URL, json={"query": query}, headers=headers, timeout=10)
        print("STATUS:", r.status_code)
        print("RAW RESPONSE:", r.text)
        
        data = r.json()

        return data["data"]["generateShortLink"]["shortLink"]

    except Exception as e:
        print("API ERROR:", e)
        return None

# =====================
# TELEGRAM HANDLER
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send Shopee links (up to 5).")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    links = extract_links(update.message.text)

    if not links:
        await update.message.reply_text("⚠️ Please send Shopee links only.")
        return

    results = []

    for link in links[:5]:
        resolved = resolve(link)

        short = generate_short_link(resolved)

        if short:
            results.append(short)
        else:
            results.append(f"❌ Failed: {link}")

    await update.message.reply_text("\n\n".join(results))

# =====================
# MAIN
# =====================
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()

import os
import re
import time
import hmac
import hashlib
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ======================
# ENV VARIABLES (RAILWAY)
# ======================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")

GRAPHQL_ENDPOINT = "https://affiliate.shopee.sg/open_api/graphql"


# ======================
# VALIDATION
# ======================
def extract_links(text: str):
    return re.findall(r"https?://[^\s]+", text or "")


# ======================
# EXPAND SHORT LINKS (sg.shp.ee / s.shopee.sg)
# ======================
def expand_link(url: str):
    try:
        r = requests.get(url, allow_redirects=True, timeout=10)
        return r.url
    except:
        return url


# ======================
# SIGNATURE (SHOPEE API)
# ======================
def generate_signature(app_id: str, app_secret: str, timestamp: int):
    base_string = f"{app_id}{timestamp}"
    return hmac.new(
        app_secret.encode(),
        base_string.encode(),
        hashlib.sha256,
    ).hexdigest()


# ======================
# SHOPEE AFFILIATE SHORT LINK API
# ======================
def generate_short_link(url: str):
    if not APP_ID or not APP_SECRET:
        raise ValueError("Missing APP_ID or APP_SECRET in environment variables")

    timestamp = int(time.time())
    sign = generate_signature(APP_ID, APP_SECRET, timestamp)

    payload = {
        "query": f"""
        mutation {{
            generateShortLink(originUrl: "{url}") {{
                shortLink
            }}
        }}
        """
    }

    headers = {
        "Content-Type": "application/json",
        "AppId": APP_ID,
        "Timestamp": str(timestamp),
        "Signature": sign,
    }

    r = requests.post(
        GRAPHQL_ENDPOINT,
        json=payload,
        headers=headers,
        timeout=10,
    )

    print("STATUS:", r.status_code)
    print("RAW RESPONSE:", r.text)

    data = r.json()

    return data["data"]["generateShortLink"]["shortLink"]


# ======================
# PROCESS LINKS
# ======================
def process_links(text: str):
    links = extract_links(text)
    results = []

    for link in links[:5]:
        expanded = expand_link(link)

        try:
            short_link = generate_short_link(expanded)
            results.append(short_link)
        except Exception as e:
            print("API ERROR:", e)
            results.append(f"❌ Failed: {link}")

    return results


# ======================
# TELEGRAM HANDLERS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send Shopee links (sg.shp.ee / s.shopee.sg / product links)\n"
        "I’ll convert them into affiliate short links 🔗"
    )


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    links = extract_links(text)

    if not links:
        await update.message.reply_text("⚠️ Please send Shopee links only.")
        return

    results = process_links(text)

    await update.message.reply_text("\n\n".join(results))


# ======================
# MAIN
# ======================
def main():
    print("Bot starting...")

    print("TOKEN:", bool(TELEGRAM_TOKEN))
    print("APP_ID:", bool(APP_ID))
    print("APP_SECRET:", bool(APP_SECRET))

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()

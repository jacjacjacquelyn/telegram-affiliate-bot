import os
import re
import time
import hmac
import hashlib
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# ======================
# ENV VARIABLES (RAILWAY)
# ======================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
APP_ID = os.getenv("SHOPEE_APP_ID")
APP_SECRET = os.getenv("SHOPEE_SECRET")

GRAPHQL_ENDPOINT = "https://affiliate.shopee.sg/open_api/graphql"

# ======================
# CLEAN LINK EXTRACTION
# ======================
def extract_links(text: str, limit=5):
    return re.findall(r"https?://[^\s]+", text)[:limit]

# ======================
# RESOLVE SHORT SHOPEE LINKS
# ======================
def resolve_shopee_url(url: str):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.url
    except Exception as e:
        print("RESOLVE ERROR:", e)
        return url

# ======================
# SIGNATURE (SHOPEE)
# ======================
def generate_sign(timestamp: int):
    base_string = f"{APP_ID}{timestamp}"
    return hmac.new(
        APP_SECRET.encode(),
        base_string.encode(),
        hashlib.sha256
    ).hexdigest()

    
# ======================
# SHOPEE AFFILIATE CALL
# ======================
def generate_affiliate_link(url: str):
    try:
        timestamp = int(time.time())
        sign = generate_sign(timestamp)

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
            "Timestamp": str(timestamp),
            "Signature": sign
        }

        response = requests.post(
            GRAPHQL_ENDPOINT,
            json={"query": query},
            headers=headers,
            timeout=10
        )

        data = response.json()

        # SAFE extraction
        result = data.get("data", {}).get("generateShortLink", {})
        short_link = result.get("shortLink")

        # fallback safety
        if short_link:
            return short_link

        return None

    except Exception as e:
        print("API ERROR:", e)
        return None

# ======================
# FORMAT FOR CREATORS (OPTIONAL UPGRADE)
# ======================
def format_for_creators(links):
    output = ["🛍️ Affiliate Picks:\n"]

    for i, link in enumerate(links, 1):
        output.append(f"{i}. 🔗 {link}")

    output.append("\n✨ Save & share this list")
    return "\n".join(output)

# ======================
# TELEGRAM HANDLERS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me up to 5 Shopee links and I’ll convert them into affiliate short links 🔗"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    links = extract_links(text)

    if not links:
        await update.message.reply_text("⚠️ No valid links found.")
        return

    results = []

    for link in links:
        real_url = resolve_shopee_url(link)
        affiliate = generate_affiliate_link(real_url)

        if affiliate:
           results.append(affiliate)

    if not results:
        await update.message.reply_text("⚠️ Could not generate affiliate links.")
        return

    # ======================
    # CREATOR MODE OUTPUT
    # ======================
    message = format_for_creators(results)

    await update.message.reply_text(message)

# ======================
# MAIN APP
# ======================
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()

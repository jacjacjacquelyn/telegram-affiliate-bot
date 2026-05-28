import os
import re
import time
import json
import hashlib
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ======================
# ENV
# ======================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")

GRAPHQL_URL = "https://open-api.affiliate.shopee.sg/graphql"


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
# SIGNATURE (SHOPEE SPEC)
# SHA256(AppId + Timestamp + Payload + Secret)
# ======================
def generate_signature(app_id, timestamp, payload_str, secret):
    raw = app_id + timestamp + payload_str + secret
    return hashlib.sha256(raw.encode()).hexdigest()


# ======================
# SHOPEE API CALL
# ======================
def generate_short_link(url: str):
    if not APP_ID or not APP_SECRET:
        print("Missing APP_ID or APP_SECRET")
        return None

    timestamp = str(int(time.time()))

    # IMPORTANT: must be single-line query for stable hashing
    QUERY = "mutation generateShortLink($input:ShortLinkInput!){generateShortLink(input:$input){shortLink}}"

    payload = {
        "query": QUERY,
        "operationName": "generateShortLink",
        "variables": {
            "input": {
                "originUrl": url
            }
        }
    }

    # EXACT string used for signature
    payload_str = json.dumps(payload, separators=(',', ':'))

    signature = generate_signature(APP_ID, timestamp, payload_str, APP_SECRET)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID}, Timestamp={timestamp}, Signature={signature}"
    }

    r = requests.post(
        GRAPHQL_URL,
        data=payload_str,
        headers=headers,
        timeout=10
    )

    print("STATUS:", r.status_code)
    print("RAW RESPONSE:", r.text)

    try:
        data = r.json()

        if "errors" in data:
            print("SHOPEE ERROR:", data["errors"])
            return None

        return data["data"]["generateShortLink"]["shortLink"]

    except Exception as e:
        print("PARSE ERROR:", e)
        return None


# ======================
# PROCESS LINKS
# ======================
def process(text):
    links = extract_links(text)
    results = []

    for link in links[:5]:
        expanded = expand_link(link)
        affiliate = generate_short_link(expanded)

        if affiliate:
            results.append(affiliate)

    return results


# ======================
# HANDLERS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋🏼 send me your shopee link(s) and I’ll convert them for you 🌼 convert up to 5 links at a go.")


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    links = extract_links(text)

    if not links:
        await update.message.reply_text("‼️I only recognise a shopee link. Paste your shopee link below and hit send. I'll reply you with the converted link which you can then add to cart. If there's a follower voucher, the voucher will automatically be applied in your cart. ")
        return

    results = process(text)

    # remove None values
    results = [r for r in results if r]

    if not results:
        await update.message.reply_text("Sorry, the system bumped into some error. Please check that it's a valid shopee link! Alternatively, you can also DM the links to me via my IG or telegram @jacquelynedna.")
        return

    await update.message.reply_text("\n\n".join(results))


# ======================
# MAIN
# ======================
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("Bot running...")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

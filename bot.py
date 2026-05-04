import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = "8542549078:AAH52vzek5w5wqIxppbwhIqEY4FSinnttR8"
AFFILIATE_ID = "14392540000"

def resolve_url(url):
    """
    Expands Shopee short links (s.shopee.sg / shp.ee)
    """
    try:
        session = requests.Session()
        response = session.get(
            url,
            allow_redirects=True,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        return response.url
    except Exception as e:
        print("Resolve error:", e)
        return None


# =========================
# EXTRACT PRODUCT IDS
# =========================
def extract_ids(url):
    """
    Supports multiple Shopee formats:
    1. i.shop.item
    2. /product/shop/item
    """

    print("Extracting from:", url)

    # Format 1: i.shop.item
    match = re.search(r"i\.(\d+)\.(\d+)", url)
    if match:
        return match.group(1), match.group(2)

    # Format 2: /product/shop/item
    match = re.search(r"product/(\d+)/(\d+)", url)
    if match:
        return match.group(1), match.group(2)

    # Fallback (sometimes Shopee hides structure)
    match = re.search(r"(\d{8,})", url)
    if match:
        return match.group(1), "0"

    return None, None


# =========================
# BUILD AFFILIATE LINK
# =========================
def build_affiliate_link(shop_id, item_id):
    return f"https://shopee.sg/product/{shop_id}/{item_id}?af_siteid={AFFILIATE_ID}"


# =========================
# BOT COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me a Shopee product link and I’ll convert it into an affiliate link 🔗"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    print("RAW INPUT:", text)

    # Step 1: handle short links
    if "s.shopee.sg" in text or "shp.ee" in text:
        resolved = resolve_url(text)
        print("RESOLVED URL:", resolved)

        if resolved:
            text = resolved
        else:
            await update.message.reply_text("⚠️ Could not resolve Shopee link.")
            return

    # Step 2: extract IDs
    shop_id, item_id = extract_ids(text)

    if not shop_id or not item_id:
        await update.message.reply_text(
            "⚠️ I couldn’t extract a valid Shopee product.\n"
            "Try sending a full Shopee product link instead."
        )
        return

    # Step 3: build affiliate link
    affiliate_link = build_affiliate_link(shop_id, item_id)

    await update.message.reply_text(f"🔗 Your affiliate link:\n{affiliate_link}")


# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()

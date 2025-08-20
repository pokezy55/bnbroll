import asyncio
import threading
import time
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8233163082:AAGFxCdgCzjPbgvXyNXNKCdfIqpwoibEwGE"
AUTH_FILE = "auth.txt"

app = Flask(__name__)

# ====== bagian SPIN LOOP ======
def spin_loop():
    while True:
        try:
            with open(AUTH_FILE) as f:
                lines = f.read().splitlines()
            for line in lines:
                if "||" not in line:  # skip salah format
                    continue
                ts, auth = line.split("||", 1)
                headers = {
                    "accept": "*/*",
                    "content-type": "application/json",
                    "origin": "https://cryptoroll-blush.vercel.app",
                    "referer": "https://cryptoroll-blush.vercel.app/claim",
                    "user-agent": "Mozilla/5.0",
                    "x-trpc-source": "nextjs-react",
                    "x-telegram-init-data": auth
                }
                r = requests.post(
                    "https://cryptoroll-blush.vercel.app/trpc/game.claim.execute?batch=1",
                    headers=headers,
                    json={"0": {"json": {}}}
                )
                print(f"[{time.strftime('%H:%M:%S')}] {r.status_code} {r.text[:100]}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(3610)


# ====== TELEGRAM BOT HANDLERS ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kirimkan query_id=... untuk disimpan!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.startswith("query_id="):
        ts = int(time.time())
        with open(AUTH_FILE, "a", encoding="utf-8") as f:
            f.write(f"{ts}||{text}\n")

        # langsung spin sekali pake query yg baru
        headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "origin": "https://cryptoroll-blush.vercel.app",
            "referer": "https://cryptoroll-blush.vercel.app/claim",
            "user-agent": "Mozilla/5.0",
            "x-trpc-source": "nextjs-react",
            "x-telegram-init-data": text
        }
        try:
            r = requests.post(
                "https://cryptoroll-blush.vercel.app/trpc/game.claim.execute?batch=1",
                headers=headers,
                json={"0": {"json": {}}}
            )
            print(f"[{time.strftime('%H:%M:%S')}] {r.status_code} {r.text[:100]}")
            await update.message.reply_text(f"✅ Data ditambahkan & spin dikirim! ({r.status_code})")
        except Exception as e:
            await update.message.reply_text(f"❌ Data ditambahkan, tapi spin gagal: {e}")
    else:
        await update.message.reply_text("❌ Format salah, kirim `query_id=...`")

def run_bot():
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app_tg.run_polling()


# ====== FLASK ENDPOINT ======
@app.route("/")
def index():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))  # default 10000 kalau lokal
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # thread utk spin
    threading.Thread(target=spin_loop, daemon=True).start()
    # thread utk flask (hanya start sekali)
    threading.Thread(target=run_flask, daemon=True).start()
    # telegram bot di main thread
    run_bot()

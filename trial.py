#!/usr/bin/env python3
#
# To deploy on a server:
# 1. Install dependencies: pip install -r requirements.txt
# 2. Run: python3 trial_scraper.py
#    (or use nohup/screen/tmux for background execution)
#
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
import time
# Telegram bot config
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Telegram bot config
TELEGRAM_BOT_TOKEN = "1916838949:AAHBZsmZso0ZGQI0f3hnkwpme0m72bEWURU"
TELEGRAM_CHAT_ID = "1492786313"

BASE_URL = "https://hblinks.pro/archives/"
NUMBERS_TO_TRY = list(range(90000, 100000))  # Try all numbers from 90000 to 99999 inclusive

async def send_telegram_message(session, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        async with session.post(url, data=payload, timeout=10) as resp:
            await resp.text()
    except Exception as e:
        print(f"Failed to send message to Telegram: {e}")

# Poll for /start command and reply
async def telegram_command_listener():
    last_update_id = None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                params = {"timeout": 10, "offset": last_update_id + 1 if last_update_id else None}
                async with session.get(url, params=params, timeout=15) as resp:
                    data = await resp.json()
                    for result in data.get("result", []):
                        last_update_id = result["update_id"]
                        message = result.get("message", {})
                        text = message.get("text", "")
                        chat_id = message.get("chat", {}).get("id")
                        if text.strip() == "/start" and str(chat_id) == TELEGRAM_CHAT_ID:
                            await send_telegram_message(session, "👋 Welcome! The scraper is running.")
            except Exception as e:
                logging.error(f"Telegram listener error: {e}")
            await asyncio.sleep(2)

async def fetch_and_process(num, session):
    url = f"{BASE_URL}{num}"
    logging.info(f"Trying number: {num}")
    try:
        async with session.get(url, timeout=10) as response:
            if response.status != 200:
                logging.info(f"Number {num}: HTTP {response.status}, skipping.")
                return
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')
            not_found = soup.find('h1', class_='large-404')
            if not_found:
                logging.info(f"Number {num}: 404 page.")
                return
            title_tag = soup.find('h1', class_='entry-title')
            if not title_tag:
                logging.info(f"Number {num}: No title found.")
                return
            title = title_tag.get_text(strip=True)
            links = []
            for a in soup.select('div[style*="text-align: center;"] a[href]'):
                href = a.get('href')
                if href and href.startswith('http'):
                    links.append(href)
            if links:
                message = f"<b>Title:</b> {title}\n<b>Links:</b>\n" + "\n".join(links)
                print(message)
                await send_telegram_message(session, message)
                print("-" * 40)
                logging.info(f"Number {num}: Sent to Telegram.")
            else:
                logging.info(f"Number {num}: No links found.")
    except Exception as e:
        logging.error(f"Number {num}: Exception occurred: {e}")

async def main():
    logging.info(f"Starting scan from {NUMBERS_TO_TRY[0]} to {NUMBERS_TO_TRY[-1]}")
    # Start the Telegram listener in the background
    listener_task = asyncio.create_task(telegram_command_listener())
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_and_process(num, session) for num in NUMBERS_TO_TRY]
        await asyncio.gather(*tasks)
    logging.info("Scan complete.")
    listener_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())

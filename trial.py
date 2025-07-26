import asyncio
import aiohttp
from bs4 import BeautifulSoup

# Telegram bot config
TELEGRAM_BOT_TOKEN = "1916838949:AAHBZsmZso0ZGQI0f3hnkwpme0m72bEWURU"
TELEGRAM_CHAT_ID = "1492786313"

BASE_URL = "https://hblinks.pro/archives/"
NUMBERS_TO_TRY = list(range(9000, 10001))  # Try all numbers from 9000 to 10000 inclusive

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

async def fetch_and_process(num, session):
    url = f"{BASE_URL}{num}"
    try:
        async with session.get(url, timeout=10) as response:
            if response.status != 200:
                return
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')
            not_found = soup.find('h1', class_='large-404')
            if not_found:
                return
            title_tag = soup.find('h1', class_='entry-title')
            if not title_tag:
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
    except Exception as e:
        pass

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_and_process(num, session) for num in NUMBERS_TO_TRY]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

import re
import aiohttp

from config.settings import WEBSITE_URL, API_KEY


def parse_signal(message: str):
    try:
        direction = re.search(r"BIAS:\s*(BUY|SELL)", message)
        entry = re.search(r"LIMIT\s*@\s*([0-9.]+)", message)
        tp1 = re.search(r"TP1:</b>\s*([0-9.]+)|TP1:\s*([0-9.]+)", message)
        tp2 = re.search(r"TP2:</b>\s*([0-9.]+)|TP2:\s*([0-9.]+)", message)
        sl = re.search(r"SL:</b>\s*([0-9.]+)|SL:\s*([0-9.]+)", message)

        if not direction:
            return None

        return {
            "direction": direction.group(1),
            "entry_price": float(entry.group(1)),
            "sl_price": float(sl.group(1) or sl.group(2)),
            "tp1_price": float(tp1.group(1) or tp1.group(2)),
            "tp2_price": float(tp2.group(1) or tp2.group(2)),
        }

    except Exception as e:
        print("PARSE ERROR:", e)
        return None


async def send_signal_to_website(signal):

    data = parse_signal(signal)

    if not data:
        print("❌ Gagal membaca format signal Telegram")
        return False

    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:

        async with session.post(
            WEBSITE_URL,
            json=data,
            headers=headers
        ) as response:

            print("STATUS :", response.status)
            print("RESULT :", await response.text())

            return response.status == 201

import re
import aiohttp

from config.settings import WEBSITE_URL, API_KEY


# =====================================
# PARSE TELEGRAM SIGNAL
# =====================================

def parse_signal(message: str):

    try:

        direction = re.search(
            r"BIAS:\s*</?b?>?\s*(BUY|SELL)",
            message,
            re.IGNORECASE
        )

        entry = re.search(
            r"(BUY|SELL)\s+LIMIT\s*@\s*([0-9.]+)",
            message,
            re.IGNORECASE
        )

        tp1 = re.search(
            r"TP1.*?([0-9]+\.[0-9]+)",
            message,
            re.DOTALL
        )

        tp2 = re.search(
            r"TP2.*?([0-9]+\.[0-9]+)",
            message,
            re.DOTALL
        )

        sl = re.search(
            r"SL.*?([0-9]+\.[0-9]+)",
            message,
            re.DOTALL
        )

        if not all([direction, entry, tp1, tp2, sl]):

            print("❌ FORMAT SIGNAL TIDAK LENGKAP")

            return None

        return {

            "direction": direction.group(1).upper(),

            "entry_price": float(
                entry.group(2)
            ),

            "sl_price": float(
                sl.group(1)
            ),

            "tp1_price": float(
                tp1.group(1)
            ),

            "tp2_price": float(
                tp2.group(1)
            )

        }

    except Exception as e:

        print(
            "❌ PARSE ERROR:",
            e
        )

        return None


# =====================================
# SEND TO WEBSITE
# =====================================

async def send_signal_to_website(signal):

    data = parse_signal(signal)

    if not data:

        print(
            "❌ Gagal membaca signal Telegram"
        )

        return False

    headers = {

        "x-api-key": API_KEY,

        "Content-Type": "application/json"

    }

    timeout = aiohttp.ClientTimeout(
        total=20
    )

    try:

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            async with session.post(

                WEBSITE_URL,

                json=data,

                headers=headers

            ) as response:

                result = await response.text()

                print(
                    "🌐 WEBSITE STATUS :",
                    response.status
                )

                print(
                    "🌐 WEBSITE RESULT :",
                    result
                )

                return response.status == 201

    except Exception as e:

        print(
            "❌ WEBSITE ERROR:",
            e
        )

        return False

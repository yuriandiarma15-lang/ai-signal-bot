import re
import aiohttp

from datetime import datetime
from zoneinfo import ZoneInfo

from config.settings import WEBSITE_URL, API_KEY


# =====================================
# PARSE TELEGRAM SIGNAL
# =====================================

def parse_signal(message: str):

    try:

        # Bersihkan tag HTML Telegram
        clean = re.sub(r"<[^>]+>", "", message)

        # Rapikan whitespace
        clean = re.sub(r"\r", "", clean)
        clean = re.sub(r"\n+", "\n", clean)

        print("========== SIGNAL ==========")
        print(clean)
        print("============================")

        # ----------------------------
        # BIAS
        # ----------------------------
        direction = re.search(
            r"BIAS\s*:\s*(BUY|SELL)",
            clean,
            re.IGNORECASE
        )

        # ----------------------------
        # ENTRY
        # contoh:
        # BUY LIMIT @ 4046.29
        # SELL LIMIT @ 4058.12
        # ----------------------------
        entry = re.search(
            r"(BUY|SELL)\s+LIMIT\s*@\s*([0-9]+(?:\.[0-9]+)?)",
            clean,
            re.IGNORECASE
        )

        # ----------------------------
        # TP1
        # ----------------------------
        tp1 = re.search(
            r"TP1\s*:\s*([0-9]+(?:\.[0-9]+)?)",
            clean,
            re.IGNORECASE
        )

        # ----------------------------
        # TP2
        # ----------------------------
        tp2 = re.search(
            r"TP2\s*:\s*([0-9]+(?:\.[0-9]+)?)",
            clean,
            re.IGNORECASE
        )

        # ----------------------------
        # SL
        # ----------------------------
        sl = re.search(
            r"SL\s*:\s*([0-9]+(?:\.[0-9]+)?)",
            clean,
            re.IGNORECASE
        )

        if not direction:
            print("❌ BIAS tidak ditemukan")

        if not entry:
            print("❌ ENTRY tidak ditemukan")

        if not tp1:
            print("❌ TP1 tidak ditemukan")

        if not tp2:
            print("❌ TP2 tidak ditemukan")

        if not sl:
            print("❌ SL tidak ditemukan")

        if not all([direction, entry, tp1, tp2, sl]):

            print("❌ FORMAT SIGNAL TIDAK LENGKAP")

            return None

        data = {

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

        print("✅ PARSE BERHASIL")
        print(data)

        return data

    except Exception as e:

        print("❌ PARSE ERROR:", e)

        return None


# =====================================
# SEND TO WEBSITE
# =====================================

async def send_signal_to_website(signal):

    data = parse_signal(signal)

    if not data:

        print("❌ Gagal membaca signal Telegram")

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

                print("🌐 WEBSITE STATUS :", response.status)
                print("🌐 WEBSITE RESULT :", result)

                if response.status in (200, 201):
                    return True

                return False

    except Exception as e:

        print("❌ WEBSITE ERROR:", e)

        return False

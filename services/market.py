import os
import requests

from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


TWELVE_TOKEN = os.getenv("TWELVE_TOKEN")


BASE_URL = "https://api.twelvedata.com"


cached_price = None
cached_price_time = None


# =====================================
# GET REALTIME PRICE
# =====================================

def get_price():

    global cached_price
    global cached_price_time

    now = datetime.now()

    if (
        cached_price is not None
        and cached_price_time is not None
    ):

        if (
            now - cached_price_time
        ).total_seconds() < 3:

            return cached_price

    try:

        url = (
            f"{BASE_URL}/price"
            f"?symbol=XAU/USD"
            f"&apikey={TWELVE_TOKEN}"
        )

        r = requests.get(
            url,
            timeout=10
        )

        data = r.json()

        if "price" in data:

            price = float(
                data["price"]
            )

            cached_price = price
            cached_price_time = now

            return price

    except Exception as e:

        print(
            "PRICE ERROR:",
            e
        )

    return cached_price


# =====================================
# GET LAST CANDLES
# =====================================

def get_candles(
    interval="15min",
    outputsize=200
):

    try:

        url = (
            f"{BASE_URL}/time_series"
            f"?symbol=XAU/USD"
            f"&interval={interval}"
            f"&outputsize={outputsize}"
            f"&apikey={TWELVE_TOKEN}"
        )

        r = requests.get(
            url,
            timeout=15
        )

        data = r.json()

        if "values" not in data:
            return []

        candles = []

        for row in reversed(data["values"]):

            candles.append({

                "datetime": row["datetime"],

                "open": float(
                    row["open"]
                ),

                "high": float(
                    row["high"]
                ),

                "low": float(
                    row["low"]
                ),

                "close": float(
                    row["close"]
                ),

            })

        return candles

    except Exception as e:

        print(
            "CANDLE ERROR:",
            e
        )

        return []


# =====================================
# LAST CANDLE
# =====================================

def get_last_candle():

    candles = get_candles(
        outputsize=1
    )

    if not candles:
        return None

    return candles[-1]


# =====================================
# MARKET AVAILABLE
# =====================================

def market_available():

    return get_price() is not None

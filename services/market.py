import time
import logging

import requests

from datetime import datetime
from typing import Optional, List, Dict

from config.settings import (
    TWELVE_TOKEN,
    SMC_SYMBOL,
)


# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# TWELVE DATA
# =========================================================

BASE_URL = "https://api.twelvedata.com"

PRICE_URL = f"{BASE_URL}/price"

TIME_SERIES_URL = f"{BASE_URL}/time_series"


# =========================================================
# CACHE REALTIME PRICE
# =========================================================

cached_price: Optional[float] = None

cached_price_time: Optional[datetime] = None

PRICE_CACHE_SECONDS = 3


# =========================================================
# REQUEST SETTINGS
# =========================================================

REQUEST_TIMEOUT = 15

MAX_RETRIES = 3

RETRY_DELAY = 2


# =========================================================
# INTERNAL REQUEST
# =========================================================

def _request(
    url: str,
    params: dict,
    timeout: int = REQUEST_TIMEOUT,
):
    """
    Request ke Twelve Data dengan retry sederhana.
    """

    last_error = None

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            response = requests.get(
                url,
                params=params,
                timeout=timeout,
            )

            response.raise_for_status()

            data = response.json()

            # ---------------------------------------------
            # Twelve Data API ERROR
            # ---------------------------------------------

            if isinstance(data, dict):

                if data.get("status") == "error":

                    message = data.get(
                        "message",
                        "Unknown Twelve Data error",
                    )

                    raise RuntimeError(
                        message
                    )

                if data.get("code") not in (
                    None,
                    200,
                ):

                    raise RuntimeError(
                        data.get(
                            "message",
                            "Twelve Data API error",
                        )
                    )

            return data

        except Exception as exc:

            last_error = exc

            logger.warning(
                "Twelve Data request gagal "
                "(attempt %s/%s): %s",
                attempt,
                MAX_RETRIES,
                exc,
            )

            if attempt < MAX_RETRIES:

                time.sleep(
                    RETRY_DELAY
                )

    logger.error(
        "Twelve Data request gagal setelah %s percobaan: %s",
        MAX_RETRIES,
        last_error,
    )

    return None


# =========================================================
# GET REALTIME PRICE
# =========================================================

def get_price() -> Optional[float]:
    """
    Mengambil harga realtime XAUUSD dari Twelve Data.

    Menggunakan cache 3 detik agar tidak terlalu banyak
    request ke API.
    """

    global cached_price
    global cached_price_time

    now = datetime.now()

    # -----------------------------------------------------
    # CACHE
    # -----------------------------------------------------

    if (
        cached_price is not None
        and cached_price_time is not None
    ):

        age = (
            now - cached_price_time
        ).total_seconds()

        if age < PRICE_CACHE_SECONDS:

            return cached_price

    # -----------------------------------------------------
    # API
    # -----------------------------------------------------

    params = {

        "symbol": SMC_SYMBOL,

        "apikey": TWELVE_TOKEN,

    }

    data = _request(
        PRICE_URL,
        params,
        timeout=10,
    )

    if not data:

        return cached_price

    # -----------------------------------------------------
    # PRICE
    # -----------------------------------------------------

    price_value = data.get(
        "price"
    )

    if price_value is None:

        logger.error(
            "Twelve Data tidak mengembalikan price: %s",
            data,
        )

        return cached_price

    try:

        price = float(
            price_value
        )

    except (
        TypeError,
        ValueError,
    ):

        logger.error(
            "Harga Twelve Data tidak valid: %s",
            price_value,
        )

        return cached_price

    # -----------------------------------------------------
    # UPDATE CACHE
    # -----------------------------------------------------

    cached_price = price

    cached_price_time = now

    return price


# =========================================================
# GET CANDLES
# =========================================================

def get_candles(
    interval: str = "15min",
    outputsize: int = 200,
) -> List[Dict]:

    """
    Mengambil candle dari Twelve Data.

    Return:

        [
            {
                "datetime": "...",
                "open": ...,
                "high": ...,
                "low": ...,
                "close": ...
            }
        ]

    Urutan:

        LAMA -> BARU
    """

    if outputsize <= 0:

        return []

    params = {

        "symbol": SMC_SYMBOL,

        "interval": interval,

        "outputsize": outputsize,

        "apikey": TWELVE_TOKEN,

        "order": "ASC",

    }

    data = _request(
        TIME_SERIES_URL,
        params,
    )

    if not data:

        return []

    values = data.get(
        "values"
    )

    if not values:

        logger.warning(
            "Twelve Data tidak mengembalikan candle %s",
            interval,
        )

        return []

    candles = []

    for row in values:

        try:

            candles.append({

                "datetime":
                    row["datetime"],

                "open":
                    float(
                        row["open"]
                    ),

                "high":
                    float(
                        row["high"]
                    ),

                "low":
                    float(
                        row["low"]
                    ),

                "close":
                    float(
                        row["close"]
                    ),

            })

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:

            logger.warning(
                "Candle tidak valid: %s | error=%s",
                row,
                exc,
            )

    return candles


# =========================================================
# LAST CANDLE
# =========================================================

def get_last_candle(
    interval: str = "1min",
):
    """
    Mengambil candle terakhir.
    """

    candles = get_candles(
        interval=interval,
        outputsize=1,
    )

    if not candles:

        return None

    return candles[-1]


# =========================================================
# MARKET AVAILABLE
# =========================================================

def market_available() -> bool:
    """
    Mengecek apakah harga XAUUSD tersedia.
    """

    return (
        get_price()
        is not None
    )


# =========================================================
# CLEAR PRICE CACHE
# =========================================================

def clear_price_cache():
    """
    Menghapus cache harga secara manual.
    """

    global cached_price
    global cached_price_time

    cached_price = None

    cached_price_time = None

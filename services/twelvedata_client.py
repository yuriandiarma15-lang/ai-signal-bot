"""
Twelve Data Client
==================

Wrapper untuk endpoint Twelve Data time_series.

Digunakan oleh:
    services.signal_builder.py

Data:
    M1
    M5

Semua candle:
    LAMA -> BARU

Semua datetime:
    timezone-aware sesuai TIMEZONE.

Contoh:
    Candle.time
    candles[-1]
"""

import logging
import time
import requests

from dataclasses import dataclass
from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo

from config.settings import (
    TWELVEDATA_API_KEY,
    SYMBOL,
    TIMEZONE,
)


# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger(
    "twelvedata_client"
)


# =========================================================
# TWELVE DATA API
# =========================================================

BASE_URL = (
    "https://api.twelvedata.com/time_series"
)

USAGE_URL = (
    "https://api.twelvedata.com/api_usage"
)


# =========================================================
# RETRY
# =========================================================

MAX_RETRIES = 3

RETRY_BACKOFF_SECONDS = 20


# =========================================================
# TIMEZONE
# =========================================================

try:

    DATA_TIMEZONE = ZoneInfo(
        TIMEZONE
    )

except Exception as exc:

    logger.exception(
        "TIMEZONE tidak valid: %s",
        TIMEZONE,
    )

    raise exc


# =========================================================
# CANDLE
# =========================================================

@dataclass
class Candle:

    time: datetime

    open: float

    high: float

    low: float

    close: float

    # -----------------------------------------------------
    # BULLISH
    # -----------------------------------------------------

    @property
    def is_bullish(self) -> bool:

        return (
            self.close
            > self.open
        )

    # -----------------------------------------------------
    # BEARISH
    # -----------------------------------------------------

    @property
    def is_bearish(self) -> bool:

        return (
            self.close
            < self.open
        )

    # -----------------------------------------------------
    # BODY
    # -----------------------------------------------------

    @property
    def body(self) -> float:

        return abs(
            self.close
            - self.open
        )

    # -----------------------------------------------------
    # RANGE
    # -----------------------------------------------------

    @property
    def range(self) -> float:

        return (
            self.high
            - self.low
        )


# =========================================================
# ERROR
# =========================================================

class TwelveDataError(
    Exception
):
    pass


# =========================================================
# VALIDATE CONFIG
# =========================================================

def _validate_config():

    if not TWELVEDATA_API_KEY:

        raise TwelveDataError(
            "TWELVEDATA_API_KEY belum diisi "
            "di config/settings.py atau environment."
        )

    if not SYMBOL:

        raise TwelveDataError(
            "SYMBOL belum diisi "
            "di config/settings.py."
        )

    if not TIMEZONE:

        raise TwelveDataError(
            "TIMEZONE belum diisi "
            "di config/settings.py."
        )


# =========================================================
# DATETIME PARSER
# =========================================================

def _parse_candle_datetime(
    value: str,
) -> datetime:

    if not value:

        raise TwelveDataError(
            "Datetime candle kosong dari Twelve Data."
        )

    try:

        candle_time = (
            datetime.fromisoformat(
                value
            )
        )

    except ValueError as exc:

        raise TwelveDataError(
            "Format datetime candle "
            f"tidak valid: {value}"
        ) from exc

    # =====================================================
    # NAIVE DATETIME
    # =====================================================

    if candle_time.tzinfo is None:

        candle_time = (
            candle_time.replace(
                tzinfo=DATA_TIMEZONE
            )
        )

    # =====================================================
    # AWARE DATETIME
    # =====================================================

    else:

        candle_time = (
            candle_time.astimezone(
                DATA_TIMEZONE
            )
        )

    return candle_time


# =========================================================
# FETCH CANDLES
# =========================================================

def fetch_candles(
    interval: str,
    outputsize: int,
) -> List[Candle]:

    """
    Mengambil candle dari Twelve Data.

    Contoh:

        fetch_candles(
            interval="5min",
            outputsize=100
        )

    Return:

        List[Candle]

    Urutan:

        candle lama -> candle baru
    """

    _validate_config()

    if outputsize <= 0:

        raise ValueError(
            "outputsize harus lebih besar dari 0."
        )

    if not interval:

        raise ValueError(
            "interval tidak boleh kosong."
        )

    # =====================================================
    # PARAMETER
    # =====================================================

    params = {

        "symbol": SYMBOL,

        "interval": interval,

        "outputsize": outputsize,

        "apikey": TWELVEDATA_API_KEY,

        "timezone": TIMEZONE,

        "order": "ASC",

    }

    data = None

    # =====================================================
    # REQUEST
    # =====================================================

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            logger.debug(
                "Request Twelve Data: "
                "symbol=%s interval=%s "
                "outputsize=%s attempt=%s/%s",
                SYMBOL,
                interval,
                outputsize,
                attempt,
                MAX_RETRIES,
            )

            response = requests.get(

                BASE_URL,

                params=params,

                timeout=15,
            )

            # -------------------------------------------------
            # CREDIT
            # -------------------------------------------------

            credits_left = (
                response.headers.get(
                    "api-credits-left"
                )
            )

            if credits_left:

                logger.info(
                    "Twelve Data credit tersisa: %s",
                    credits_left,
                )

                try:

                    if int(
                        credits_left
                    ) < 50:

                        logger.warning(
                            "Credit Twelve Data "
                            "tinggal %s.",
                            credits_left,
                        )

                except ValueError:

                    pass

            # -------------------------------------------------
            # JSON
            # -------------------------------------------------

            try:

                data = response.json()

            except ValueError as exc:

                raise TwelveDataError(
                    "Response Twelve Data "
                    "bukan JSON valid."
                ) from exc

            # -------------------------------------------------
            # RATE LIMIT
            # -------------------------------------------------

            is_rate_limited = (

                response.status_code == 429

                or

                data.get("code") == 429

            )

            if is_rate_limited:

                logger.warning(
                    "Rate limit Twelve Data "
                    "(attempt %s/%s). "
                    "Menunggu %s detik.",
                    attempt,
                    MAX_RETRIES,
                    RETRY_BACKOFF_SECONDS,
                )

                if (
                    attempt
                    < MAX_RETRIES
                ):

                    time.sleep(
                        RETRY_BACKOFF_SECONDS
                    )

                    continue

            break

        except requests.RequestException as exc:

            logger.error(
                "Request Twelve Data gagal "
                "(attempt %s/%s): %s",
                attempt,
                MAX_RETRIES,
                exc,
            )

            if (
                attempt
                < MAX_RETRIES
            ):

                time.sleep(
                    RETRY_BACKOFF_SECONDS
                )

                continue

            raise TwelveDataError(
                "Gagal menghubungi Twelve Data "
                "setelah beberapa percobaan."
            ) from exc

    # =====================================================
    # VALIDASI RESPONSE
    # =====================================================

    if not data:

        raise TwelveDataError(
            "Tidak ada response dari Twelve Data."
        )

    # -----------------------------------------------------
    # ERROR API
    # -----------------------------------------------------

    if (
        data.get("status")
        == "error"
    ):

        message = data.get(
            "message",
            "Unknown error",
        )

        logger.error(
            "Twelve Data error: %s",
            message,
        )

        raise TwelveDataError(
            message
        )

    # -----------------------------------------------------
    # VALUES
    # -----------------------------------------------------

    values = data.get(
        "values"
    )

    if not values:

        message = data.get(
            "message",
            "Twelve Data tidak "
            "mengembalikan candle.",
        )

        raise TwelveDataError(
            message
        )

    # =====================================================
    # PARSE
    # =====================================================

    candles: List[Candle] = []

    for row in values:

        try:

            candle_time = (
                _parse_candle_datetime(
                    row["datetime"]
                )
            )

            candle = Candle(

                time=candle_time,

                open=float(
                    row["open"]
                ),

                high=float(
                    row["high"]
                ),

                low=float(
                    row["low"]
                ),

                close=float(
                    row["close"]
                ),

            )

            candles.append(
                candle
            )

        except KeyError as exc:

            logger.error(
                "Field candle tidak lengkap: %s",
                row,
            )

            raise TwelveDataError(
                f"Field candle tidak lengkap: {exc}"
            ) from exc

        except (
            TypeError,
            ValueError,
        ) as exc:

            logger.error(
                "Data candle tidak valid: %s",
                row,
            )

            raise TwelveDataError(
                f"Data candle tidak valid: {row}"
            ) from exc

    # =====================================================
    # VALIDASI
    # =====================================================

    if not candles:

        raise TwelveDataError(
            "Tidak ada candle valid."
        )

    # =====================================================
    # SORT
    # =====================================================

    candles.sort(
        key=lambda candle: candle.time
    )

    # =====================================================
    # LOG
    # =====================================================

    logger.info(
        "Twelve Data OK | "
        "symbol=%s | interval=%s | "
        "candles=%s | last=%s",
        SYMBOL,
        interval,
        len(candles),
        candles[-1].time,
    )

    return candles


# =========================================================
# GET CURRENT PRICE
# =========================================================

def get_current_price() -> float:

    """
    Mengambil harga terakhir menggunakan candle M1.
    """

    candles = fetch_candles(

        interval="1min",

        outputsize=1,

    )

    if not candles:

        raise TwelveDataError(
            "Tidak ada data harga terkini."
        )

    return candles[-1].close


# =========================================================
# CHECK QUOTA
# =========================================================

def check_remaining_quota() -> dict:

    """
    Cek quota Twelve Data.

    Jangan dipanggil setiap signal karena
    endpoint ini dapat menggunakan credit.
    """

    _validate_config()

    try:

        response = requests.get(

            USAGE_URL,

            params={
                "apikey":
                    TWELVEDATA_API_KEY
            },

            timeout=15,

        )

        response.raise_for_status()

        data = response.json()

        return data

    except requests.RequestException as exc:

        logger.exception(
            "Gagal mengecek quota Twelve Data."
        )

        raise TwelveDataError(
            "Gagal mengecek quota Twelve Data."
        ) from exc


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s "
            "[%(levelname)s] "
            "%(name)s: %(message)s"
        ),
    )

    try:

        candles = fetch_candles(
            interval="5min",
            outputsize=10,
        )

        print(
            "TOTAL CANDLE:",
            len(candles)
        )

        if candles:

            last = candles[-1]

            print(
                "LAST:",
                last.time,
                last.close
            )

            print(
                "BULLISH:",
                last.is_bullish
            )

            print(
                "BEARISH:",
                last.is_bearish
            )

    except Exception as exc:

        print(
            "ERROR:",
            exc
        )

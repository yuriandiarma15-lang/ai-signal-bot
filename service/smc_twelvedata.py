import logging
import time

from dataclasses import dataclass
from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo

import requests

from config.settings import (
    TWELVE_TOKEN,
    SMC_SYMBOL,
    TIMEZONE,
)


logger = logging.getLogger(__name__)


# =========================================================
# API
# =========================================================

BASE_URL = (
    "https://api.twelvedata.com/time_series"
)


USAGE_URL = (
    "https://api.twelvedata.com/api_usage"
)


MAX_RETRIES = 3

RETRY_BACKOFF_SECONDS = 20


# =========================================================
# TIMEZONE
# =========================================================

DATA_TIMEZONE = ZoneInfo(
    TIMEZONE
)


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

    @property
    def is_bullish(self):

        return (
            self.close >
            self.open
        )

    @property
    def is_bearish(self):

        return (
            self.close <
            self.open
        )

    @property
    def body(self):

        return abs(
            self.close -
            self.open
        )

    @property
    def range(self):

        return (
            self.high -
            self.low
        )


# =========================================================
# ERROR
# =========================================================

class TwelveDataError(
    Exception
):

    pass


# =========================================================
# DATETIME
# =========================================================

def _parse_candle_datetime(
    value: str
):

    if not value:

        raise TwelveDataError(
            "Datetime candle kosong."
        )

    try:

        candle_time = (
            datetime.fromisoformat(
                value
            )
        )

    except ValueError as exc:

        raise TwelveDataError(
            f"Format datetime tidak valid: "
            f"{value}"
        ) from exc


    if candle_time.tzinfo is None:

        candle_time = (
            candle_time.replace(
                tzinfo=DATA_TIMEZONE
            )
        )

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

    if not TWELVE_TOKEN:

        raise TwelveDataError(
            "TWELVE_TOKEN belum diisi."
        )


    if outputsize <= 0:

        raise ValueError(
            "outputsize harus lebih besar dari 0."
        )


    params = {

        "symbol":
            SMC_SYMBOL,

        "interval":
            interval,

        "outputsize":
            outputsize,

        "apikey":
            TWELVE_TOKEN,

        "timezone":
            TIMEZONE,

        "order":
            "ASC",
    }


    data = None


    # =====================================================
    # REQUEST
    # =====================================================

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            response = requests.get(

                BASE_URL,

                params=params,

                timeout=15,
            )


            data = response.json()


            if (
                response.status_code == 429
                or
                data.get("code") == 429
            ):

                logger.warning(
                    "Twelve Data rate limit "
                    "(%s/%s)",
                    attempt,
                    MAX_RETRIES,
                )


                if (
                    attempt <
                    MAX_RETRIES
                ):

                    time.sleep(
                        RETRY_BACKOFF_SECONDS
                    )

                    continue


            break


        except requests.RequestException:

            logger.exception(
                "Request Twelve Data gagal "
                "(%s/%s)",
                attempt,
                MAX_RETRIES,
            )


            if (
                attempt <
                MAX_RETRIES
            ):

                time.sleep(
                    RETRY_BACKOFF_SECONDS
                )

                continue


            raise TwelveDataError(
                "Gagal menghubungi Twelve Data."
            )


        except ValueError:

            raise TwelveDataError(
                "Response Twelve Data "
                "bukan JSON."
            )


    # =====================================================
    # VALIDATE
    # =====================================================

    if not data:

        raise TwelveDataError(
            "Tidak ada response Twelve Data."
        )


    if (
        data.get("status") == "error"
        or
        "values" not in data
    ):

        raise TwelveDataError(

            data.get(
                "message",
                "Unknown Twelve Data error"
            )
        )


    values = data.get(
        "values",
        []
    )


    if not values:

        raise TwelveDataError(
            "Tidak ada candle dari Twelve Data."
        )


    # =====================================================
    # PARSE
    # =====================================================

    candles = []


    for row in values:

        try:

            candle = Candle(

                time=
                    _parse_candle_datetime(
                        row["datetime"]
                    ),

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


        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:

            raise TwelveDataError(
                f"Data candle tidak valid: "
                f"{row}"
            ) from exc


    if not candles:

        raise TwelveDataError(
            "Tidak ada candle valid."
        )


    # =====================================================
    # SORT
    # =====================================================

    candles.sort(
        key=lambda c: c.time
    )


    logger.info(
        "SMC DATA: %s candle %s "
        "untuk %s",
        len(candles),
        interval,
        SMC_SYMBOL,
    )


    return candles


# =========================================================
# CURRENT PRICE
# =========================================================

def get_current_price():

    candles = fetch_candles(

        interval="1min",

        outputsize=1,
    )


    if not candles:

        raise TwelveDataError(
            "Harga terkini tidak tersedia."
        )


    return candles[-1].close

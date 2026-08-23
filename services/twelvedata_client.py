import logging
import time
import requests

from dataclasses import dataclass
from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo

from config import (
    TWELVE_TOKEN,
    SMC_SYMBOL,
    TIMEZONE,
)


logger = logging.getLogger(__name__)


BASE_URL = "https://api.twelvedata.com/time_series"

USAGE_URL = "https://api.twelvedata.com/api_usage"


MAX_RETRIES = 3

RETRY_BACKOFF_SECONDS = 20


try:
    DATA_TIMEZONE = ZoneInfo(TIMEZONE)

except Exception:

    logger.exception(
        "TIMEZONE tidak valid: %s",
        TIMEZONE,
    )

    raise


@dataclass
class Candle:

    time: datetime

    open: float

    high: float

    low: float

    close: float

    @property
    def is_bullish(self) -> bool:

        return self.close > self.open

    @property
    def is_bearish(self) -> bool:

        return self.close < self.open

    @property
    def body(self) -> float:

        return abs(
            self.close - self.open
        )

    @property
    def range(self) -> float:

        return self.high - self.low


class TwelveDataError(Exception):

    pass


def _parse_candle_datetime(
    value: str,
) -> datetime:

    if not value:

        raise TwelveDataError(
            "Datetime candle kosong dari Twelve Data."
        )

    try:

        candle_time = datetime.fromisoformat(
            value
        )

    except ValueError as exc:

        raise TwelveDataError(
            f"Format datetime candle tidak valid: {value}"
        ) from exc

    if candle_time.tzinfo is None:

        candle_time = candle_time.replace(
            tzinfo=DATA_TIMEZONE
        )

    else:

        candle_time = candle_time.astimezone(
            DATA_TIMEZONE
        )

    return candle_time


def fetch_candles(
    interval: str,
    outputsize: int,
) -> List[Candle]:

    if outputsize <= 0:

        raise ValueError(
            "outputsize harus lebih besar dari 0."
        )

    if not TWELVE_TOKEN:

        raise TwelveDataError(
            "TWELVE_TOKEN belum tersedia."
        )

    params = {

        "symbol": SMC_SYMBOL,

        "interval": interval,

        "outputsize": outputsize,

        "apikey": TWELVE_TOKEN,

        "timezone": TIMEZONE,

        "order": "ASC",
    }

    data = None

    for attempt in range(
        1,
        MAX_RETRIES + 1,
    ):

        try:

            response = requests.get(
                BASE_URL,
                params=params,
                timeout=15,
            )

            credits_left = response.headers.get(
                "api-credits-left"
            )

            if credits_left is not None:

                logger.info(
                    "Twelve Data credit tersisa: %s",
                    credits_left,
                )

            data = response.json()

            is_rate_limited = (
                response.status_code == 429
                or data.get("code") == 429
            )

            if is_rate_limited:

                logger.warning(
                    "Rate limit Twelve Data "
                    "(%s/%s)",
                    attempt,
                    MAX_RETRIES,
                )

                if attempt < MAX_RETRIES:

                    time.sleep(
                        RETRY_BACKOFF_SECONDS
                    )

                    continue

            break

        except requests.RequestException as exc:

            logger.exception(
                "Request Twelve Data gagal "
                "(%s/%s)",
                attempt,
                MAX_RETRIES,
            )

            if attempt < MAX_RETRIES:

                time.sleep(
                    RETRY_BACKOFF_SECONDS
                )

                continue

            raise TwelveDataError(
                "Gagal menghubungi Twelve Data."
            ) from exc

        except ValueError as exc:

            raise TwelveDataError(
                "Response Twelve Data tidak valid."
            ) from exc

    if not data:

        raise TwelveDataError(
            "Tidak ada response dari Twelve Data."
        )

    if (
        data.get("status") == "error"
        or "values" not in data
    ):

        msg = data.get(
            "message",
            "Unknown error dari Twelve Data",
        )

        logger.error(
            "Twelve Data error: %s",
            msg,
        )

        raise TwelveDataError(msg)

    values = data.get(
        "values",
        [],
    )

    if not values:

        raise TwelveDataError(
            "Twelve Data tidak mengembalikan candle."
        )

    candles = []

    for row in values:

        try:

            candle = Candle(

                time=_parse_candle_datetime(
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

            candles.append(candle)

        except KeyError as exc:

            raise TwelveDataError(
                f"Field candle tidak lengkap: {exc}"
            ) from exc

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise TwelveDataError(
                f"Data candle tidak valid: {row}"
            ) from exc

    if not candles:

        raise TwelveDataError(
            "Tidak ada candle valid setelah parsing."
        )

    candles.sort(
        key=lambda c: c.time
    )

    logger.debug(
        "Berhasil mengambil %s candle %s untuk %s",
        len(candles),
        interval,
        SMC_SYMBOL,
    )

    return candles


def check_remaining_quota() -> dict:

    if not TWELVE_TOKEN:

        raise TwelveDataError(
            "TWELVE_TOKEN belum tersedia."
        )

    try:

        response = requests.get(

            USAGE_URL,

            params={
                "apikey": TWELVE_TOKEN
            },

            timeout=15,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as exc:

        logger.exception(
            "Gagal mengecek quota Twelve Data."
        )

        raise TwelveDataError(
            "Gagal mengecek quota Twelve Data."
        ) from exc


def get_current_price() -> float:

    candles = fetch_candles(
        interval="1min",
        outputsize=1,
    )

    if not candles:

        raise TwelveDataError(
            "Tidak ada data harga terkini."
        )

    return candles[-1].close

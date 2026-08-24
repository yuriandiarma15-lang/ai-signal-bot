import re
import logging

import aiohttp

from datetime import datetime
from zoneinfo import ZoneInfo

from config.settings import (
    WEBSITE_URL,
    API_KEY,
    TIMEZONE,
)


# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger(
    "website"
)


# =========================================================
# TIMEZONE
# =========================================================

WIB = ZoneInfo(
    TIMEZONE
)


# =========================================================
# PARSE NUMBER
# =========================================================

def _parse_price(value):
    """
    Konversi nilai harga menjadi float.

    Bisa menerima:

        3345
        3345.50
        "3345"
        "3345.50"
        "`3345.50`"
        "ENTRY: 3345.50"
    """

    if value is None:
        return None

    try:

        if isinstance(
            value,
            (int, float)
        ):

            return float(value)

        text = str(value)

        text = (
            text
            .replace("`", "")
            .replace(",", "")
            .strip()
        )

        match = re.search(
            r"\d+(?:\.\d+)?",
            text
        )

        if not match:
            return None

        return float(
            match.group(0)
        )

    except Exception:

        logger.exception(
            "❌ ERROR PARSE PRICE | value=%r",
            value
        )

        return None


# =========================================================
# PARSE TELEGRAM SIGNAL
# =========================================================

def parse_signal(
    message: str
):
    """
    Parse signal berbentuk text Telegram.

    Mendukung:

        🟢 BUY XAUUSD
        🔴 SELL XAUUSD

        BIAS : BUY

        Entry (Buy Limit) : 3345

        BUY LIMIT @ 3345

        TP1 : 3400
        TP2 : 3450
        SL  : 3300
    """

    try:

        if not message:

            logger.error(
                "❌ MESSAGE SIGNAL KOSONG"
            )

            return None

        # =================================================
        # HTML CLEAN
        # =================================================

        clean = re.sub(
            r"<[^>]+>",
            "",
            str(message)
        )

        clean = (
            clean
            .replace("\r", "")
        )

        clean = re.sub(
            r"\n+",
            "\n",
            clean
        )

        logger.info(
            "========== SIGNAL PARSER =========="
        )

        logger.info(
            "\n%s",
            clean
        )

        logger.info(
            "===================================="
        )

        # =================================================
        # BIAS
        # =================================================

        direction = re.search(

            r"(?:BIAS\s*:\s*)?"
            r"\b(BUY|SELL)\b",

            clean,

            re.IGNORECASE
        )

        # =================================================
        # ENTRY
        # =================================================

        entry = re.search(

            r"(?:Entry\s*"
            r"(?:\([^)]*\))?"
            r"\s*[:=@]\s*"
            r"|"
            r"(?:BUY|SELL)"
            r"\s+(?:LIMIT|STOP)"
            r"\s*@\s*)"

            r"`?"
            r"([0-9]+(?:\.[0-9]+)?)"
            r"`?",

            clean,

            re.IGNORECASE
        )

        # =================================================
        # TP1
        # =================================================

        tp1 = re.search(

            r"TP1\s*"
            r"[:=@]\s*"
            r"`?"
            r"([0-9]+(?:\.[0-9]+)?)"
            r"`?",

            clean,

            re.IGNORECASE
        )

        # =================================================
        # TP2
        # =================================================

        tp2 = re.search(

            r"TP2\s*"
            r"[:=@]\s*"
            r"`?"
            r"([0-9]+(?:\.[0-9]+)?)"
            r"`?",

            clean,

            re.IGNORECASE
        )

        # =================================================
        # SL
        # =================================================

        sl = re.search(

            r"SL\s*"
            r"[:=@]\s*"
            r"`?"
            r"([0-9]+(?:\.[0-9]+)?)"
            r"`?",

            clean,

            re.IGNORECASE
        )

        # =================================================
        # CHECK
        # =================================================

        if not direction:

            logger.error(
                "❌ BIAS tidak ditemukan"
            )

        if not entry:

            logger.error(
                "❌ ENTRY tidak ditemukan"
            )

        if not tp1:

            logger.error(
                "❌ TP1 tidak ditemukan"
            )

        if not tp2:

            logger.error(
                "❌ TP2 tidak ditemukan"
            )

        if not sl:

            logger.error(
                "❌ SL tidak ditemukan"
            )

        if not all([
            direction,
            entry,
            tp1,
            tp2,
            sl
        ]):

            logger.error(
                "❌ FORMAT SIGNAL TIDAK LENGKAP"
            )

            return None

        # =================================================
        # DATA
        # =================================================

        data = {

            "direction":
                direction.group(1).upper(),

            "entry_price":
                _parse_price(
                    entry.group(1)
                ),

            "sl_price":
                _parse_price(
                    sl.group(1)
                ),

            "tp1_price":
                _parse_price(
                    tp1.group(1)
                ),

            "tp2_price":
                _parse_price(
                    tp2.group(1)
                ),

            "signal_time":
                datetime.now(
                    WIB
                ).isoformat(),

            "entry_type":
                "",

            "order_type":
                "",

            "is_pending":
                False,

            "probability":
                None,

            "zone_type":
                None,

            "fill_status":
                "untouched",

            "session":
                None,

        }

        # =================================================
        # VALIDATION
        # =================================================

        if not all([
            data["entry_price"] is not None,
            data["sl_price"] is not None,
            data["tp1_price"] is not None,
            data["tp2_price"] is not None,
        ]):

            logger.error(
                "❌ HARGA SIGNAL TIDAK VALID: %s",
                data
            )

            return None

        # =================================================
        # SUCCESS
        # =================================================

        logger.info(
            "✅ TELEGRAM SIGNAL BERHASIL DIPARSE: %s",
            data
        )

        return data

    except Exception:

        logger.exception(
            "❌ PARSE SIGNAL ERROR"
        )

        return None


# =========================================================
# CONVERT DICT SIGNAL
# =========================================================

def dict_to_website_data(
    signal
):
    """
    Mengubah dictionary dari pending_signal.json
    menjadi payload website.

    Penting:

    Setelah TradeSignal disimpan ke JSON,
    object tersebut akan menjadi dict.

    Jadi tidak boleh menggunakan getattr()
    seperti pada object TradeSignal.
    """

    try:

        if not isinstance(
            signal,
            dict
        ):

            logger.error(
                "❌ INPUT BUKAN DICT: %s",
                type(signal).__name__
            )

            return None

        logger.info(
            "📦 MEMPROSES DICT SIGNAL"
        )

        logger.debug(
            "DICT SIGNAL: %r",
            signal
        )

        # =================================================
        # BIAS
        # =================================================

        bias = signal.get(
            "bias"
        )

        # Kadang data JSON mungkin sudah menggunakan
        # direction, jadi kita support juga.

        if not bias:

            bias = signal.get(
                "direction"
            )

        if not bias:

            logger.error(
                "❌ DICT SIGNAL TIDAK MEMILIKI BIAS/DIRECTION"
            )

            return None

        bias = str(
            bias
        ).lower().strip()

        # =================================================
        # DIRECTION
        # =================================================

        if bias in (
            "bullish",
            "buy"
        ):

            direction = "BUY"

        elif bias in (
            "bearish",
            "sell"
        ):

            direction = "SELL"

        else:

            logger.error(
                "❌ BIAS TIDAK DIKENAL: %r",
                bias
            )

            return None

        # =================================================
        # ENTRY
        # =================================================

        entry_price = _parse_price(
            signal.get(
                "entry_price"
            )
        )

        # =================================================
        # SL
        # =================================================

        sl_price = _parse_price(
            signal.get(
                "sl"
            )
        )

        # Support kemungkinan nama sl_price

        if sl_price is None:

            sl_price = _parse_price(
                signal.get(
                    "sl_price"
                )
            )

        # =================================================
        # TP1
        # =================================================

        tp1_price = _parse_price(
            signal.get(
                "tp1"
            )
        )

        if tp1_price is None:

            tp1_price = _parse_price(
                signal.get(
                    "tp1_price"
                )
            )

        # =================================================
        # TP2
        # =================================================

        tp2_price = _parse_price(
            signal.get(
                "tp2"
            )
        )

        if tp2_price is None:

            tp2_price = _parse_price(
                signal.get(
                    "tp2_price"
                )
            )

        # =================================================
        # VALIDATE PRICE
        # =================================================

        if not all([
            entry_price is not None,
            sl_price is not None,
            tp1_price is not None,
            tp2_price is not None,
        ]):

            logger.error(
                "❌ HARGA SIGNAL TIDAK LENGKAP | "
                "entry=%r | "
                "sl=%r | "
                "tp1=%r | "
                "tp2=%r",

                entry_price,
                sl_price,
                tp1_price,
                tp2_price
            )

            logger.error(
                "❌ RAW DICT SIGNAL: %r",
                signal
            )

            return None

        # =================================================
        # SIGNAL TIME
        # =================================================

        signal_time = signal.get(
            "timestamp"
        )

        if signal_time is None:

            signal_time = signal.get(
                "signal_time"
            )

        # =================================================
        # DEFAULT TIME
        # =================================================

        if signal_time is None:

            signal_time = datetime.now(
                WIB
            )

        # =================================================
        # DATETIME OBJECT
        # =================================================

        if isinstance(
            signal_time,
            datetime
        ):

            if signal_time.tzinfo is None:

                signal_time = signal_time.replace(
                    tzinfo=WIB
                )

            else:

                signal_time = signal_time.astimezone(
                    WIB
                )

            signal_time = signal_time.isoformat()

        else:

            signal_time = str(
                signal_time
            )

        # =================================================
        # EXTRA DATA
        # =================================================

        entry_type = signal.get(
            "entry_type",
            ""
        )

        order_type = signal.get(
            "order_type",
            ""
        )

        probability = signal.get(
            "probability"
        )

        is_pending = signal.get(
            "is_pending",
            False
        )

        zone_type = signal.get(
            "zone_type"
        )

        fill_status = signal.get(
            "fill_status",
            "untouched"
        )

        session_name = signal.get(
            "session_name"
        )

        if session_name is None:

            session_name = signal.get(
                "session"
            )

        # =================================================
        # PAYLOAD
        # =================================================

        data = {

            "direction":
                direction,

            "entry_price":
                entry_price,

            "sl_price":
                sl_price,

            "tp1_price":
                tp1_price,

            "tp2_price":
                tp2_price,

            "signal_time":
                signal_time,

            # =============================================
            # EXTRA
            # =============================================

            "entry_type":
                entry_type,

            "order_type":
                order_type,

            "is_pending":
                bool(
                    is_pending
                ),

            "probability":
                probability,

            "zone_type":
                zone_type,

            "fill_status":
                fill_status,

            "session":
                session_name,

        }

        logger.info(
            "✅ DICT SIGNAL BERHASIL DIUBAH: %s",
            data
        )

        return data

    except Exception:

        logger.exception(
            "❌ DICT SIGNAL CONVERSION ERROR"
        )

        return None


# =========================================================
# CONVERT SIGNAL OBJECT
# =========================================================

def signal_object_to_data(
    signal
):
    """
    Mengubah TradeSignal / object hasil
    signal_builder menjadi payload website.
    """

    try:

        # =================================================
        # DIRECTION / BIAS
        # =================================================

        bias = getattr(
            signal,
            "bias",
            None
        )

        if not bias:

            logger.error(
                "❌ SIGNAL OBJECT TIDAK MEMILIKI BIAS"
            )

            return None

        bias = str(
            bias
        ).lower().strip()

        # =================================================
        # DIRECTION
        # =================================================

        if bias in (
            "bullish",
            "buy"
        ):

            direction = "BUY"

        elif bias in (
            "bearish",
            "sell"
        ):

            direction = "SELL"

        else:

            logger.error(
                "❌ BIAS TIDAK DIKENAL: %s",
                bias
            )

            return None

        # =================================================
        # PRICE
        # =================================================

        entry_price = _parse_price(
            getattr(
                signal,
                "entry_price",
                None
            )
        )

        sl_price = _parse_price(
            getattr(
                signal,
                "sl",
                None
            )
        )

        tp1_price = _parse_price(
            getattr(
                signal,
                "tp1",
                None
            )
        )

        tp2_price = _parse_price(
            getattr(
                signal,
                "tp2",
                None
            )
        )

        # =================================================
        # VALIDATE
        # =================================================

        if not all([
            entry_price is not None,
            sl_price is not None,
            tp1_price is not None,
            tp2_price is not None,
        ]):

            logger.error(
                "❌ HARGA SIGNAL TIDAK LENGKAP | "
                "entry=%r | "
                "sl=%r | "
                "tp1=%r | "
                "tp2=%r",

                entry_price,
                sl_price,
                tp1_price,
                tp2_price
            )

            logger.error(
                "❌ SIGNAL OBJECT: %r",
                signal
            )

            return None

        # =================================================
        # SIGNAL TIME
        # =================================================

        signal_time = getattr(
            signal,
            "timestamp",
            None
        )

        if signal_time is None:

            signal_time = datetime.now(
                WIB
            )

        elif signal_time.tzinfo is None:

            signal_time = signal_time.replace(
                tzinfo=WIB
            )

        else:

            signal_time = signal_time.astimezone(
                WIB
            )

        # =================================================
        # EXTRA
        # =================================================

        entry_type = getattr(
            signal,
            "entry_type",
            ""
        )

        order_type = getattr(
            signal,
            "order_type",
            ""
        )

        probability = getattr(
            signal,
            "probability",
            None
        )

        is_pending = getattr(
            signal,
            "is_pending",
            False
        )

        zone_type = getattr(
            signal,
            "zone_type",
            None
        )

        fill_status = getattr(
            signal,
            "fill_status",
            "untouched"
        )

        session_name = getattr(
            signal,
            "session_name",
            None
        )

        if session_name is None:

            session_name = getattr(
                signal,
                "session",
                None
            )

        # =================================================
        # PAYLOAD
        # =================================================

        data = {

            "direction":
                direction,

            "entry_price":
                entry_price,

            "sl_price":
                sl_price,

            "tp1_price":
                tp1_price,

            "tp2_price":
                tp2_price,

            "signal_time":
                signal_time.isoformat(),

            "entry_type":
                entry_type,

            "order_type":
                order_type,

            "is_pending":
                bool(
                    is_pending
                ),

            "probability":
                probability,

            "zone_type":
                zone_type,

            "fill_status":
                fill_status,

            "session":
                session_name,

        }

        logger.info(
            "✅ SIGNAL OBJECT CONVERTED: %s",
            data
        )

        return data

    except Exception:

        logger.exception(
            "❌ SIGNAL OBJECT CONVERSION ERROR"
        )

        return None


# =========================================================
# SEND TO WEBSITE
# =========================================================

async def send_signal_to_website(
    signal
):
    """
    Kirim signal ke website.

    Mendukung:

        1. TradeSignal object
        2. dict dari pending_signal.json
        3. string Telegram
    """

    # =====================================================
    # CHECK INPUT
    # =====================================================

    logger.info(
        "📡 WEBSITE INPUT TYPE: %s",
        type(signal).__name__
    )

    # =====================================================
    # DETERMINE INPUT TYPE
    # =====================================================

    if isinstance(
        signal,
        str
    ):

        logger.info(
            "📝 INPUT BERUPA TELEGRAM STRING"
        )

        data = parse_signal(
            signal
        )

    elif isinstance(
        signal,
        dict
    ):

        logger.info(
            "📦 INPUT BERUPA DICT / JSON"
        )

        data = dict_to_website_data(
            signal
        )

    else:

        logger.info(
            "🧠 INPUT BERUPA SIGNAL OBJECT"
        )

        data = signal_object_to_data(
            signal
        )

    # =====================================================
    # VALIDATION
    # =====================================================

    if not data:

        logger.error(
            "❌ GAGAL MEMBACA SIGNAL | "
            "TYPE=%s | "
            "VALUE=%r",

            type(signal).__name__,
            signal
        )

        return False

    # =====================================================
    # WEBSITE CONFIG
    # =====================================================

    if not WEBSITE_URL:

        logger.error(
            "❌ WEBSITE_URL KOSONG"
        )

        return False

    if not API_KEY:

        logger.error(
            "❌ API_KEY KOSONG"
        )

        return False

    # =====================================================
    # HEADERS
    # =====================================================

    headers = {

        "x-api-key":
            API_KEY,

        "Content-Type":
            "application/json",

    }

    # =====================================================
    # TIMEOUT
    # =====================================================

    timeout = aiohttp.ClientTimeout(
        total=20
    )

    # =====================================================
    # LOG PAYLOAD
    # =====================================================

    logger.info(
        "📤 PAYLOAD WEBSITE: %s",
        data
    )

    # =====================================================
    # REQUEST
    # =====================================================

    try:

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            async with session.post(

                WEBSITE_URL,

                json=data,

                headers=headers,

            ) as response:

                result = await response.text()

                logger.info(
                    "🌐 WEBSITE STATUS: %s",
                    response.status
                )

                logger.info(
                    "🌐 WEBSITE RESULT: %s",
                    result
                )

                # =========================================
                # SUCCESS
                # =========================================

                if response.status in (
                    200,
                    201
                ):

                    logger.info(
                        "✅ WEBSITE BERHASIL UPDATE"
                    )

                    return True

                # =========================================
                # FAILED
                # =========================================

                logger.error(
                    "❌ WEBSITE GAGAL UPDATE | HTTP %s",
                    response.status
                )

                return False

    # =====================================================
    # CONNECTION ERROR
    # =====================================================

    except asyncio.TimeoutError:

        logger.error(
            "❌ WEBSITE TIMEOUT"
        )

        return False

    except aiohttp.ClientError as e:

        logger.error(
            "❌ WEBSITE CONNECTION ERROR: %s",
            e
        )

        return False

    # =====================================================
    # UNKNOWN ERROR
    # =====================================================

    except Exception:

        logger.exception(
            "❌ WEBSITE ERROR"
        )

        return False

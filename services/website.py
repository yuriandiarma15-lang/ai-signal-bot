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

        return None


# =========================================================
# PARSE TELEGRAM SIGNAL
# =========================================================

def parse_signal(
    message: str
):
    """
    Parse signal berbentuk text Telegram.

    Mendukung format lama maupun format
    XAU AI SIGNAL terbaru.
    """

    try:

        if not message:
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
            "========== SIGNAL =========="
        )

        logger.info(
            "\n%s",
            clean
        )

        logger.info(
            "============================"
        )

        # =================================================
        # BIAS
        #
        # Format:
        # 🟢 BUY XAUUSD
        #
        # atau:
        # BIAS : BUY
        # =================================================

        direction = re.search(

            r"(?:BIAS\s*:\s*)?"
            r"\b(BUY|SELL)\b",

            clean,

            re.IGNORECASE
        )

        # =================================================
        # ENTRY
        #
        # Format baru:
        #
        # Entry (Buy Limit) : 3345
        #
        # Format lama:
        #
        # BUY LIMIT @ 3345
        # =================================================

        entry = re.search(

            r"(?:Entry\s*"
            r"(?:\([^)]*\))?"
            r"\s*[:=@]\s*"
            r"|"
            r"(?:BUY|SELL)"
            r"\s+(?:LIMIT|STOP)"
            r"\s*@\s*)"

            r"([0-9]+(?:\.[0-9]+)?)",

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
            r"([0-9]+(?:\.[0-9]+)?)",

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
            r"([0-9]+(?:\.[0-9]+)?)",

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
            r"([0-9]+(?:\.[0-9]+)?)",

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

        }

        # =================================================
        # VALIDATION
        # =================================================

        if not all([
            data["entry_price"],
            data["sl_price"],
            data["tp1_price"],
            data["tp2_price"],
        ]):

            logger.error(
                "❌ Harga signal tidak valid: %s",
                data
            )

            return None

        logger.info(
            "✅ PARSE BERHASIL: %s",
            data
        )

        return data

    except Exception:

        logger.exception(
            "❌ PARSE ERROR"
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

    Ini lebih aman daripada membuat Telegram
    message lalu diparse kembali.
    """

    try:

        # =================================================
        # DIRECTION
        # =================================================

        bias = getattr(
            signal,
            "bias",
            None
        )

        if not bias:

            return None

        bias = str(
            bias
        ).lower()

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
                "Bias tidak dikenal: %s",
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
                "Harga signal tidak lengkap."
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
        # EXTRA INFORMATION
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

            # =============================================
            # EXTRA DATA
            # =============================================

            "entry_type":
                entry_type,

            "order_type":
                order_type,

            "is_pending":
                bool(is_pending),

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

    Prioritas:
        1. Kalau object TradeSignal -> langsung ambil data
        2. Kalau string -> parse Telegram
    """

    # =====================================================
    # DETERMINE INPUT TYPE
    # =====================================================

    if isinstance(
        signal,
        str
    ):

        data = parse_signal(
            signal
        )

    else:

        data = signal_object_to_data(
            signal
        )

    # =====================================================
    # VALIDATION
    # =====================================================

    if not data:

        logger.error(
            "❌ Gagal membaca signal."
        )

        return False

    # =====================================================
    # WEBSITE CONFIG
    # =====================================================

    if not WEBSITE_URL:

        logger.error(
            "WEBSITE_URL kosong."
        )

        return False

    if not API_KEY:

        logger.error(
            "API_KEY kosong."
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
                    "❌ WEBSITE GAGAL UPDATE | "
                    "HTTP %s",
                    response.status
                )

                return False

    except aiohttp.ClientError as e:

        logger.error(
            "❌ WEBSITE CONNECTION ERROR: %s",
            e
        )

        return False

    except Exception:

        logger.exception(
            "❌ WEBSITE ERROR"
        )

        return False

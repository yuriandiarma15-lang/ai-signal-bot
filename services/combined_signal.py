"""
services/combined_signal.py

XAU AI SIGNAL BOT
COMBINED SIGNAL ADAPTER
=======================

Fungsi:
- Menerima TradeSignal dari signal_builder.py
- Mengambil fundamental news
- Menggabungkan SMC + Fundamental
- TIDAK mengubah logic SMC
- TIDAK mengubah Entry
- TIDAK mengubah SL
- TIDAK mengubah TP1
- TIDAK mengubah TP2
- TIDAK mengubah probability SMC
- Menambahkan data kombinasi sebagai attribute tambahan

ALUR:

signal_builder.py
        |
        | TradeSignal
        v
combined_signal.py
        |
        +--> fundamental_service.py
        |
        +--> combined_analysis.py
        |
        v
TradeSignal + combined data
        |
        v
sender.py
"""

import logging
from typing import Any, Dict, Optional, Tuple


from services.fundamental_service import (
    get_latest_fundamental_news,
)


from services.combined_analysis import (
    build_combined_analysis,
    format_combined_analysis,
)


logger = logging.getLogger(__name__)


# =========================================================
# CONFIG
# =========================================================

# Fundamental tidak boleh mengganti bias SMC.
SMC_REMAINS_PRIMARY = True


# =========================================================
# GENERIC ATTRIBUTE HELPER
# =========================================================

def _get_attr(
    obj: Any,
    name: str,
    default: Any = None,
) -> Any:
    """
    Membaca attribute secara aman.
    """

    if obj is None:
        return default

    try:

        value = getattr(
            obj,
            name,
            default,
        )

        if value is None:
            return default

        return value

    except Exception:

        return default


# =========================================================
# SET ATTRIBUTE SAFELY
# =========================================================

def _set_attr(
    obj: Any,
    name: str,
    value: Any,
) -> bool:
    """
    Menambahkan attribute ke object TradeSignal.

    Tidak mengubah field SMC yang sudah ada.
    """

    try:

        setattr(
            obj,
            name,
            value,
        )

        return True

    except Exception:

        logger.exception(
            "Gagal menambahkan attribute | %s",
            name,
        )

        return False


# =========================================================
# GET SMC BIAS
# =========================================================

def get_signal_bias(
    signal: Any,
) -> str:
    """
    Mengambil bias dari TradeSignal.

    TradeSignal Anda menggunakan:
        signal.bias
    """

    bias = _get_attr(
        signal,
        "bias",
        "NEUTRAL",
    )


    if bias is None:
        return "NEUTRAL"


    value = str(
        bias
    ).strip().upper()


    if value in (
        "BUY",
        "BULLISH",
        "LONG",
        "BULL",
    ):

        return "BUY"


    if value in (
        "SELL",
        "BEARISH",
        "SHORT",
        "BEAR",
    ):

        return "SELL"


    return "NEUTRAL"


# =========================================================
# FETCH FUNDAMENTAL
# =========================================================

def fetch_fundamental_for_signal() -> Optional[Dict[str, Any]]:
    """
    Mengambil satu berita fundamental terbaik.

    Jika API/news gagal:
        return None

    Signal SMC tetap berjalan.
    """

    try:

        news = get_latest_fundamental_news()


        if not news:

            logger.info(
                "Tidak ada fundamental news valid "
                "untuk signal saat ini."
            )

            return None


        logger.info(
            "Fundamental ditemukan | "
            "impact=%s | source=%s | title=%s",
            news.get(
                "gold_impact",
                "NEUTRAL",
            ),
            news.get(
                "source",
                "",
            ),
            news.get(
                "title",
                "",
            ),
        )


        return news


    except Exception:

        logger.exception(
            "Gagal mengambil fundamental news."
        )

        # =================================================
        # FUNDAMENTAL ERROR TIDAK BOLEH MEMATIKAN SMC
        # =================================================

        return None


# =========================================================
# ANALYZE TRADE SIGNAL
# =========================================================

def analyze_trade_signal(
    signal: Any,
    fundamental_news: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, Any]:
    """
    Menghasilkan combined analysis dari TradeSignal.

    TradeSignal SMC tidak dimodifikasi.
    """

    if signal is None:

        logger.warning(
            "analyze_trade_signal menerima signal=None."
        )

        return {

            "smc_bias": "NEUTRAL",

            "fundamental_available": False,

            "fundamental_impact": "NEUTRAL",

            "status": "SMC_NEUTRAL",

            "status_label": "⚪ SMC NEUTRAL",

            "confirmation_score": 0,

            "note": (
                "Signal SMC tidak tersedia."
            ),

            "fundamental": {},

        }


    # =====================================================
    # SMC BIAS
    # =====================================================

    smc_bias = get_signal_bias(
        signal
    )


    # =====================================================
    # FUNDAMENTAL
    # =====================================================

    if fundamental_news is None:

        fundamental_news = (
            fetch_fundamental_for_signal()
        )


    # =====================================================
    # COMBINED
    # =====================================================

    combined = build_combined_analysis(

        smc_bias=smc_bias,

        fundamental_news=fundamental_news,

    )


    return combined


# =========================================================
# ATTACH TO TRADE SIGNAL
# =========================================================

def attach_combined_to_signal(
    signal: Any,
    fundamental_news: Optional[
        Dict[str, Any]
    ] = None,
) -> Any:
    """
    Menambahkan hasil fundamental + combined
    ke TradeSignal.

    IMPORTANT:

    Field SMC berikut TIDAK disentuh:

        bias
        entry_price
        entry_type
        order_type
        is_pending
        sl
        tp1
        tp2
        probability
        reasons
        smc
        session_name
        session_note

    Data baru ditambahkan sebagai attribute:
        fundamental_news
        fundamental_impact
        fundamental_status
        fundamental_status_label
        confirmation_score
        combined_note
        combined_analysis
    """

    if signal is None:

        logger.warning(
            "Tidak dapat attach combined ke signal=None."
        )

        return signal


    # =====================================================
    # ANALYSIS
    # =====================================================

    combined = analyze_trade_signal(

        signal,

        fundamental_news,

    )


    # =====================================================
    # ATTACH FUNDAMENTAL
    # =====================================================

    _set_attr(

        signal,

        "fundamental_news",

        combined.get(
            "fundamental"
        ),

    )


    # =====================================================
    # FUNDAMENTAL IMPACT
    # =====================================================

    _set_attr(

        signal,

        "fundamental_impact",

        combined.get(
            "fundamental_impact",
            "NEUTRAL",
        ),

    )


    # =====================================================
    # STATUS
    # =====================================================

    _set_attr(

        signal,

        "fundamental_status",

        combined.get(
            "status",
            "SMC_PRIMARY",
        ),

    )


    # =====================================================
    # STATUS LABEL
    # =====================================================

    _set_attr(

        signal,

        "fundamental_status_label",

        combined.get(
            "status_label",
            "🟡 SMC PRIMARY",
        ),

    )


    # =====================================================
    # SCORE
    # =====================================================

    _set_attr(

        signal,

        "confirmation_score",

        combined.get(
            "confirmation_score",
            0,
        ),

    )


    # =====================================================
    # NOTE
    # =====================================================

    _set_attr(

        signal,

        "combined_note",

        combined.get(
            "note",
            "",
        ),

    )


    # =====================================================
    # FULL COMBINED DATA
    # =====================================================

    _set_attr(

        signal,

        "combined_analysis",

        combined,

    )


    # =====================================================
    # FUNDAMENTAL TITLE
    # =====================================================

    fundamental = combined.get(
        "fundamental"
    )


    if not isinstance(
        fundamental,
        dict,
    ):

        fundamental = {}


    _set_attr(

        signal,

        "fundamental_title",

        fundamental.get(
            "title",
            "",
        ),

    )


    # =====================================================
    # FUNDAMENTAL SOURCE
    # =====================================================

    _set_attr(

        signal,

        "fundamental_source",

        fundamental.get(
            "source",
            "",
        ),

    )


    # =====================================================
    # FUNDAMENTAL SUMMARY
    # =====================================================

    _set_attr(

        signal,

        "fundamental_summary",

        fundamental.get(
            "summary",
            "",
        ),

    )


    # =====================================================
    # FUNDAMENTAL URL
    # =====================================================

    _set_attr(

        signal,

        "fundamental_url",

        fundamental.get(
            "url",
            "",
        ),

    )


    # =====================================================
    # LOG
    # =====================================================

    logger.info(

        "Combined attached | "
        "SMC=%s | Fundamental=%s | "
        "Status=%s | Score=%s",

        combined.get(
            "smc_bias"
        ),

        combined.get(
            "fundamental_impact"
        ),

        combined.get(
            "status"
        ),

        combined.get(
            "confirmation_score"
        ),

    )


    return signal


# =========================================================
# GET COMBINED FROM SIGNAL
# =========================================================

def get_combined_from_signal(
    signal: Any,
) -> Dict[str, Any]:
    """
    Mengambil combined analysis yang sudah ditempel.
    """

    if signal is None:

        return {}


    combined = _get_attr(

        signal,

        "combined_analysis",

        None,

    )


    if isinstance(
        combined,
        dict,
    ):

        return combined


    # =====================================================
    # FALLBACK
    # =====================================================

    return {

        "smc_bias": get_signal_bias(
            signal
        ),

        "fundamental_available": False,

        "fundamental_impact": _get_attr(

            signal,

            "fundamental_impact",

            "NEUTRAL",

        ),

        "status": _get_attr(

            signal,

            "fundamental_status",

            "SMC_PRIMARY",

        ),

        "status_label": _get_attr(

            signal,

            "fundamental_status_label",

            "🟡 SMC PRIMARY",

        ),

        "confirmation_score": _get_attr(

            signal,

            "confirmation_score",

            0,

        ),

        "note": _get_attr(

            signal,

            "combined_note",

            "",

        ),

        "fundamental": _get_attr(

            signal,

            "fundamental_news",

            {},

        ),

    }


# =========================================================
# FORMAT COMBINED FROM SIGNAL
# =========================================================

def format_signal_combined(
    signal: Any,
) -> str:
    """
    Menghasilkan format Telegram untuk combined analysis.
    """

    combined = get_combined_from_signal(
        signal
    )


    if not combined:

        return (
            "🧠 *COMBINED ANALYSIS*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Data tidak tersedia."
        )


    return format_combined_analysis(
        combined
    )


# =========================================================
# FUNDAMENTAL SUMMARY
# =========================================================

def get_fundamental_summary(
    signal: Any,
) -> str:
    """
    Mengambil ringkasan fundamental dari signal.
    """

    summary = _get_attr(

        signal,

        "fundamental_summary",

        "",

    )


    if summary is None:
        return ""


    return str(
        summary
    ).strip()


# =========================================================
# FUNDAMENTAL TITLE
# =========================================================

def get_fundamental_title(
    signal: Any,
) -> str:

    value = _get_attr(

        signal,

        "fundamental_title",

        "",

    )


    if value is None:
        return ""


    return str(
        value
    ).strip()


# =========================================================
# FUNDAMENTAL SOURCE
# =========================================================

def get_fundamental_source(
    signal: Any,
) -> str:

    value = _get_attr(

        signal,

        "fundamental_source",

        "",

    )


    if value is None:
        return ""


    return str(
        value
    ).strip()


# =========================================================
# FUNDAMENTAL IMPACT
# =========================================================

def get_fundamental_impact(
    signal: Any,
) -> str:

    value = _get_attr(

        signal,

        "fundamental_impact",

        "NEUTRAL",

    )


    if value is None:
        return "NEUTRAL"


    return str(
        value
    ).strip().upper()


# =========================================================
# COMBINED STATUS
# =========================================================

def get_combined_status(
    signal: Any,
) -> str:

    value = _get_attr(

        signal,

        "fundamental_status",

        "SMC_PRIMARY",

    )


    if value is None:
        return "SMC_PRIMARY"


    return str(
        value
    ).strip().upper()


# =========================================================
# CONFIRMATION SCORE
# =========================================================

def get_confirmation_score(
    signal: Any,
) -> int:

    value = _get_attr(

        signal,

        "confirmation_score",

        0,

    )


    try:

        return int(
            value
        )

    except (
        ValueError,
        TypeError,
    ):

        return 0


# =========================================================
# DOES FUNDAMENTAL SUPPORT?
# =========================================================

def fundamental_supports_signal(
    signal: Any,
) -> bool:

    status = get_combined_status(
        signal
    )


    return status == (
        "STRONG_CONFIRMATION"
    )


# =========================================================
# DOES FUNDAMENTAL CONFLICT?
# =========================================================

def fundamental_conflicts_signal(
    signal: Any,
) -> bool:

    status = get_combined_status(
        signal
    )


    return status == (
        "FUNDAMENTAL_CONFLICT"
    )


# =========================================================
# SAFE SIGNAL PROCESSOR
# =========================================================

def process_signal(
    signal: Any,
    fundamental_news: Optional[
        Dict[str, Any]
    ] = None,
) -> Any:
    """
    Entry point sederhana.

    Dipanggil setelah signal_builder menghasilkan
    TradeSignal.

    Contoh:

        signal = generate_signal()

        signal = process_signal(
            signal
        )

    SMC tetap menjadi sumber signal utama.
    """

    if signal is None:

        logger.warning(
            "process_signal menerima signal=None."
        )

        return None


    try:

        return attach_combined_to_signal(

            signal,

            fundamental_news,

        )


    except Exception:

        logger.exception(

            "Combined processing gagal. "
            "Signal SMC tetap dikembalikan."

        )

        return signal


# =========================================================
# BATCH PROCESS
# =========================================================

def process_signals(
    signals: Any,
) -> list:
    """
    Memproses beberapa TradeSignal.

    Jika terjadi error pada satu signal,
    signal lainnya tetap diproses.
    """

    if signals is None:

        return []


    if not isinstance(
        signals,
        (
            list,
            tuple,
        ),
    ):

        signals = [
            signals
        ]


    results = []


    for signal in signals:

        try:

            processed = process_signal(
                signal
            )


            if processed is not None:

                results.append(
                    processed
                )


        except Exception:

            logger.exception(
                "Gagal memproses salah satu signal."
            )


            # =========================================
            # Tetap simpan signal asli
            # =========================================

            if signal is not None:

                results.append(
                    signal
                )


    return results


# =========================================================
# DEBUG INFO
# =========================================================

def get_combined_debug_info(
    signal: Any,
) -> Dict[str, Any]:
    """
    Informasi debug untuk log.
    """

    if signal is None:

        return {

            "available": False,

            "smc_bias": "NEUTRAL",

            "fundamental_impact": "NEUTRAL",

            "status": "NO_SIGNAL",

            "confirmation_score": 0,

        }


    return {

        "available": True,

        "smc_bias": get_signal_bias(
            signal
        ),

        "fundamental_impact": (
            get_fundamental_impact(
                signal
            )
        ),

        "status": get_combined_status(
            signal
        ),

        "confirmation_score": (
            get_confirmation_score(
                signal
            )
        ),

        "fundamental_title": (
            get_fundamental_title(
                signal
            )
        ),

        "fundamental_source": (
            get_fundamental_source(
                signal
            )
        ),

    }


# =========================================================
# HEALTH CHECK
# =========================================================

def combined_signal_health_check() -> Dict[str, Any]:
    """
    Health check adapter.
    """

    return {

        "service": (
            "combined_signal"
        ),

        "status": "ok",

        "smc_primary": (
            SMC_REMAINS_PRIMARY
        ),

        "smc_modified": False,

        "entry_modified": False,

        "sl_modified": False,

        "tp1_modified": False,

        "tp2_modified": False,

        "probability_modified": False,

    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO
    )


    print(
        "=========================================="
    )

    print(
        "COMBINED SIGNAL ADAPTER TEST"
    )

    print(
        "=========================================="
    )


    class DummySignal:

        bias = "BUY"


        entry_price = 3400.0

        sl = 3395.0

        tp1 = 3407.0

        tp2 = 3415.0


    dummy = DummySignal()


    news = {

        "title": (
            "Gold rises as US yields fall"
        ),

        "source": "Reuters",

        "url": "https://example.com",

        "summary": (
            "Gold receives support "
            "from lower US yields."
        ),

        "gold_impact": "BULLISH",

        "published_at": "",

        "age_minutes": 10,

    }


    result = process_signal(

        dummy,

        news,

    )


    print(
        format_signal_combined(
            result
        )
    )


    print(
        ""
    )


    print(
        "DEBUG:"
    )


    print(
        get_combined_debug_info(
            result
        )
    )


    print(
        ""
    )


    print(
        "HEALTH:"
    )


    print(
        combined_signal_health_check()
    )

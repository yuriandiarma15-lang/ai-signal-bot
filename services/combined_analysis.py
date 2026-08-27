"""
services/combined_analysis.py

XAU AI SIGNAL BOT
COMBINED SMC + FUNDAMENTAL ANALYSIS
====================================

Fungsi:
- Menggabungkan hasil SMC lama dengan fundamental news.
- SMC tetap menjadi analisa utama.
- Fundamental menjadi confirmation layer.
- Tidak mengubah BOS / CHoCH / OB / FVG / Liquidity.
- Tidak mengubah Entry / SL / TP1 / TP2.
- Tidak membuat signal baru.
- Hanya memberikan status konfirmasi tambahan.

LOGIC:

SMC BUY
+ Fundamental BULLISH
    -> STRONG CONFIRMATION

SMC SELL
+ Fundamental BEARISH
    -> STRONG CONFIRMATION

SMC BUY
+ Fundamental BEARISH
    -> FUNDAMENTAL CONFLICT

SMC SELL
+ Fundamental BULLISH
    -> FUNDAMENTAL CONFLICT

SMC BUY/SELL
+ Fundamental NEUTRAL
    -> SMC PRIMARY

Fundamental tidak boleh mengganti bias SMC.
"""

import logging
from typing import Any, Dict, Optional


from services.fundamental_service import (
    build_combined_fundamental_context,
)


logger = logging.getLogger(__name__)


# =========================================================
# CONFIG
# =========================================================

# Nilai dasar confidence tambahan.
# Tidak mengubah probability SMC secara langsung.
CONFIRMATION_BONUS = 10
CONFLICT_PENALTY = 10
NEUTRAL_SCORE = 0


# =========================================================
# NORMALIZE
# =========================================================

def normalize_text(
    value: Any,
) -> str:
    """
    Membersihkan text dan mengubah menjadi lowercase.
    """

    if value is None:
        return ""

    return str(
        value
    ).strip().lower()


# =========================================================
# NORMALIZE BIAS
# =========================================================

def normalize_smc_bias(
    bias: Any,
) -> str:
    """
    Mengubah berbagai format bias menjadi:

    BUY
    SELL
    NEUTRAL
    """

    value = normalize_text(
        bias
    )

    if value in (
        "buy",
        "bullish",
        "long",
        "bull",
    ):
        return "BUY"

    if value in (
        "sell",
        "bearish",
        "short",
        "bear",
    ):
        return "SELL"

    return "NEUTRAL"


# =========================================================
# NORMALIZE FUNDAMENTAL IMPACT
# =========================================================

def normalize_fundamental_impact(
    impact: Any,
) -> str:
    """
    Mengubah fundamental impact menjadi:

    BULLISH
    BEARISH
    NEUTRAL
    """

    value = normalize_text(
        impact
    )

    if value in (
        "bullish",
        "buy",
        "positive",
        "bull",
    ):
        return "BULLISH"

    if value in (
        "bearish",
        "sell",
        "negative",
        "bear",
    ):
        return "BEARISH"

    return "NEUTRAL"


# =========================================================
# FUNDAMENTAL SUPPORT
# =========================================================

def is_fundamental_supporting(
    smc_bias: str,
    fundamental_impact: str,
) -> bool:
    """
    Mengecek apakah fundamental mendukung SMC.
    """

    smc_bias = normalize_smc_bias(
        smc_bias
    )

    fundamental_impact = normalize_fundamental_impact(
        fundamental_impact
    )

    if (
        smc_bias == "BUY"
        and fundamental_impact == "BULLISH"
    ):
        return True

    if (
        smc_bias == "SELL"
        and fundamental_impact == "BEARISH"
    ):
        return True

    return False


# =========================================================
# FUNDAMENTAL CONFLICT
# =========================================================

def is_fundamental_conflict(
    smc_bias: str,
    fundamental_impact: str,
) -> bool:
    """
    Mengecek apakah fundamental berlawanan
    dengan arah SMC.
    """

    smc_bias = normalize_smc_bias(
        smc_bias
    )

    fundamental_impact = normalize_fundamental_impact(
        fundamental_impact
    )

    if (
        smc_bias == "BUY"
        and fundamental_impact == "BEARISH"
    ):
        return True

    if (
        smc_bias == "SELL"
        and fundamental_impact == "BULLISH"
    ):
        return True

    return False


# =========================================================
# COMBINATION STATUS
# =========================================================

def determine_combination_status(
    smc_bias: str,
    fundamental_impact: str,
) -> str:
    """
    Menentukan status kombinasi SMC + Fundamental.
    """

    smc_bias = normalize_smc_bias(
        smc_bias
    )

    fundamental_impact = normalize_fundamental_impact(
        fundamental_impact
    )

    # -----------------------------------------------------
    # SMC NETRAL
    # -----------------------------------------------------

    if smc_bias == "NEUTRAL":

        return "SMC_NEUTRAL"


    # -----------------------------------------------------
    # FUNDAMENTAL NETRAL
    # -----------------------------------------------------

    if fundamental_impact == "NEUTRAL":

        return "SMC_PRIMARY"


    # -----------------------------------------------------
    # SUPPORT
    # -----------------------------------------------------

    if is_fundamental_supporting(
        smc_bias,
        fundamental_impact,
    ):

        return "STRONG_CONFIRMATION"


    # -----------------------------------------------------
    # CONFLICT
    # -----------------------------------------------------

    if is_fundamental_conflict(
        smc_bias,
        fundamental_impact,
    ):

        return "FUNDAMENTAL_CONFLICT"


    return "NEUTRAL"


# =========================================================
# CONFIRMATION SCORE
# =========================================================

def calculate_confirmation_score(
    status: str,
) -> int:
    """
    Menghasilkan skor tambahan.

    STRONG_CONFIRMATION = +10
    FUNDAMENTAL_CONFLICT = -10
    lainnya = 0

    Nilai ini TERPISAH dari probability SMC.
    """

    status = normalize_text(
        status
    )

    if status == "strong_confirmation":

        return CONFIRMATION_BONUS


    if status == "fundamental_conflict":

        return -CONFLICT_PENALTY


    return NEUTRAL_SCORE


# =========================================================
# STATUS LABEL
# =========================================================

def get_status_label(
    status: str,
) -> str:
    """
    Label yang aman digunakan oleh Telegram.
    """

    status = normalize_text(
        status
    )

    if status == "strong_confirmation":

        return "🟢 STRONG CONFIRMATION"


    if status == "fundamental_conflict":

        return "🔴 FUNDAMENTAL CONFLICT"


    if status == "smc_primary":

        return "🟡 SMC PRIMARY"


    if status == "smc_neutral":

        return "⚪ SMC NEUTRAL"


    return "⚪ NEUTRAL"


# =========================================================
# BUILD COMBINATION NOTE
# =========================================================

def build_combination_note(
    smc_bias: str,
    fundamental_impact: str,
    status: str,
) -> str:
    """
    Membuat catatan analisa kombinasi.
    """

    smc_bias = normalize_smc_bias(
        smc_bias
    )

    fundamental_impact = normalize_fundamental_impact(
        fundamental_impact
    )

    status = normalize_text(
        status
    )

    # -----------------------------------------------------
    # STRONG CONFIRMATION
    # -----------------------------------------------------

    if status == "strong_confirmation":

        if smc_bias == "BUY":

            return (
                "Struktur SMC menunjukkan BUY dan "
                "fundamental memberikan dukungan bullish "
                "terhadap Gold. Kedua layer analisa searah."
            )

        if smc_bias == "SELL":

            return (
                "Struktur SMC menunjukkan SELL dan "
                "fundamental memberikan dukungan bearish "
                "terhadap Gold. Kedua layer analisa searah."
            )


    # -----------------------------------------------------
    # CONFLICT
    # -----------------------------------------------------

    if status == "fundamental_conflict":

        if smc_bias == "BUY":

            return (
                "Struktur SMC masih menunjukkan BUY, "
                "namun fundamental saat ini berlawanan "
                "dan memberikan tekanan bearish terhadap Gold. "
                "SMC tetap menjadi bias utama."
            )

        if smc_bias == "SELL":

            return (
                "Struktur SMC masih menunjukkan SELL, "
                "namun fundamental saat ini berlawanan "
                "dan memberikan tekanan bullish terhadap Gold. "
                "SMC tetap menjadi bias utama."
            )


    # -----------------------------------------------------
    # FUNDAMENTAL NETRAL
    # -----------------------------------------------------

    if status == "smc_primary":

        return (
            "Fundamental belum memberikan arah yang jelas. "
            "Analisa SMC menjadi dasar utama pengambilan signal."
        )


    # -----------------------------------------------------
    # SMC NETRAL
    # -----------------------------------------------------

    if status == "smc_neutral":

        return (
            "Struktur SMC belum memberikan arah yang cukup jelas. "
            "Fundamental tidak digunakan untuk menggantikan "
            "bias struktur."
        )


    return (
        "Kombinasi SMC dan fundamental belum memberikan "
        "konfirmasi tambahan."
    )


# =========================================================
# BUILD COMBINED ANALYSIS
# =========================================================

def build_combined_analysis(
    smc_bias: Any,
    fundamental_news: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Fungsi utama kombinasi.

    Parameter:

        smc_bias
            Bias dari SMC lama.

        fundamental_news
            Hasil dari fundamental_service.

    Return:

        dictionary hasil kombinasi.

    Penting:
        Fungsi ini TIDAK mengubah TradeSignal.
        Fungsi ini hanya menghasilkan data tambahan.
    """

    normalized_smc = normalize_smc_bias(
        smc_bias
    )


    # =====================================================
    # FUNDAMENTAL CONTEXT
    # =====================================================

    fundamental_context = (
        build_combined_fundamental_context(
            fundamental_news
        )
    )


    fundamental_available = bool(
        fundamental_context.get(
            "available",
            False,
        )
    )


    fundamental_impact = normalize_fundamental_impact(

        fundamental_context.get(
            "gold_impact",
            "NEUTRAL",
        )

    )


    # =====================================================
    # JIKA FUNDAMENTAL TIDAK TERSEDIA
    # =====================================================

    if not fundamental_available:

        status = "SMC_PRIMARY"

        score = 0

        note = (
            "Data fundamental tidak tersedia. "
            "Analisa tetap menggunakan SMC sebagai "
            "dasar utama tanpa mengubah signal."
        )


    else:

        status = determine_combination_status(

            normalized_smc,

            fundamental_impact,

        )


        score = calculate_confirmation_score(
            status
        )


        note = build_combination_note(

            normalized_smc,

            fundamental_impact,

            status,

        )


    # =====================================================
    # RESULT
    # =====================================================

    result = {

        "smc_bias": normalized_smc,

        "fundamental_available": (
            fundamental_available
        ),

        "fundamental_impact": (
            fundamental_impact
        ),

        "status": status,

        "status_label": get_status_label(
            status
        ),

        "confirmation_score": score,

        "note": note,

        "fundamental": fundamental_context,

    }


    logger.info(

        "Combined Analysis | "
        "SMC=%s | Fundamental=%s | "
        "Status=%s | Score=%s",

        normalized_smc,

        fundamental_impact,

        status,

        score,

    )


    return result


# =========================================================
# APPLY COMBINATION TO SIGNAL DATA
# =========================================================

def attach_combined_analysis(
    signal_data: Dict[str, Any],
    fundamental_news: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Menambahkan hasil kombinasi ke dictionary signal.

    Fungsi ini membuat COPY dictionary.

    Data SMC asli tidak dimodifikasi.
    """

    if not isinstance(
        signal_data,
        dict,
    ):

        logger.error(
            "signal_data harus berupa dictionary."
        )

        return {}


    result = dict(
        signal_data
    )


    # =====================================================
    # AMBIL BIAS
    # =====================================================

    smc_bias = (

        signal_data.get(
            "bias"
        )

        or signal_data.get(
            "smc_bias"
        )

        or signal_data.get(
            "direction"
        )

        or "NEUTRAL"

    )


    # =====================================================
    # COMBINED
    # =====================================================

    combined = build_combined_analysis(

        smc_bias,

        fundamental_news,

    )


    # =====================================================
    # SIMPAN SEBAGAI DATA TAMBAHAN
    # =====================================================

    result[
        "combined_analysis"
    ] = combined


    # =====================================================
    # SHORTCUT FIELD
    #
    # Hanya data tambahan.
    # Tidak overwrite:
    #
    # bias
    # entry
    # sl
    # tp1
    # tp2
    #
    # =====================================================

    result[
        "fundamental_impact"
    ] = combined[
        "fundamental_impact"
    ]


    result[
        "fundamental_status"
    ] = combined[
        "status"
    ]


    result[
        "fundamental_status_label"
    ] = combined[
        "status_label"
    ]


    result[
        "confirmation_score"
    ] = combined[
        "confirmation_score"
    ]


    result[
        "combined_note"
    ] = combined[
        "note"
    ]


    return result


# =========================================================
# TELEGRAM FORMAT
# =========================================================

def format_combined_analysis(
    combined: Optional[Dict[str, Any]],
) -> str:
    """
    Format layer kombinasi untuk Telegram.

    Bisa digunakan nanti oleh signal_builder.py.
    """

    if not combined:

        return (
            "🧠 *COMBINED ANALYSIS*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Data kombinasi tidak tersedia."
        )


    smc_bias = normalize_smc_bias(
        combined.get(
            "smc_bias"
        )
    )


    fundamental = normalize_fundamental_impact(
        combined.get(
            "fundamental_impact"
        )
    )


    status_label = normalize_text(
        combined.get(
            "status_label"
        )
    )


    note = str(
        combined.get(
            "note",
            ""
        )
    ).strip()


    score = combined.get(
        "confirmation_score",
        0,
    )


    if smc_bias == "BUY":

        smc_text = "🟢 BUY"


    elif smc_bias == "SELL":

        smc_text = "🔴 SELL"


    else:

        smc_text = "⚪ NEUTRAL"


    if fundamental == "BULLISH":

        fundamental_text = "🟢 BULLISH GOLD"


    elif fundamental == "BEARISH":

        fundamental_text = "🔴 BEARISH GOLD"


    else:

        fundamental_text = "🟡 NEUTRAL"


    lines = [

        "🧠 *COMBINED ANALYSIS*",

        "━━━━━━━━━━━━━━━━━━",

        "",

        f"📐 SMC Bias: *{smc_text}*",

        f"📰 Fundamental: *{fundamental_text}*",

        f"🎯 Status: *{status_label.upper()}*",

        f"📊 Confirmation Score: *{score:+d}*",

    ]


    if note:

        lines.extend(

            [

                "",

                "📝 *Analisa Kombinasi*",

                note,

            ]

        )


    return "\n".join(
        lines
    )


# =========================================================
# SIMPLE HELPERS
# =========================================================

def should_trade_from_combination(
    combined: Dict[str, Any],
) -> bool:
    """
    IMPORTANT:

    Fundamental TIDAK BOLEH membatalkan signal SMC
    pada layer ini.

    Fungsi ini hanya mengecek apakah SMC memiliki bias.
    """

    if not combined:

        return False


    smc_bias = normalize_smc_bias(
        combined.get(
            "smc_bias"
        )
    )


    return smc_bias in (
        "BUY",
        "SELL",
    )


# =========================================================
# HEALTH CHECK
# =========================================================

def combined_health_check() -> Dict[str, Any]:
    """
    Health check sederhana.
    """

    return {

        "service": "combined_analysis",

        "status": "ok",

        "smc_primary": True,

        "fundamental_layer": True,

        "smc_logic_modified": False,

        "entry_logic_modified": False,

        "risk_logic_modified": False,

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
        "COMBINED ANALYSIS TEST"
    )

    print(
        "=========================================="
    )


    # =====================================================
    # TEST BUY + BULLISH
    # =====================================================

    result = build_combined_analysis(

        "BUY",

        {

            "title": "Gold rises as US yields fall",

            "source": "Reuters",

            "url": "https://example.com",

            "summary": (
                "Gold gains as lower yields "
                "support demand."
            ),

            "gold_impact": "BULLISH",

            "published_at": "",

            "age_minutes": 10,

        },

    )


    print(
        format_combined_analysis(
            result
        )
    )


    print(
        ""
    )


    # =====================================================
    # TEST BUY + BEARISH
    # =====================================================

    result = build_combined_analysis(

        "BUY",

        {

            "title": "Dollar strengthens",

            "source": "Reuters",

            "url": "https://example.com",

            "summary": (
                "The dollar gains against major currencies."
            ),

            "gold_impact": "BEARISH",

            "published_at": "",

            "age_minutes": 5,

        },

    )


    print(
        format_combined_analysis(
            result
        )
    )


    print(
        ""
    )


    # =====================================================
    # TEST SELL + NEUTRAL
    # =====================================================

    result = build_combined_analysis(

        "SELL",

        {

            "title": "Markets await economic data",

            "source": "Reuters",

            "url": "https://example.com",

            "summary": (
                "Investors remain cautious."
            ),

            "gold_impact": "NEUTRAL",

            "published_at": "",

            "age_minutes": 20,

        },

    )


    print(
        format_combined_analysis(
            result
        )
    )


    print(
        ""
    )


    # =====================================================
    # HEALTH
    # =====================================================

    print(
        combined_health_check()
    )

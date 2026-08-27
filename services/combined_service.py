"""
services/combined_service.py

XAU AI SMC REAL
===============

Fungsi:
- Menggabungkan probability SMC + Fundamental
- Fundamental membaca gold_impact dari fundamental_service.py
- Tidak pernah membatalkan signal
- Selalu menghasilkan BUY / SELL probability
- Menyediakan reasons untuk signal_builder.py

COMPATIBLE DENGAN:
    services/fundamental_service.py

BOBOT:
    SMC         = 70%
    Fundamental = 30%

FUNDAMENTAL IMPACT:
    BULLISH  -> BUY 70 / SELL 30
    BEARISH  -> BUY 30 / SELL 70
    NEUTRAL  -> BUY 50 / SELL 50
"""


from typing import Any, Dict, List


# =========================================================
# CONFIG
# =========================================================

SMC_WEIGHT = 0.70
FUNDAMENTAL_WEIGHT = 0.30


# =========================================================
# FUNDAMENTAL IMPACT PROBABILITY
# =========================================================

FUNDAMENTAL_BULLISH_BUY = 70
FUNDAMENTAL_BULLISH_SELL = 30

FUNDAMENTAL_BEARISH_BUY = 30
FUNDAMENTAL_BEARISH_SELL = 70

FUNDAMENTAL_NEUTRAL_BUY = 50
FUNDAMENTAL_NEUTRAL_SELL = 50


# =========================================================
# SAFE NUMBER
# =========================================================

def _safe_probability(
    value: Any,
    default: int = 50,
) -> int:

    try:

        value = float(value)

    except (
        TypeError,
        ValueError,
    ):

        value = default

    value = max(
        0,
        min(
            100,
            value,
        ),
    )

    return int(
        round(value)
    )


# =========================================================
# GET VALUE
# =========================================================

def _get_value(
    data: Any,
    key: str,
    default=None,
):

    if isinstance(
        data,
        dict,
    ):

        return data.get(
            key,
            default,
        )

    return getattr(
        data,
        key,
        default,
    )


# =========================================================
# NORMALIZE IMPACT
# =========================================================

def _normalize_impact(
    value: Any,
) -> str:

    if value is None:

        return "NEUTRAL"

    value = str(
        value
    ).strip().upper()

    if value in (
        "BULLISH",
        "BUY",
        "POSITIVE",
        "BULL",
    ):

        return "BULLISH"

    if value in (
        "BEARISH",
        "SELL",
        "NEGATIVE",
        "BEAR",
    ):

        return "BEARISH"

    return "NEUTRAL"


# =========================================================
# GET FUNDAMENTAL PROBABILITY
# =========================================================

def _get_fundamental_probability(
    fundamental_context: Any,
) -> tuple:

    """
    Mengambil probability fundamental.

    Prioritas:

    1. probability_buy / probability_sell
    2. buy_probability / sell_probability
    3. gold_impact
    4. NEUTRAL

    Ini membuat fungsi kompatibel dengan
    fundamental_service.py sekarang.
    """

    if not fundamental_context:

        return (
            FUNDAMENTAL_NEUTRAL_BUY,
            FUNDAMENTAL_NEUTRAL_SELL,
        )


    # =====================================================
    # DIRECT PROBABILITY
    # =====================================================

    buy = _get_value(
        fundamental_context,
        "probability_buy",
        None,
    )

    sell = _get_value(
        fundamental_context,
        "probability_sell",
        None,
    )


    if buy is None:

        buy = _get_value(
            fundamental_context,
            "buy_probability",
            None,
        )


    if sell is None:

        sell = _get_value(
            fundamental_context,
            "sell_probability",
            None,
        )


    # =====================================================
    # JIKA ADA PROBABILITY LANGSUNG
    # =====================================================

    if (
        buy is not None
        and sell is not None
    ):

        return (
            _safe_probability(
                buy
            ),
            _safe_probability(
                sell
            ),
        )


    # =====================================================
    # GOLD IMPACT
    # =====================================================

    impact = _get_value(
        fundamental_context,
        "gold_impact",
        "NEUTRAL",
    )


    impact = _normalize_impact(
        impact
    )


    # =====================================================
    # BULLISH
    # =====================================================

    if impact == "BULLISH":

        return (
            FUNDAMENTAL_BULLISH_BUY,
            FUNDAMENTAL_BULLISH_SELL,
        )


    # =====================================================
    # BEARISH
    # =====================================================

    if impact == "BEARISH":

        return (
            FUNDAMENTAL_BEARISH_BUY,
            FUNDAMENTAL_BEARISH_SELL,
        )


    # =====================================================
    # NEUTRAL
    # =====================================================

    return (
        FUNDAMENTAL_NEUTRAL_BUY,
        FUNDAMENTAL_NEUTRAL_SELL,
    )


# =========================================================
# GET FUNDAMENTAL IMPACT
# =========================================================

def _get_fundamental_impact(
    fundamental_context: Any,
) -> str:

    if not fundamental_context:

        return "NEUTRAL"


    impact = _get_value(
        fundamental_context,
        "gold_impact",
        "NEUTRAL",
    )


    return _normalize_impact(
        impact
    )


# =========================================================
# NORMALIZE REASONS
# =========================================================

def _get_reasons(
    data: Any,
) -> List[str]:

    if not data:

        return []


    reasons = _get_value(
        data,
        "reasons",
        [],
    )


    if not isinstance(
        reasons,
        list,
    ):

        return []


    return [

        str(reason).strip()

        for reason in reasons

        if reason

    ]


# =========================================================
# GET FUNDAMENTAL TITLE
# =========================================================

def _get_fundamental_title(
    fundamental_context: Any,
) -> str:

    value = _get_value(
        fundamental_context,
        "title",
        "",
    )

    if value is None:

        return ""

    return str(
        value
    ).strip()


# =========================================================
# GET FUNDAMENTAL SOURCE
# =========================================================

def _get_fundamental_source(
    fundamental_context: Any,
) -> str:

    value = _get_value(
        fundamental_context,
        "source",
        "",
    )

    if value is None:

        return ""

    return str(
        value
    ).strip()


# =========================================================
# GET FUNDAMENTAL SUMMARY
# =========================================================

def _get_fundamental_summary(
    fundamental_context: Any,
) -> str:

    value = _get_value(
        fundamental_context,
        "summary",
        "",
    )

    if value is None:

        return ""

    return str(
        value
    ).strip()


# =========================================================
# COMBINE SMC + FUNDAMENTAL
# =========================================================

def combine_smc_and_fundamental(
    smc_result=None,
    fundamental_context=None,
    smc_probability_buy=None,
    smc_probability_sell=None,
    **kwargs,
) -> Dict[str, Any]:

    """
    Menggabungkan probability SMC + Fundamental.

    SMC:
        70%

    Fundamental:
        30%

    Fundamental tidak pernah membatalkan signal.

    Return:

        {
            probability_buy,
            probability_sell,
            reasons,
            smc_probability_buy,
            smc_probability_sell,
            fundamental_probability_buy,
            fundamental_probability_sell,
            fundamental_impact
        }
    """


    # =====================================================
    # SMC PROBABILITY
    # =====================================================

    if smc_probability_buy is None:

        smc_probability_buy = _get_value(
            smc_result,
            "probability_buy",
            None,
        )


    if smc_probability_sell is None:

        smc_probability_sell = _get_value(
            smc_result,
            "probability_sell",
            None,
        )


    # =====================================================
    # FALLBACK DARI BIAS
    # =====================================================

    bias = _get_value(
        smc_result,
        "bias",
        "",
    )


    if isinstance(
        bias,
        str,
    ):

        bias = bias.lower().strip()


    # -----------------------------------------------------
    # BULLISH
    # -----------------------------------------------------

    if (
        smc_probability_buy is None
        or smc_probability_sell is None
    ):

        if bias in (
            "bullish",
            "buy",
        ):

            if smc_probability_buy is None:

                smc_probability_buy = 60


            if smc_probability_sell is None:

                smc_probability_sell = 40


        # -------------------------------------------------
        # BEARISH
        # -------------------------------------------------

        elif bias in (
            "bearish",
            "sell",
        ):

            if smc_probability_buy is None:

                smc_probability_buy = 40


            if smc_probability_sell is None:

                smc_probability_sell = 60


        # -------------------------------------------------
        # NEUTRAL
        # -------------------------------------------------

        else:

            if smc_probability_buy is None:

                smc_probability_buy = 50


            if smc_probability_sell is None:

                smc_probability_sell = 50


    # =====================================================
    # NORMALIZE SMC
    # =====================================================

    smc_probability_buy = _safe_probability(
        smc_probability_buy
    )


    smc_probability_sell = _safe_probability(
        smc_probability_sell
    )


    # =====================================================
    # FUNDAMENTAL
    # =====================================================

    fundamental_buy, fundamental_sell = (
        _get_fundamental_probability(
            fundamental_context
        )
    )


    fundamental_impact = (
        _get_fundamental_impact(
            fundamental_context
        )
    )


    # =====================================================
    # COMBINE
    # =====================================================

    combined_buy = (

        (
            smc_probability_buy
            * SMC_WEIGHT
        )

        +

        (
            fundamental_buy
            * FUNDAMENTAL_WEIGHT
        )

    )


    combined_sell = (

        (
            smc_probability_sell
            * SMC_WEIGHT
        )

        +

        (
            fundamental_sell
            * FUNDAMENTAL_WEIGHT
        )

    )


    # =====================================================
    # NORMALIZE RESULT
    # =====================================================

    combined_buy = _safe_probability(
        combined_buy
    )


    combined_sell = _safe_probability(
        combined_sell
    )


    # =====================================================
    # DETERMINE WINNER
    # =====================================================

    if combined_buy > combined_sell:

        final_bias = "BUY"

    elif combined_sell > combined_buy:

        final_bias = "SELL"

    else:

        # Tie tidak membatalkan signal.
        # Gunakan SMC sebagai tie breaker.

        if smc_probability_buy >= smc_probability_sell:

            final_bias = "BUY"

        else:

            final_bias = "SELL"


    # =====================================================
    # REASONS
    # =====================================================

    reasons: List[str] = []


    # =====================================================
    # COMBINATION REASON
    # =====================================================

    reasons.append(
        (
            f"AI menggabungkan SMC "
            f"{int(SMC_WEIGHT * 100)}% "
            f"dan Fundamental "
            f"{int(FUNDAMENTAL_WEIGHT * 100)}%."
        )
    )


    # =====================================================
    # SMC REASON
    # =====================================================

    reasons.append(
        (
            f"Probability SMC: "
            f"BUY {smc_probability_buy}% | "
            f"SELL {smc_probability_sell}%."
        )
    )


    # =====================================================
    # FUNDAMENTAL REASON
    # =====================================================

    reasons.append(
        (
            f"Fundamental Gold: "
            f"{fundamental_impact}."
        )
    )


    reasons.append(
        (
            f"Probability Fundamental: "
            f"BUY {fundamental_buy}% | "
            f"SELL {fundamental_sell}%."
        )
    )


    # =====================================================
    # FINAL PROBABILITY
    # =====================================================

    reasons.append(
        (
            f"Probability gabungan: "
            f"BUY {combined_buy}% | "
            f"SELL {combined_sell}%."
        )
    )


    # =====================================================
    # FINAL BIAS
    # =====================================================

    reasons.append(
        (
            f"AI memilih {final_bias} "
            f"berdasarkan probability tertinggi."
        )
    )


    # =====================================================
    # FUNDAMENTAL ARTICLE
    # =====================================================

    title = _get_fundamental_title(
        fundamental_context
    )


    source = _get_fundamental_source(
        fundamental_context
    )


    summary = _get_fundamental_summary(
        fundamental_context
    )


    if title:

        reasons.append(
            f"Headline fundamental: {title}"
        )


    if source:

        reasons.append(
            f"Sumber fundamental: {source}"
        )


    if summary:

        # Batasi agar tidak membuat reasons terlalu panjang.

        short_summary = summary[:300]

        if len(summary) > 300:

            short_summary += "..."


        reasons.append(
            f"Dampak berita: {short_summary}"
        )


    # =====================================================
    # ORIGINAL FUNDAMENTAL REASONS
    # =====================================================

    fundamental_reasons = _get_reasons(
        fundamental_context
    )


    for reason in fundamental_reasons[:5]:

        reasons.append(
            f"Fundamental AI: {reason}"
        )


    # =====================================================
    # RETURN
    # =====================================================

    return {

        # -------------------------------------------------
        # FINAL PROBABILITY
        # -------------------------------------------------

        "probability_buy": (
            combined_buy
        ),

        "probability_sell": (
            combined_sell
        ),

        # -------------------------------------------------
        # FINAL BIAS
        # -------------------------------------------------

        "bias": final_bias,

        # -------------------------------------------------
        # REASONS
        # -------------------------------------------------

        "reasons": reasons,

        # -------------------------------------------------
        # SMC
        # -------------------------------------------------

        "smc_probability_buy": (
            smc_probability_buy
        ),

        "smc_probability_sell": (
            smc_probability_sell
        ),

        # -------------------------------------------------
        # FUNDAMENTAL
        # -------------------------------------------------

        "fundamental_probability_buy": (
            fundamental_buy
        ),

        "fundamental_probability_sell": (
            fundamental_sell
        ),

        "fundamental_impact": (
            fundamental_impact
        ),

        # -------------------------------------------------
        # ARTICLE
        # -------------------------------------------------

        "fundamental_title": (
            title
        ),

        "fundamental_source": (
            source
        ),

        "fundamental_summary": (
            summary
        ),

    }


# =========================================================
# SIMPLE TEST
# =========================================================

if __name__ == "__main__":

    # =====================================================
    # TEST BULLISH
    # =====================================================

    smc_test = {

        "bias": "bullish",

        "probability_buy": 70,

        "probability_sell": 30,

    }


    fundamental_test = {

        "available": True,

        "gold_impact": "BULLISH",

        "title": (
            "Gold rises as markets expect lower rates"
        ),

        "source": "Test Source",

        "summary": (
            "Markets expect monetary policy "
            "to become more dovish."
        ),

    }


    result = combine_smc_and_fundamental(

        smc_result=smc_test,

        fundamental_context=fundamental_test,

    )


    print(
        "=========================================="
    )

    print(
        "COMBINED SERVICE TEST"
    )

    print(
        "=========================================="
    )

    print(
        "BUY :",
        result["probability_buy"],
        "%"
    )

    print(
        "SELL:",
        result["probability_sell"],
        "%"
    )

    print(
        "BIAS:",
        result["bias"]
    )

    print(
        "IMPACT:",
        result["fundamental_impact"]
    )

    print(
        "=========================================="
    )

    for reason in result["reasons"]:

        print(
            "-",
            reason
        )

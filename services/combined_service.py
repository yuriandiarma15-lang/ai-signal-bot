"""
services/combined_service.py

XAU AI SMC REAL
===============

Fungsi:
- Menggabungkan probability SMC + fundamental
- Tidak pernah memblokir signal
- Selalu menghasilkan BUY / SELL probability
- Menyediakan reasons untuk signal_builder.py
"""

from typing import Any, Dict, List


# =========================================================
# CONFIG
# =========================================================

SMC_WEIGHT = 0.70
FUNDAMENTAL_WEIGHT = 0.30


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

    if isinstance(data, dict):

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
# EXTRACT FUNDAMENTAL PROBABILITY
# =========================================================

def _get_fundamental_probability(
    fundamental_context: Any,
) -> tuple:

    if not fundamental_context:

        return 50, 50

    buy = None
    sell = None

    # -----------------------------------------------------
    # DICT
    # -----------------------------------------------------

    if isinstance(
        fundamental_context,
        dict,
    ):

        buy = (
            fundamental_context.get(
                "probability_buy"
            )
        )

        sell = (
            fundamental_context.get(
                "probability_sell"
            )
        )

        if buy is None:

            buy = (
                fundamental_context.get(
                    "buy_probability"
                )
            )

        if sell is None:

            sell = (
                fundamental_context.get(
                    "sell_probability"
                )
            )

    # -----------------------------------------------------
    # OBJECT
    # -----------------------------------------------------

    else:

        buy = getattr(
            fundamental_context,
            "probability_buy",
            None,
        )

        sell = getattr(
            fundamental_context,
            "probability_sell",
            None,
        )

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    if buy is None:
        buy = 50

    if sell is None:
        sell = 50

    return (
        _safe_probability(buy),
        _safe_probability(sell),
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
        str(reason)
        for reason in reasons
        if reason
    ]


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
    Menggabungkan probability SMC dan fundamental.

    SMC:
        70%

    Fundamental:
        30%

    Signal TIDAK dibatalkan meskipun fundamental
    tidak tersedia.

    Output:
        {
            probability_buy,
            probability_sell,
            reasons
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

    # -----------------------------------------------------
    # FALLBACK DARI BIAS
    # -----------------------------------------------------

    if (
        smc_probability_buy is None
        or smc_probability_sell is None
    ):

        bias = _get_value(
            smc_result,
            "bias",
            "",
        )

        if bias == "bullish":

            smc_probability_buy = (
                60
                if smc_probability_buy is None
                else smc_probability_buy
            )

            smc_probability_sell = (
                40
                if smc_probability_sell is None
                else smc_probability_sell
            )

        elif bias == "bearish":

            smc_probability_buy = (
                40
                if smc_probability_buy is None
                else smc_probability_buy
            )

            smc_probability_sell = (
                60
                if smc_probability_sell is None
                else smc_probability_sell
            )

        else:

            smc_probability_buy = (
                50
                if smc_probability_buy is None
                else smc_probability_buy
            )

            smc_probability_sell = (
                50
                if smc_probability_sell is None
                else smc_probability_sell
            )

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

    # =====================================================
    # COMBINATION
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

    combined_buy = _safe_probability(
        combined_buy
    )

    combined_sell = _safe_probability(
        combined_sell
    )

    # =====================================================
    # REASONS
    # =====================================================

    reasons = []

    reasons.append(
        (
            f"AI menggabungkan SMC "
            f"{int(SMC_WEIGHT * 100)}% dan Fundamental "
            f"{int(FUNDAMENTAL_WEIGHT * 100)}%."
        )
    )

    reasons.append(
        (
            f"Probability SMC: "
            f"BUY {smc_probability_buy}% | "
            f"SELL {smc_probability_sell}%."
        )
    )

    reasons.append(
        (
            f"Probability Fundamental: "
            f"BUY {fundamental_buy}% | "
            f"SELL {fundamental_sell}%."
        )
    )

    reasons.append(
        (
            f"Probability gabungan: "
            f"BUY {combined_buy}% | "
            f"SELL {combined_sell}%."
        )
    )

    # -----------------------------------------------------
    # FUNDAMENTAL REASONS
    # -----------------------------------------------------

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

        "probability_buy": combined_buy,

        "probability_sell": combined_sell,

        "reasons": reasons,

        "smc_probability_buy": (
            smc_probability_buy
        ),

        "smc_probability_sell": (
            smc_probability_sell
        ),

        "fundamental_probability_buy": (
            fundamental_buy
        ),

        "fundamental_probability_sell": (
            fundamental_sell
        ),
    }

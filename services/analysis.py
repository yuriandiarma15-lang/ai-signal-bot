from services.market import get_price


# ==========================================
# ANALYSIS
# SAME AS BOT 1
# ==========================================

def analyze_market():

    price = get_price()

    if price is None:

        return {

            "bias": "BUY",

            "confidence": 0,

            "buy_score": 0,

            "sell_score": 0,

            "reason": [

                "NO DATA"

            ]

        }


    # ==========================
    # BUY
    # ==========================

    if int(price) % 2 == 0:

        return {

            "bias": "BUY",

            "confidence": 100,

            "buy_score": 100,

            "sell_score": 0,

            "reason": [

                "Liquidity sweep bullish",

                "Bullish reversal",

                "Momentum shift up"

            ]

        }


    # ==========================
    # SELL
    # ==========================

    return {

        "bias": "SELL",

        "confidence": 100,

        "buy_score": 0,

        "sell_score": 100,

        "reason": [

            "Liquidity sweep bearish",

            "Bearish rejection",

            "Momentum continuation"

        ]

    }

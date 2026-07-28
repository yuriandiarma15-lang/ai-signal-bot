from datetime import datetime

from services.market import get_price

from services.analysis import (
    analyze_market
)


# =====================================
# BUILD SIGNAL
# =====================================

def build_signal():


    price = get_price()


    if price is None:


        return """

⚠️ XAUUSD SIGNAL

Harga tidak tersedia

        """



    analysis = analyze_market()



    bias = analysis.get(
        "bias",
        "BUY"
    )


    confidence = analysis.get(
        "confidence",
        50
    )


    reasons = analysis.get(
        "reason",
        []
    )



    entry = price



    # ==========================
    # BUY
    # ==========================

    if bias == "BUY":


        setup = "BUY LIMIT"


        tp1 = entry + 7

        tp2 = entry + 15

        sl = entry - 5



    # ==========================
    # SELL
    # ==========================

    else:


        setup = "SELL LIMIT"


        tp1 = entry - 7

        tp2 = entry - 15

        sl = entry + 5





    reason_text = "\n".join(

        [

            f"- {x}"

            for x in reasons

        ]

    )



    now = datetime.now().strftime(

        "%d-%m-%Y %H:%M WIB"

    )





    message = f"""

📊 <b>XAUUSD SIGNAL</b>


🕒 {now}


━━━━━━━━━━━━━━


📈 <b>BIAS: {bias}</b>


📌 <b>ENTRY:</b>

{setup} @ {entry:.2f}



🎯 <b>TP1:</b> {tp1:.2f}

🎯 <b>TP2:</b> {tp2:.2f}


⛔ <b>SL:</b> {sl:.2f}



🔥 <b>CONFIDENCE:</b>

{confidence}%



🧠 <b>REASON:</b>

{reason_text}


━━━━━━━━━━━━━━


🤖 <b>XAU AI ASSISTANT</b>

"""



    return message

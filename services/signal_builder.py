from datetime import datetime, timezone

from services.market import get_price
from services.analysis import analyze_market


# =====================================
# BUILD SIGNAL
# =====================================

def build_signal():
    price = get_price()

    if price is None:
        return "⚠️ <b>XAUUSD SIGNAL</b>\nHarga tidak tersedia"

    analysis = analyze_market()
    bias = analysis.get("bias", "BUY")
    confidence = analysis.get("confidence", 50)
    reasons = analysis.get("reason", [])

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

    reason_text = "\n".join(f"- {x}" for x in reasons)

    now = datetime.now(timezone.utc).strftime("%d-%m-%Y %H:%M UTC")

    message = (
        f"📊 <b>XAUUSD SIGNAL</b>\n"
        f"🕒 {now}\n"
        f"━━━━━━━━━━━━━━\n"
        f"📈 <b>BIAS:</b> {bias}\n"
        f"📌 <b>ENTRY:</b> {setup} @ {entry:.2f}\n"
        f"🎯 <b>TP1:</b> {tp1:.2f}\n"
        f"🎯 <b>TP2:</b> {tp2:.2f}\n"
        f"⛔ <b>SL:</b> {sl:.2f}\n"
        f"🔥 <b>CONFIDENCE:</b> {confidence}%\n"
        f"🧠 <b>REASON:</b>\n{reason_text}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🤖 <b>XAU AI ASSISTANT</b>"
    )

    return message

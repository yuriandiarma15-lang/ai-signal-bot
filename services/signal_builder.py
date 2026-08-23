"""
Signal Builder
==============

Adapter untuk menghubungkan logic SMC utama dari signal_generator.py
ke sistem bot yang menggunakan services.signal_builder.

Logic trading TIDAK dilakukan di sini.

Semua analisa:
- M5 SMC
- BOS
- CHoCH
- Order Block
- FVG
- Liquidity Sweep
- M1 entry
- Market / Pending
- SL
- TP1
- TP2
- Confidence
- Reason

berasal dari signal_generator.py.
"""

from signal_generator import (
    generate_signal,
    format_signal_message,
)


# =========================================================
# BUILD SIGNAL
# =========================================================

def build_signal(
    structure_candle_count=None,
):
    """
    Generate signal menggunakan engine SMC utama.

    Scheduler:
        build_signal()

    Manual /signal:
        build_signal(structure_candle_count=12)
    """

    try:

        signal = generate_signal(
            structure_candle_count=structure_candle_count
        )

        return format_signal_message(signal)

    except Exception as e:

        return (
            "⚠️ *XAU AI SIGNAL*\n\n"
            "Signal tidak dapat dibuat.\n\n"
            f"Error: `{str(e)}`"
        )

"""
signal_builder.py

XAU AI SIGNAL ENGINE
====================

Menggabungkan:

- Analisa struktur SMC M5
- Timing entry M1
- Order Block
- Fair Value Gap
- Liquidity / BOS / CHoCH dari SMC analyzer
- Zone freshness
- FVG partial/full fill
- Market / Pending Limit
- Maximum zone distance
- M1 rejection confirmation
- Risk management
- SL / TP
- Probability
- Session
- Entry reason bank

ATURAN ENTRY UTAMA
==================

1. BULLISH
   - Bullish OB/FVG di bawah harga
   - Fresh -> Buy Limit
   - Sudah diretest + rejection bullish -> Market Buy
   - Partial FVG -> WAIT
   - Zona terlalu jauh -> NO TRADE

2. BEARISH
   - Bearish OB/FVG di atas harga
   - Fresh -> Sell Limit
   - Sudah diretest + rejection bearish -> Market Sell
   - Partial FVG -> WAIT
   - Zona terlalu jauh -> NO TRADE

3. Tidak ada zona valid
   -> NO TRADE

4. Tidak menggunakan Buy Stop / Sell Stop
   untuk zona SMC retracement.

5. Harga sekarang tidak boleh mengejar zona yang terlalu jauh.

6. M5 menggunakan candle CLOSED.

7. M1 digunakan untuk validasi timing entry.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo

from .twelvedata_client import Candle, fetch_candles
from smc_analyzer import analyze, SMCResult
from entry_reason_bank import (
    get_entry_reason,
    get_session_extra_note,
)

from config import (
    CANDLES_FOR_STRUCTURE,
    CANDLES_LOOKBACK,
    CANDLES_ENTRY_LOOKBACK,
    TF_STRUCTURE,
    TF_ENTRY,
    SL_DISTANCE,
    TP1_DISTANCE,
    TP2_DISTANCE,
    SL_PIPS,
    TP1_PIPS,
    TP2_PIPS,
    SESSIONS,
    MARKET_ENTRY_TOLERANCE,
    PENDING_ORDER_TIMEOUT_MINUTES,
    TIMEZONE,
)

# =========================================================
# OPTIONAL CONFIG
# =========================================================

try:
    from config import MAX_ZONE_DISTANCE
except ImportError:
    MAX_ZONE_DISTANCE = SL_DISTANCE * 1.5


try:
    from config import MIN_RR_TP1
except ImportError:
    MIN_RR_TP1 = 1.20


try:
    from config import MIN_RR_TP2
except ImportError:
    MIN_RR_TP2 = 2.00


try:
    from config import REQUIRE_M1_REJECTION
except ImportError:
    REQUIRE_M1_REJECTION = True


try:
    from config import ALLOW_PARTIAL_FVG_MARKET
except ImportError:
    ALLOW_PARTIAL_FVG_MARKET = False


try:
    from config import M1_CONFIRMATION_CANDLES
except ImportError:
    M1_CONFIRMATION_CANDLES = 5


# =========================================================
# TIMEZONE
# =========================================================

WIB = ZoneInfo(TIMEZONE)


# =========================================================
# TRADE SIGNAL
# =========================================================

@dataclass
class TradeSignal:

    timestamp: datetime

    bias: str

    entry_price: float

    entry_type: str

    order_type: str

    is_pending: bool

    sl: float

    tp1: float

    tp2: float

    probability: int

    reasons: List[str]

    smc: SMCResult

    session_name: str

    session_note: str

    zone_touched: bool = False

    zone_type: Optional[str] = None

    fill_status: str = "untouched"

    zone_low: Optional[float] = None

    zone_high: Optional[float] = None

    m1_confirmation: bool = False

    rr_tp1: float = 0.0

    rr_tp2: float = 0.0


# =========================================================
# EXCEPTION
# =========================================================

class NoTradeSignal(Exception):
    """
    Dipakai ketika kondisi market tidak memenuhi syarat entry.
    """

    pass


# =========================================================
# SESSION
# =========================================================

def _get_session_info(
    dt: datetime,
) -> Tuple[str, str]:

    if dt.tzinfo is None:

        dt = dt.replace(
            tzinfo=WIB
        )

    else:

        dt = dt.astimezone(
            WIB
        )

    hour = dt.hour

    for session in SESSIONS:

        if hour in session["hours"]:

            return (
                session["name"],
                session["note"],
            )

    return (
        "Trading",
        "pantau pergerakan harga dengan disiplin dan manajemen risiko",
    )


# =========================================================
# DATETIME
# =========================================================

def _to_wib(
    dt: datetime,
) -> datetime:

    if dt.tzinfo is None:

        return dt.replace(
            tzinfo=WIB
        )

    return dt.astimezone(
        WIB
    )


def _get_current_m5_open_time(
    now: datetime,
) -> datetime:

    now = _to_wib(
        now
    )

    minute = (
        now.minute // 5
    ) * 5

    return now.replace(
        minute=minute,
        second=0,
        microsecond=0,
    )


# =========================================================
# CLOSED M5
# =========================================================

def _get_closed_m5_candles(
    candles: List[Candle],
    count: int,
) -> List[Candle]:

    if count <= 0:

        raise ValueError(
            "Jumlah candle closed harus lebih besar dari 0."
        )

    now = datetime.now(
        WIB
    )

    current_open = (
        _get_current_m5_open_time(
            now
        )
    )

    closed = []

    for candle in candles:

        candle_time = _to_wib(
            candle.time
        )

        if candle_time < current_open:

            closed.append(
                candle
            )

    closed.sort(
        key=lambda c: _to_wib(c.time)
    )

    if len(closed) < count:

        raise ValueError(
            "Candle M5 CLOSED tidak cukup. "
            f"Tersedia {len(closed)}, "
            f"dibutuhkan {count}. "
            f"Waktu WIB: "
            f"{now.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    return closed[-count:]


# =========================================================
# ZONE OVERLAP
# =========================================================

def _candle_overlaps_zone(
    candle: Candle,
    zone_low: float,
    zone_high: float,
) -> bool:

    return not (
        candle.high < zone_low
        or candle.low > zone_high
    )


# =========================================================
# ZONE TOUCH
# =========================================================

def _zone_touched_by_recent_price(
    zone_low: float,
    zone_high: float,
    recent_candles: List[Candle],
) -> bool:

    if not recent_candles:

        return False

    for candle in recent_candles:

        if _candle_overlaps_zone(
            candle,
            zone_low,
            zone_high,
        ):

            return True

    return False


# =========================================================
# FVG FILL STATUS
# =========================================================

def _fvg_fill_status(
    direction: str,
    top: float,
    bottom: float,
    recent_candles: List[Candle],
) -> str:
    """
    Return:

        untouched
        partial
        full

    Bullish FVG:

        harga dari atas turun ke gap.

    Full:

        close menembus sisi bawah gap.

    Bearish FVG:

        harga dari bawah naik ke gap.

    Full:

        close menembus sisi atas gap.
    """

    if not recent_candles:

        return "untouched"

    touched = _zone_touched_by_recent_price(
        bottom,
        top,
        recent_candles,
    )

    if not touched:

        return "untouched"

    if direction == "bullish":

        fully_closed_through = any(
            candle.close < bottom
            for candle in recent_candles
        )

    else:

        fully_closed_through = any(
            candle.close > top
            for candle in recent_candles
        )

    if fully_closed_through:

        return "full"

    return "partial"


# =========================================================
# M1 REJECTION
# =========================================================

def _bullish_rejection(
    candles: List[Candle],
    zone_low: float,
    zone_high: float,
) -> bool:
    """
    Mencari indikasi rejection bullish:

    - candle menyentuh zona
    - close berada di atas open
    - close berada relatif dekat high
    """

    if not candles:

        return False

    for candle in candles:

        if not _candle_overlaps_zone(
            candle,
            zone_low,
            zone_high,
        ):

            continue

        body = candle.body
        candle_range = candle.range

        if candle_range <= 0:

            continue

        close_strength = (
            candle.close - candle.low
        ) / candle_range

        if (
            candle.is_bullish
            and close_strength >= 0.55
        ):

            return True

    return False


def _bearish_rejection(
    candles: List[Candle],
    zone_low: float,
    zone_high: float,
) -> bool:
    """
    Mencari indikasi rejection bearish.
    """

    if not candles:

        return False

    for candle in candles:

        if not _candle_overlaps_zone(
            candle,
            zone_low,
            zone_high,
        ):

            continue

        candle_range = candle.range

        if candle_range <= 0:

            continue

        close_strength = (
            candle.high - candle.close
        ) / candle_range

        if (
            candle.is_bearish
            and close_strength >= 0.55
        ):

            return True

    return False


def _has_m1_rejection(
    bias: str,
    zone_low: float,
    zone_high: float,
    recent_candles: List[Candle],
) -> bool:

    check_candles = (
        recent_candles[
            -M1_CONFIRMATION_CANDLES:
        ]
        if len(recent_candles)
        >= M1_CONFIRMATION_CANDLES
        else recent_candles
    )

    if bias == "bullish":

        return _bullish_rejection(
            check_candles,
            zone_low,
            zone_high,
        )

    return _bearish_rejection(
        check_candles,
        zone_low,
        zone_high,
    )


# =========================================================
# ZONE DIRECTION VALIDATION
# =========================================================

def _zone_matches_bias(
    bias: str,
    current_price: float,
    zone_low: float,
    zone_high: float,
) -> bool:
    """
    Bullish:
        zona ideal berada di bawah harga.

    Bearish:
        zona ideal berada di atas harga.

    Jika harga sedang berada di dalam zona,
    tetap dianggap valid.
    """

    if bias == "bullish":

        return zone_low <= current_price

    if bias == "bearish":

        return zone_high >= current_price

    return False


# =========================================================
# ZONE DISTANCE
# =========================================================

def _zone_distance(
    current_price: float,
    zone_low: float,
    zone_high: float,
) -> float:

    if (
        zone_low
        <= current_price
        <= zone_high
    ):

        return 0.0

    if current_price < zone_low:

        return zone_low - current_price

    return current_price - zone_high


# =========================================================
# FIND ENTRY ZONE
# =========================================================

def _find_entry_zone(
    smc: SMCResult,
    current_price: float,
    recent_candles: List[Candle],
    max_distance: float = MAX_ZONE_DISTANCE,
):
    """
    Cari zona terbaik.

    Prioritas:

    1. Zona sesuai bias
    2. Zona belum disentuh
    3. Zona terdekat
    4. FVG partial/full sebagai fallback

    Return:

        price
        zone_type
        fill_status
        zone_low
        zone_high
    """

    candidates = []

    # =====================================================
    # ORDER BLOCK
    # =====================================================

    for ob in smc.order_blocks:

        zone_low = float(
            min(ob.low, ob.high)
        )

        zone_high = float(
            max(ob.low, ob.high)
        )

        mid = (
            zone_low
            + zone_high
        ) / 2

        distance = _zone_distance(
            current_price,
            zone_low,
            zone_high,
        )

        # Jangan mengejar zona yang terlalu jauh.
        if (
            max_distance is not None
            and distance > max_distance
        ):
            continue

        if not _zone_matches_bias(
            smc.bias,
            current_price,
            zone_low,
            zone_high,
        ):
            continue

        touched = (
            _zone_touched_by_recent_price(
                zone_low,
                zone_high,
                recent_candles,
            )
        )

        status = (
            "full"
            if touched
            else "untouched"
        )

        candidates.append(
            {
                "distance": distance,
                "price": mid,
                "type": "Order Block",
                "status": status,
                "low": zone_low,
                "high": zone_high,
            }
        )

    # =====================================================
    # FAIR VALUE GAP
    # =====================================================

    for fvg in smc.fvgs:

        zone_low = float(
            min(
                fvg.bottom,
                fvg.top,
            )
        )

        zone_high = float(
            max(
                fvg.bottom,
                fvg.top,
            )
        )

        mid = (
            zone_low
            + zone_high
        ) / 2

        distance = _zone_distance(
            current_price,
            zone_low,
            zone_high,
        )

        if (
            max_distance is not None
            and distance > max_distance
        ):
            continue

        if not _zone_matches_bias(
            smc.bias,
            current_price,
            zone_low,
            zone_high,
        ):
            continue

        status = _fvg_fill_status(
            fvg.direction,
            zone_high,
            zone_low,
            recent_candles,
        )

        candidates.append(
            {
                "distance": distance,
                "price": mid,
                "type": "Fair Value Gap",
                "status": status,
                "low": zone_low,
                "high": zone_high,
            }
        )

    if not candidates:

        return (
            None,
            None,
            "untouched",
            None,
            None,
        )

    # =====================================================
    # PRIORITAS
    # =====================================================

    untouched = [
        c
        for c in candidates
        if c["status"] == "untouched"
    ]

    if untouched:

        pool = untouched

    else:

        pool = candidates

    pool.sort(
        key=lambda x: x["distance"]
    )

    selected = pool[0]

    return (
        selected["price"],
        selected["type"],
        selected["status"],
        selected["low"],
        selected["high"],
    )


# =========================================================
# ENTRY DESCRIPTION
# =========================================================

def _build_entry_description(
    order_type: str,
    is_pending: bool,
    fill_status: str,
    zone_type: Optional[str],
    m1_confirmation: bool,
) -> str:

    if is_pending:

        return (
            f"Pending {order_type} "
            "(menunggu retest zona SMC)"
        )

    if (
        zone_type == "Fair Value Gap"
        and fill_status == "partial"
    ):

        return (
            "Market "
            "(FVG partial fill)"
        )

    if fill_status == "full":

        if m1_confirmation:

            return (
                "Market "
                "(zona sudah diretest + "
                "M1 rejection)"
            )

        return (
            "Market "
            "(zona sudah termitigasi)"
        )

    if m1_confirmation:

        return (
            "Market "
            "(M1 rejection confirmation)"
        )

    return (
        "Market "
        "(zona valid)"
    )


# =========================================================
# RISK CALCULATION
# =========================================================

def _calculate_risk(
    bias: str,
    entry_price: float,
):
    if bias == "bullish":

        sl = (
            entry_price
            - SL_DISTANCE
        )

        tp1 = (
            entry_price
            + TP1_DISTANCE
        )

        tp2 = (
            entry_price
            + TP2_DISTANCE
        )

    else:

        sl = (
            entry_price
            + SL_DISTANCE
        )

        tp1 = (
            entry_price
            - TP1_DISTANCE
        )

        tp2 = (
            entry_price
            - TP2_DISTANCE
        )

    risk = abs(
        entry_price - sl
    )

    reward_tp1 = abs(
        tp1 - entry_price
    )

    reward_tp2 = abs(
        tp2 - entry_price
    )

    rr_tp1 = (
        reward_tp1 / risk
        if risk > 0
        else 0
    )

    rr_tp2 = (
        reward_tp2 / risk
        if risk > 0
        else 0
    )

    return (
        sl,
        tp1,
        tp2,
        rr_tp1,
        rr_tp2,
    )


# =========================================================
# VALIDATE RISK
# =========================================================

def _validate_rr(
    rr_tp1: float,
    rr_tp2: float,
) -> bool:

    if rr_tp1 < MIN_RR_TP1:

        return False

    if rr_tp2 < MIN_RR_TP2:

        return False

    return True


# =========================================================
# ORDER TYPE
# =========================================================

def _determine_order_type(
    bias: str,
    entry_price: float,
    current_price: float,
    has_zone: bool,
    fill_status: str,
    m1_confirmation: bool,
) -> Tuple[str, bool]:

    if not has_zone:

        return (
            "NO TRADE",
            False,
        )

    # =====================================================
    # FVG PARTIAL
    # =====================================================

    if fill_status == "partial":

        if (
            ALLOW_PARTIAL_FVG_MARKET
            and m1_confirmation
        ):

            return (
                "Market",
                False,
            )

        return (
            "WAIT",
            False,
        )

    # =====================================================
    # ZONA SUDAH FULL
    # =====================================================

    if fill_status == "full":

        if REQUIRE_M1_REJECTION:

            if not m1_confirmation:

                return (
                    "WAIT",
                    False,
                )

        return (
            "Market",
            False,
        )

    # =====================================================
    # ZONA FRESH
    # =====================================================

    if fill_status == "untouched":

        if bias == "bullish":

            if entry_price < current_price:

                return (
                    "Buy Limit",
                    True,
                )

            if (
                abs(
                    entry_price
                    - current_price
                )
                <= MARKET_ENTRY_TOLERANCE
            ):

                return (
                    "Market",
                    False,
                )

            return (
                "WAIT",
                False,
            )

        else:

            if entry_price > current_price:

                return (
                    "Sell Limit",
                    True,
                )

            if (
                abs(
                    entry_price
                    - current_price
                )
                <= MARKET_ENTRY_TOLERANCE
            ):

                return (
                    "Market",
                    False,
                )

            return (
                "WAIT",
                False,
            )

    return (
        "WAIT",
        False,
    )


# =========================================================
# PROBABILITY
# =========================================================

def _calculate_probability(
    smc_score: int,
    zone_type: Optional[str],
    fill_status: str,
    is_pending: bool,
    m1_confirmation: bool,
) -> int:

    score = int(
        max(
            0,
            min(
                100,
                smc_score,
            ),
        )
    )

    # =====================================================
    # ZONE
    # =====================================================

    if zone_type:

        score += 3

    # =====================================================
    # M1 CONFIRMATION
    # =====================================================

    if m1_confirmation:

        score += 5

    # =====================================================
    # FRESH ZONE
    # =====================================================

    if fill_status == "untouched":

        score += 3

    # =====================================================
    # PARTIAL FVG
    # =====================================================

    if fill_status == "partial":

        score -= 8

    # =====================================================
    # FULL MITIGATION
    # =====================================================

    if fill_status == "full":

        score += 1

    # =====================================================
    # PENDING
    # =====================================================

    if is_pending:

        score -= 1

    return int(
        max(
            0,
            min(
                100,
                score,
            ),
        )
    )


# =========================================================
# GENERATE SIGNAL
# =========================================================

def generate_signal(
    structure_candle_count: Optional[int] = None,
) -> TradeSignal:

    now = datetime.now(
        WIB
    )

    # =====================================================
    # M5
    # =====================================================

    if structure_candle_count is None:

        m5_outputsize = (
            CANDLES_LOOKBACK
        )

    else:

        m5_outputsize = max(
            structure_candle_count + 8,
            20,
        )

    structure_raw = fetch_candles(
        interval=TF_STRUCTURE,
        outputsize=m5_outputsize,
    )

    if not structure_raw:

        raise ValueError(
            "Twelve Data tidak mengembalikan candle M5."
        )

    # =====================================================
    # MANUAL /SIGNAL
    # =====================================================

    if structure_candle_count is not None:

        structure_candles = (
            _get_closed_m5_candles(
                structure_raw,
                structure_candle_count,
            )
        )

        first_time = _to_wib(
            structure_candles[0].time
        )

        last_time = _to_wib(
            structure_candles[-1].time
        )

        print(
            "[M5 CLOSED] "
            f"{len(structure_candles)} candle | "
            f"{first_time.strftime('%H:%M')} -> "
            f"{last_time.strftime('%H:%M')} WIB"
        )

    # =====================================================
    # SCHEDULER
    # =====================================================

    else:

        structure_candles = (
            _get_closed_m5_candles(
                structure_raw,
                CANDLES_FOR_STRUCTURE,
            )
        )

    if len(structure_candles) < CANDLES_FOR_STRUCTURE:

        raise ValueError(
            "Data M5 closed tidak cukup untuk analisa."
        )

    # =====================================================
    # SMC
    # =====================================================

    smc = analyze(
        structure_candles
    )

    if smc.bias not in (
        "bullish",
        "bearish",
    ):

        raise NoTradeSignal(
            "Bias SMC tidak valid."
        )

    # =====================================================
    # M1
    # =====================================================

    entry_candles = fetch_candles(
        interval=TF_ENTRY,
        outputsize=CANDLES_ENTRY_LOOKBACK,
    )

    if not entry_candles:

        raise ValueError(
            "Data candle M1 tidak tersedia."
        )

    # =====================================================
    # CURRENT PRICE
    #
    # Untuk sekarang kita tetap menggunakan close candle
    # M1 terbaru karena client Twelve Data yang kamu punya
    # belum memiliki endpoint quote.
    # =====================================================

    current_price = float(
        entry_candles[-1].close
    )

    # =====================================================
    # RECENT M1
    # =====================================================

    recent_candles = (
        entry_candles[-10:]
        if len(entry_candles) >= 10
        else entry_candles
    )

    # =====================================================
    # FIND ZONE
    # =====================================================

    (
        zone_price,
        zone_type,
        fill_status,
        zone_low,
        zone_high,
    ) = _find_entry_zone(
        smc=smc,
        current_price=current_price,
        recent_candles=recent_candles,
        max_distance=MAX_ZONE_DISTANCE,
    )

    has_zone = (
        zone_price is not None
    )

    # =====================================================
    # NO ZONE
    # =====================================================

    if not has_zone:

        raise NoTradeSignal(
            "Tidak ditemukan OB/FVG yang valid "
            f"dalam radius {MAX_ZONE_DISTANCE} USD "
            "dari harga sekarang."
        )

    # =====================================================
    # M1 CONFIRMATION
    # =====================================================

    m1_confirmation = (
        _has_m1_rejection(
            bias=smc.bias,
            zone_low=zone_low,
            zone_high=zone_high,
            recent_candles=recent_candles,
        )
    )

    # =====================================================
    # ENTRY PRICE
    # =====================================================

    if fill_status == "untouched":

        entry_price = float(
            zone_price
        )

    else:

        entry_price = float(
            current_price
        )

    # =====================================================
    # ORDER TYPE
    # =====================================================

    (
        order_type,
        is_pending,
    ) = _determine_order_type(
        bias=smc.bias,
        entry_price=entry_price,
        current_price=current_price,
        has_zone=has_zone,
        fill_status=fill_status,
        m1_confirmation=m1_confirmation,
    )

    # =====================================================
    # WAIT
    # =====================================================

    if order_type == "WAIT":

        if fill_status == "partial":

            raise NoTradeSignal(
                f"{zone_type} masih partial fill. "
                "Menunggu harga menyelesaikan retracement "
                "atau memberikan rejection yang lebih jelas."
            )

        raise NoTradeSignal(
            f"{zone_type} sudah tersentuh tetapi "
            "belum memberikan M1 rejection yang cukup."
        )

    # =====================================================
    # SL / TP
    # =====================================================

    (
        sl,
        tp1,
        tp2,
        rr_tp1,
        rr_tp2,
    ) = _calculate_risk(
        bias=smc.bias,
        entry_price=entry_price,
    )

    # =====================================================
    # RR VALIDATION
    # =====================================================

    if not _validate_rr(
        rr_tp1,
        rr_tp2,
    ):

        raise NoTradeSignal(
            "Risk/Reward tidak memenuhi minimum. "
            f"TP1 RR={rr_tp1:.2f}, "
            f"TP2 RR={rr_tp2:.2f}"
        )

    # =====================================================
    # ENTRY DESCRIPTION
    # =====================================================

    entry_type = _build_entry_description(
        order_type=order_type,
        is_pending=is_pending,
        fill_status=fill_status,
        zone_type=zone_type,
        m1_confirmation=m1_confirmation,
    )

    # =====================================================
    # REASON
    # =====================================================

    reason_text = get_entry_reason(
        bias=smc.bias,
        zone_type=zone_type,
        is_pending=is_pending,
        fill_status=fill_status,
        seed=(
            f"{now.isoformat()}-"
            f"{zone_type}-"
            f"{smc.bias}-"
            f"{fill_status}"
        ),
    )

    smc.confluences.append(
        reason_text
    )

    # =====================================================
    # ZONE PRICE
    # =====================================================

    if (
        zone_low is not None
        and zone_high is not None
    ):

        smc.confluences.append(
            f"Area {zone_type}: "
            f"{round(zone_low, 2)} - "
            f"{round(zone_high, 2)}"
        )

    # =====================================================
    # ZONE STATUS
    # =====================================================

    if fill_status == "untouched":

        smc.confluences.append(
            "Zona masih fresh dan belum "
            "termitigasi oleh harga M1."
        )

    elif fill_status == "partial":

        smc.confluences.append(
            "FVG baru terisi sebagian; "
            "masih terdapat risiko harga "
            "kembali mengisi sisa imbalance."
        )

    elif fill_status == "full":

        smc.confluences.append(
            "Zona sudah mengalami mitigasi "
            "oleh pergerakan harga sebelumnya."
        )

    # =====================================================
    # M1 CONFIRMATION
    # =====================================================

    if m1_confirmation:

        if smc.bias == "bullish":

            smc.confluences.append(
                "M1 menunjukkan rejection bullish "
                "di sekitar zona entry."
            )

        else:

            smc.confluences.append(
                "M1 menunjukkan rejection bearish "
                "di sekitar zona entry."
            )

    elif is_pending:

        smc.confluences.append(
            "Harga belum kembali ke zona; "
            "pending order digunakan untuk menunggu retest."
        )

    # =====================================================
    # DISTANCE
    # =====================================================

    distance = _zone_distance(
        current_price,
        zone_low,
        zone_high,
    )

    smc.confluences.append(
        f"Jarak harga sekarang ke zona: "
        f"{round(distance, 2)} USD."
    )

    # =====================================================
    # ENTRY PRICE
    # =====================================================

    if is_pending:

        smc.confluences.append(
            f"Harga sekarang "
            f"{round(current_price, 2)}, "
            f"entry ditempatkan di zona "
            f"{round(entry_price, 2)}."
        )

    else:

        smc.confluences.append(
            f"Entry market mengikuti harga "
            f"terakhir {round(current_price, 2)}."
        )

    # =====================================================
    # RR
    # =====================================================

    smc.confluences.append(
        f"Risk/Reward TP1 = 1:{rr_tp1:.2f}, "
        f"TP2 = 1:{rr_tp2:.2f}."
    )

    # =====================================================
    # FVG WARNING
    # =====================================================

    if (
        zone_type == "Fair Value Gap"
        and fill_status == "partial"
    ):

        smc.confluences.append(
            "⚠️ FVG belum sepenuhnya tertutup. "
            "Masih ada kemungkinan retracement "
            "ke sisa gap."
        )

    # =====================================================
    # SESSION
    # =====================================================

    session_name, session_note = (
        _get_session_info(
            now
        )
    )

    extra_note = (
        get_session_extra_note(
            session_name=session_name,
            seed=(
                f"{now.isoformat()}-"
                f"{session_name}"
            ),
        )
    )

    if extra_note:

        session_note = (
            f"{session_note}. "
            f"{extra_note}"
        )

    # =====================================================
    # PROBABILITY
    # =====================================================

    probability = (
        _calculate_probability(
            smc_score=smc.score,
            zone_type=zone_type,
            fill_status=fill_status,
            is_pending=is_pending,
            m1_confirmation=m1_confirmation,
        )
    )

    # =====================================================
    # RETURN
    # =====================================================

    return TradeSignal(

        timestamp=now,

        bias=smc.bias,

        entry_price=round(
            entry_price,
            2,
        ),

        entry_type=entry_type,

        order_type=order_type,

        is_pending=is_pending,

        sl=round(
            sl,
            2,
        ),

        tp1=round(
            tp1,
            2,
        ),

        tp2=round(
            tp2,
            2,
        ),

        probability=probability,

        reasons=smc.confluences,

        smc=smc,

        session_name=session_name,

        session_note=session_note,

        zone_touched=(
            fill_status != "untouched"
        ),

        zone_type=zone_type,

        fill_status=fill_status,

        zone_low=(
            round(zone_low, 2)
            if zone_low is not None
            else None
        ),

        zone_high=(
            round(zone_high, 2)
            if zone_high is not None
            else None
        ),

        m1_confirmation=m1_confirmation,

        rr_tp1=round(
            rr_tp1,
            2,
        ),

        rr_tp2=round(
            rr_tp2,
            2,
        ),
    )


# =========================================================
# FORMAT SIGNAL
# =========================================================

def format_signal_message(
    sig: TradeSignal,
) -> str:

    arrow = (
        "🟢 BUY"
        if sig.bias == "bullish"
        else "🔴 SELL"
    )

    time_str = sig.timestamp.strftime(
        "%d %b %Y, %H:%M WIB"
    )

    entry_label = (
        f"🎯 Entry ({sig.order_type})"
    )

    lines = [

        "📊 *XAU AI INTELLIGENCE*",

        f"_Signal H1 — {time_str}_",

        f"_Sesi {sig.session_name}_",

        "",

        f"{arrow}  XAUUSD",

        f"Tipe entry : {sig.entry_type}",

        "",

        (
            f"{entry_label} : "
            f"`{sig.entry_price:.2f}`"
        ),

        (
            f"🛑 SL     : "
            f"`{sig.sl:.2f}` "
            f"(-{SL_PIPS} pip)"
        ),

        (
            f"✅ TP1    : "
            f"`{sig.tp1:.2f}` "
            f"(+{TP1_PIPS} pip)"
        ),

        (
            f"✅ TP2    : "
            f"`{sig.tp2:.2f}` "
            f"(+{TP2_PIPS} pip)"
        ),

        "",

        (
            f"📐 RR      : "
            f"TP1 1:{sig.rr_tp1:.2f} | "
            f"TP2 1:{sig.rr_tp2:.2f}"
        ),

        (
            f"📈 Probabilitas: "
            f"*{sig.probability}%*"
        ),

        "",

        (
            f"📍 Zona: "
            f"{sig.zone_type or '-'}"
        ),

    ]

    if (
        sig.zone_low is not None
        and sig.zone_high is not None
    ):

        lines.append(
            (
                f"📏 Area: "
                f"`{sig.zone_low:.2f} - "
                f"{sig.zone_high:.2f}`"
            )
        )

    lines += [

        (
            f"🧩 Status zona: "
            f"{sig.fill_status}"
        ),

        (
            f"🔎 M1 Confirmation: "
            f"{'YES' if sig.m1_confirmation else 'NO'}"
        ),

        "",

        f"🕐 Catatan sesi {sig.session_name}:",

        _wrap_reason(
            sig.session_note
        ),

        "",

        "🧠 Alasan entry:",
    ]

    for i, reason in enumerate(
        sig.reasons,
        1,
    ):

        lines.append(
            _wrap_reason(
                f"{i}. {reason}"
            )
        )

    # =====================================================
    # PENDING
    # =====================================================

    if sig.is_pending:

        lines += [

            "",

            _wrap_reason(
                f"⏳ Pasang {sig.order_type} "
                f"di harga entry di atas."
            ),

            _wrap_reason(
                f"Jika dalam "
                f"{PENDING_ORDER_TIMEOUT_MINUTES} menit "
                f"belum tersentuh, signal dianggap "
                f"batal dan tidak perlu entry lagi."
            ),

        ]

    # =====================================================
    # FOOTER
    # =====================================================

    lines += [

        "",

        "⚠️ _Signal berbasis AI (SMC), bukan jaminan profit._",

        "_Selalu gunakan money management pribadi._",

        "",

        "🤖 _Signal ini dihasilkan oleh AI Agent Gold_",

    ]

    return "\n".join(
        lines
    )


# =========================================================
# WRAP TEXT
# =========================================================

def _wrap_reason(
    text: str,
    width: int = 34,
) -> str:

    words = text.split(
        " "
    )

    lines = []

    current = ""

    for word in words:

        if (
            len(current)
            + len(word)
            + 1
            > width
        ):

            if current:

                lines.append(
                    current
                )

            current = word

        else:

            current = (
                f"{current} {word}"
            ).strip()

    if current:

        lines.append(
            current
        )

    return "\n   ".join(
        lines
    )


# =========================================================
# DEBUG
# =========================================================

def debug_signal(
    sig: TradeSignal,
) -> str:

    return (
        "\n"
        "==============================\n"
        "XAU AI SIGNAL DEBUG\n"
        "==============================\n"
        f"Bias          : {sig.bias}\n"
        f"Entry         : {sig.entry_price}\n"
        f"Order         : {sig.order_type}\n"
        f"Pending       : {sig.is_pending}\n"
        f"Zone          : {sig.zone_type}\n"
        f"Zone Low      : {sig.zone_low}\n"
        f"Zone High     : {sig.zone_high}\n"
        f"Fill Status   : {sig.fill_status}\n"
        f"M1 Confirm    : {sig.m1_confirmation}\n"
        f"SL            : {sig.sl}\n"
        f"TP1           : {sig.tp1}\n"
        f"TP2           : {sig.tp2}\n"
        f"RR TP1        : {sig.rr_tp1}\n"
        f"RR TP2        : {sig.rr_tp2}\n"
        f"Probability   : {sig.probability}%\n"
        f"Session       : {sig.session_name}\n"
        "==============================\n"
    )

"""
services/signal_builder.py

XAU AI SIGNAL ENGINE
====================

M5  = STRUCTURE
M1  = ENTRY TIMING

Fitur:
- M5 closed candle untuk SMC utama
- BOS / CHoCH
- Swing
- Liquidity sweep
- Order Block
- Fair Value Gap
- M1 sebagai entry timing
- M1 rejection confirmation
- M1 zone diprioritaskan
- M5 zone sebagai fallback
- Radius zona maksimum 100 pip
- Buy Limit / Sell Limit
- Market Buy / Market Sell
- Tidak menggunakan Buy Stop / Sell Stop
- SL / TP dihitung dari ENTRY PRICE
- RR validation
- Probability
- Entry reason bank
- Session note bank
- Pending timeout
- Compatible dengan scheduler dan /signal
"""

# =========================================================
# IMPORT
# =========================================================

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo


# =========================================================
# LOCAL SERVICES
# =========================================================

from .twelvedata_client import (
    Candle,
    fetch_candles,
)

from .smc_analyzer import (
    analyze,
    SMCResult,
)

from .entry_reason_bank import (
    get_entry_reason,
    get_session_extra_note,
)


# =========================================================
# CONFIG
# =========================================================

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
    SMC_PIP_VALUE,
)


# =========================================================
# OPTIONAL CONFIG
# =========================================================

try:
    from config import MAX_ZONE_DISTANCE
except ImportError:
    MAX_ZONE_DISTANCE = 100 * SMC_PIP_VALUE


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


try:
    from config import MIN_SMC_SCORE
except ImportError:
    MIN_SMC_SCORE = 50


# =========================================================
# ZONE CONFIG
# =========================================================

MAX_ZONE_DISTANCE_PIPS = 100

MAX_ZONE_DISTANCE_PRICE = (
    MAX_ZONE_DISTANCE_PIPS
    * SMC_PIP_VALUE
)


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

    zone_timeframe: str = "M5"

    pending_timeout_minutes: int = (
        PENDING_ORDER_TIMEOUT_MINUTES
    )


# =========================================================
# EXCEPTION
# =========================================================

class NoTradeSignal(Exception):
    pass


# =========================================================
# TIMEZONE HELPER
# =========================================================

def _to_wib(dt: datetime) -> datetime:

    if dt.tzinfo is None:
        return dt.replace(tzinfo=WIB)

    return dt.astimezone(WIB)


# =========================================================
# SESSION
# =========================================================

def _get_session_info(
    dt: datetime,
) -> Tuple[str, str]:

    dt = _to_wib(dt)

    hour = dt.hour

    for session in SESSIONS:

        if hour in session["hours"]:

            return (
                session["name"],
                session["note"],
            )

    return (
        "Trading",
        "Pantau pergerakan harga dengan disiplin "
        "dan manajemen risiko.",
    )


# =========================================================
# CURRENT M5 OPEN
# =========================================================

def _get_current_m5_open_time(
    now: datetime,
) -> datetime:

    now = _to_wib(now)

    minute = (
        now.minute // 5
    ) * 5

    return now.replace(
        minute=minute,
        second=0,
        microsecond=0,
    )


# =========================================================
# GET CLOSED M5
# =========================================================

def _get_closed_m5_candles(
    candles: List[Candle],
    count: int,
) -> List[Candle]:

    if count <= 0:

        raise ValueError(
            "Jumlah candle closed harus lebih besar dari 0."
        )

    now = datetime.now(WIB)

    current_open = (
        _get_current_m5_open_time(now)
    )

    closed = []

    for candle in candles:

        candle_time = _to_wib(
            candle.time
        )

        if candle_time < current_open:

            closed.append(candle)

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
# GET CLOSED M1
# =========================================================

def _get_closed_m1_candles(
    candles: List[Candle],
    count: int,
) -> List[Candle]:

    if not candles:
        return []

    now = datetime.now(WIB)

    current_minute = now.replace(
        second=0,
        microsecond=0,
    )

    closed = []

    for candle in candles:

        candle_time = _to_wib(
            candle.time
        )

        if candle_time < current_minute:

            closed.append(candle)

    closed.sort(
        key=lambda c: _to_wib(c.time)
    )

    return closed[-count:]


# =========================================================
# CANDLE OVERLAP
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
# FVG STATUS
# =========================================================

def _fvg_fill_status(
    direction: str,
    top: float,
    bottom: float,
    recent_candles: List[Candle],
) -> str:

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

        if any(
            candle.close < bottom
            for candle in recent_candles
        ):
            return "full"

    elif direction == "bearish":

        if any(
            candle.close > top
            for candle in recent_candles
        ):
            return "full"

    return "partial"


# =========================================================
# PIPS
# =========================================================

def _price_to_pips(
    price_distance: float,
) -> float:

    if SMC_PIP_VALUE <= 0:
        return 0.0

    return (
        abs(price_distance)
        / SMC_PIP_VALUE
    )


def _pips_to_price(
    pips: float,
) -> float:

    return (
        float(pips)
        * SMC_PIP_VALUE
    )


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

        return (
            zone_low
            - current_price
        )

    return (
        current_price
        - zone_high
    )


def _zone_distance_pips(
    current_price: float,
    zone_low: float,
    zone_high: float,
) -> float:

    return _price_to_pips(
        _zone_distance(
            current_price,
            zone_low,
            zone_high,
        )
    )


# =========================================================
# BULLISH REJECTION
# =========================================================

def _bullish_rejection(
    candles: List[Candle],
    zone_low: float,
    zone_high: float,
) -> bool:

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
            candle.close - candle.low
        ) / candle_range

        lower_wick = (
            min(candle.open, candle.close)
            - candle.low
        )

        body = abs(
            candle.close
            - candle.open
        )

        # Candle harus bullish
        if not candle.is_bullish:
            continue

        # Close harus relatif kuat
        if close_strength < 0.55:
            continue

        # Minimal ada rejection body/wick
        if lower_wick >= body * 0.5:

            return True

    return False


# =========================================================
# BEARISH REJECTION
# =========================================================

def _bearish_rejection(
    candles: List[Candle],
    zone_low: float,
    zone_high: float,
) -> bool:

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

        upper_wick = (
            candle.high
            - max(candle.open, candle.close)
        )

        body = abs(
            candle.close
            - candle.open
        )

        if not candle.is_bearish:
            continue

        if close_strength < 0.55:
            continue

        if upper_wick >= body * 0.5:

            return True

    return False


# =========================================================
# M1 CONFIRMATION
# =========================================================

def _has_m1_rejection(
    bias: str,
    zone_low: float,
    zone_high: float,
    recent_candles: List[Candle],
) -> bool:

    if not recent_candles:
        return False

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

    if bias == "bearish":

        return _bearish_rejection(
            check_candles,
            zone_low,
            zone_high,
        )

    return False


# =========================================================
# ZONE MATCH BIAS
# =========================================================

def _zone_matches_bias(
    bias: str,
    current_price: float,
    zone_low: float,
    zone_high: float,
) -> bool:

    if bias == "bullish":

        # Buy zone idealnya berada di bawah harga
        return zone_low <= current_price

    if bias == "bearish":

        # Sell zone idealnya berada di atas harga
        return zone_high >= current_price

    return False


# =========================================================
# COLLECT ZONES
# =========================================================

def _collect_zones(
    smc: SMCResult,
    current_price: float,
    recent_candles: List[Candle],
    timeframe: str,
    max_distance_price: float,
):

    candidates = []

    # =====================================================
    # ORDER BLOCK
    # =====================================================

    for ob in getattr(
        smc,
        "order_blocks",
        [],
    ):

        zone_low = float(
            min(
                ob.low,
                ob.high,
            )
        )

        zone_high = float(
            max(
                ob.low,
                ob.high,
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
            max_distance_price is not None
            and distance > max_distance_price
        ):
            continue

        if not _zone_matches_bias(
            smc.bias,
            current_price,
            zone_low,
            zone_high,
        ):
            continue

        touched = _zone_touched_by_recent_price(
            zone_low,
            zone_high,
            recent_candles,
        )

        status = (
            "full"
            if touched
            else "untouched"
        )

        candidates.append(
            {
                "distance": distance,
                "distance_pips": _price_to_pips(
                    distance
                ),
                "price": mid,
                "type": "Order Block",
                "status": status,
                "low": zone_low,
                "high": zone_high,
                "timeframe": timeframe,
                "index": getattr(
                    ob,
                    "index",
                    -1,
                ),
            }
        )

    # =====================================================
    # FVG
    # =====================================================

    for fvg in getattr(
        smc,
        "fvgs",
        [],
    ):

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
            max_distance_price is not None
            and distance > max_distance_price
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
                "distance_pips": _price_to_pips(
                    distance
                ),
                "price": mid,
                "type": "Fair Value Gap",
                "status": status,
                "low": zone_low,
                "high": zone_high,
                "timeframe": timeframe,
                "index": getattr(
                    fvg,
                    "index",
                    -1,
                ),
            }
        )

    return candidates


# =========================================================
# FIND ENTRY ZONE
# =========================================================

def _find_entry_zone(
    smc: SMCResult,
    current_price: float,
    recent_candles: List[Candle],
    timeframe: str,
    max_distance_price: float,
):

    candidates = _collect_zones(
        smc=smc,
        current_price=current_price,
        recent_candles=recent_candles,
        timeframe=timeframe,
        max_distance_price=max_distance_price,
    )

    if not candidates:
        return None

    # =====================================================
    # PRIORITY
    #
    # Fresh > Partial > Full
    #
    # OB lebih diprioritaskan daripada FVG
    # jika status dan jaraknya sama.
    # =====================================================

    status_priority = {
        "untouched": 0,
        "partial": 1,
        "full": 2,
    }

    type_priority = {
        "Order Block": 0,
        "Fair Value Gap": 1,
    }

    candidates.sort(
        key=lambda x: (
            status_priority.get(
                x["status"],
                99,
            ),
            type_priority.get(
                x["type"],
                99,
            ),
            x["distance"],
            -x.get("index", -1),
        )
    )

    return candidates[0]


# =========================================================
# BEST ENTRY ZONE M1 + M5
# =========================================================

def _find_best_entry_zone(
    m5_smc: SMCResult,
    m1_smc: Optional[SMCResult],
    current_price: float,
    m5_candles: List[Candle],
    m1_candles: List[Candle],
):

    # =====================================================
    # M1 FIRST
    # =====================================================

    if m1_smc is not None:

        m1_zone = _find_entry_zone(
            smc=m1_smc,
            current_price=current_price,
            recent_candles=m1_candles,
            timeframe="M1",
            max_distance_price=(
                MAX_ZONE_DISTANCE_PRICE
            ),
        )

        if m1_zone is not None:

            return (
                m1_zone,
                m1_smc,
            )

    # =====================================================
    # FALLBACK M5
    # =====================================================

    m5_zone = _find_entry_zone(
        smc=m5_smc,
        current_price=current_price,
        recent_candles=m5_candles,
        timeframe="M5",
        max_distance_price=(
            MAX_ZONE_DISTANCE_PRICE
        ),
    )

    if m5_zone is not None:

        return (
            m5_zone,
            m5_smc,
        )

    return (
        None,
        m5_smc,
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
    zone_timeframe: str,
) -> str:

    if is_pending:

        return (
            f"Pending {order_type} "
            f"(menunggu retest {zone_timeframe})"
        )

    if (
        zone_type == "Fair Value Gap"
        and fill_status == "partial"
    ):

        return (
            f"Market {zone_timeframe} "
            "(FVG partial fill)"
        )

    if fill_status == "full":

        if m1_confirmation:

            return (
                f"Market {zone_timeframe} "
                "(zona diretest + M1 rejection)"
            )

        return (
            f"Market {zone_timeframe} "
            "(zona sudah termitigasi)"
        )

    if m1_confirmation:

        return (
            f"Market {zone_timeframe} "
            "(M1 rejection confirmation)"
        )

    return (
        f"Market {zone_timeframe} "
        "(zona valid)"
    )


# =========================================================
# RISK
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

    elif bias == "bearish":

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

    else:

        raise ValueError(
            f"Bias tidak valid: {bias}"
        )

    risk = abs(
        entry_price
        - sl
    )

    reward_tp1 = abs(
        tp1
        - entry_price
    )

    reward_tp2 = abs(
        tp2
        - entry_price
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
# RR VALIDATION
# =========================================================

def _validate_rr(
    rr_tp1: float,
    rr_tp2: float,
) -> bool:

    return (
        rr_tp1 >= MIN_RR_TP1
        and rr_tp2 >= MIN_RR_TP2
    )


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
    # PARTIAL
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
    # FULL
    # =====================================================

    if fill_status == "full":

        if (
            REQUIRE_M1_REJECTION
            and not m1_confirmation
        ):

            return (
                "WAIT",
                False,
            )

        return (
            "Market",
            False,
        )

    # =====================================================
    # FRESH
    # =====================================================

    if fill_status == "untouched":

        if bias == "bullish":

            if entry_price < current_price:

                return (
                    "Buy Limit",
                    True,
                )

            if abs(
                entry_price
                - current_price
            ) <= MARKET_ENTRY_TOLERANCE:

                if (
                    REQUIRE_M1_REJECTION
                    and not m1_confirmation
                ):

                    return (
                        "WAIT",
                        False,
                    )

                return (
                    "Market",
                    False,
                )

        elif bias == "bearish":

            if entry_price > current_price:

                return (
                    "Sell Limit",
                    True,
                )

            if abs(
                entry_price
                - current_price
            ) <= MARKET_ENTRY_TOLERANCE:

                if (
                    REQUIRE_M1_REJECTION
                    and not m1_confirmation
                ):

                    return (
                        "WAIT",
                        False,
                    )

                return (
                    "Market",
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
    zone_timeframe: str,
    structure_event: Optional[str] = None,
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

    # Zone
    if zone_type:
        score += 3

    # M1 confirmation
    if m1_confirmation:
        score += 7

    # Fresh
    if fill_status == "untouched":
        score += 3

    # Partial
    elif fill_status == "partial":
        score -= 8

    # Full
    elif fill_status == "full":
        score += 1

    # Pending
    if is_pending:
        score -= 1

    # M1 timing
    if zone_timeframe == "M1":
        score += 2

    # BOS
    if structure_event == "BOS":
        score += 3

    # CHoCH
    elif structure_event == "CHoCH":
        score += 1

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
# EDUCATIONAL REASON
# =========================================================

def _build_educational_reason(
    bias: str,
    zone_type: str,
    zone_timeframe: str,
    fill_status: str,
    m1_confirmation: bool,
    is_pending: bool,
) -> str:

    direction = (
        "buyer"
        if bias == "bullish"
        else "seller"
    )

    if zone_type == "Order Block":

        if fill_status == "untouched":

            return (
                f"Pelajaran entry: Order Block "
                f"{zone_timeframe} yang masih fresh "
                f"lebih baik diperlakukan sebagai area "
                f"menunggu retracement, bukan mengejar harga. "
                f"Untuk setup ini, {direction} menjadi pihak "
                f"yang sedang dipantau."
            )

        if m1_confirmation:

            return (
                f"Pelajaran entry: setelah Order Block "
                f"{zone_timeframe} diretest, rejection M1 "
                f"memberikan bukti bahwa area tersebut "
                f"masih mendapatkan respons. Konfirmasi "
                f"lebih penting daripada sekadar menyentuh zona."
            )

        return (
            f"Pelajaran entry: Order Block {zone_timeframe} "
            f"sudah mengalami mitigasi. Karena itu entry "
            f"tidak boleh hanya berdasarkan asumsi bahwa "
            f"zona akan kembali menahan harga."
        )

    if zone_type == "Fair Value Gap":

        if fill_status == "untouched":

            return (
                f"Pelajaran entry: FVG {zone_timeframe} "
                f"menunjukkan adanya imbalance. Harga dapat "
                f"melakukan retracement ke area tersebut, "
                f"sehingga pending entry lebih terukur "
                f"daripada mengejar candle."
            )

        if fill_status == "partial":

            return (
                f"Pelajaran entry: FVG {zone_timeframe} "
                f"baru terisi sebagian. Partial fill belum "
                f"cukup untuk menyimpulkan bahwa imbalance "
                f"akan langsung menjadi support/resistance. "
                f"Karena itu perlu menunggu konfirmasi."
            )

        if m1_confirmation:

            return (
                f"Pelajaran entry: FVG {zone_timeframe} "
                f"telah diretest dan rejection M1 memberikan "
                f"konfirmasi tambahan. Tetap perhatikan "
                f"apakah harga mampu mempertahankan area tersebut."
            )

        return (
            f"Pelajaran entry: FVG {zone_timeframe} "
            f"telah termitigasi. Jangan menganggap setiap "
            f"FVG yang disentuh otomatis menjadi entry."
        )

    if is_pending:

        return (
            f"Pelajaran entry: zona {zone_timeframe} "
            f"digunakan sebagai area tunggu. Pending entry "
            f"membantu menghindari entry impulsif ketika "
            f"harga belum kembali ke area SMC."
        )

    return (
        f"Pelajaran entry: keputusan dibuat berdasarkan "
        f"struktur {zone_timeframe}, lokasi zona, dan "
        f"konfirmasi price action, bukan hanya arah candle terakhir."
    )


# =========================================================
# GENERATE SIGNAL
# =========================================================

def generate_signal(
    structure_candle_count: Optional[int] = None,
) -> TradeSignal:

    now = datetime.now(WIB)

    # =====================================================
    # M5 OUTPUT SIZE
    # =====================================================

    if structure_candle_count is None:

        m5_outputsize = max(
            CANDLES_LOOKBACK,
            CANDLES_FOR_STRUCTURE + 8,
        )

    else:

        m5_outputsize = max(
            structure_candle_count + 8,
            20,
        )

    # =====================================================
    # FETCH M5
    # =====================================================

    structure_raw = fetch_candles(
        interval=TF_STRUCTURE,
        outputsize=m5_outputsize,
    )

    if not structure_raw:

        raise ValueError(
            "Twelve Data tidak mengembalikan candle M5."
        )

    # =====================================================
    # CLOSED M5
    # =====================================================

    requested_count = (
        structure_candle_count
        if structure_candle_count is not None
        else CANDLES_FOR_STRUCTURE
    )

    structure_candles = (
        _get_closed_m5_candles(
            structure_raw,
            requested_count,
        )
    )

    if structure_candle_count is not None:

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

    if len(structure_candles) < CANDLES_FOR_STRUCTURE:

        raise ValueError(
            "Data M5 closed tidak cukup untuk analisa. "
            f"Minimal {CANDLES_FOR_STRUCTURE} candle."
        )

    # =====================================================
    # M5 SMC
    # =====================================================

    m5_smc = analyze(
        structure_candles
    )

    if m5_smc.bias not in (
        "bullish",
        "bearish",
    ):

        raise NoTradeSignal(
            "Bias SMC M5 tidak valid."
        )

    # =====================================================
    # MINIMUM SMC SCORE
    # =====================================================

    if m5_smc.score < MIN_SMC_SCORE:

        raise NoTradeSignal(
            "Score SMC M5 terlalu rendah. "
            f"Score={m5_smc.score}, "
            f"minimum={MIN_SMC_SCORE}."
        )

    # =====================================================
    # M1 DATA
    # =====================================================

    entry_raw = fetch_candles(
        interval=TF_ENTRY,
        outputsize=CANDLES_ENTRY_LOOKBACK,
    )

    if not entry_raw:

        raise ValueError(
            "Data candle M1 tidak tersedia."
        )

    entry_candles = (
        _get_closed_m1_candles(
            entry_raw,
            CANDLES_ENTRY_LOOKBACK,
        )
    )

    if not entry_candles:

        raise NoTradeSignal(
            "Tidak tersedia candle M1 CLOSED."
        )

    # =====================================================
    # CURRENT PRICE
    # =====================================================

    current_price = float(
        entry_candles[-1].close
    )

    if current_price <= 0:

        raise NoTradeSignal(
            "Harga XAUUSD tidak valid."
        )

    # =====================================================
    # RECENT M5
    # =====================================================

    recent_m5 = (
        structure_candles[-10:]
        if len(structure_candles) >= 10
        else structure_candles
    )

    # =====================================================
    # RECENT M1
    # =====================================================

    recent_m1 = (
        entry_candles[-10:]
        if len(entry_candles) >= 10
        else entry_candles
    )

    # =====================================================
    # M1 SMC
    # =====================================================

    m1_smc = None

    try:

        if len(entry_candles) >= 12:

            temp_m1_smc = analyze(
                entry_candles
            )

            # M1 hanya valid bila searah M5.
            if (
                temp_m1_smc.bias
                == m5_smc.bias
            ):

                m1_smc = temp_m1_smc

    except Exception as exc:

        print(
            "[M1 SMC] Analyzer gagal, "
            f"fallback M5: {exc}"
        )

        m1_smc = None

    # =====================================================
    # FIND BEST ZONE
    # =====================================================

    (
        selected_zone,
        selected_smc,
    ) = _find_best_entry_zone(
        m5_smc=m5_smc,
        m1_smc=m1_smc,
        current_price=current_price,
        m5_candles=recent_m5,
        m1_candles=recent_m1,
    )

    if selected_zone is None:

        raise NoTradeSignal(
            "Tidak ditemukan OB/FVG valid "
            f"dalam radius "
            f"{MAX_ZONE_DISTANCE_PIPS} pip "
            "dari harga sekarang."
        )

    # =====================================================
    # ZONE
    # =====================================================

    zone_price = float(
        selected_zone["price"]
    )

    zone_type = selected_zone["type"]

    fill_status = selected_zone["status"]

    zone_low = float(
        selected_zone["low"]
    )

    zone_high = float(
        selected_zone["high"]
    )

    zone_timeframe = selected_zone[
        "timeframe"
    ]

    # =====================================================
    # EXTRA ZONE VALIDATION
    # =====================================================

    zone_distance_pips = _zone_distance_pips(
        current_price,
        zone_low,
        zone_high,
    )

    if (
        zone_distance_pips
        > MAX_ZONE_DISTANCE_PIPS
    ):

        raise NoTradeSignal(
            "Zona terlalu jauh dari harga."
        )

    # =====================================================
    # M1 CONFIRMATION
    #
    # M1 selalu digunakan untuk timing.
    # =====================================================

    m1_confirmation = _has_m1_rejection(
        bias=m5_smc.bias,
        zone_low=zone_low,
        zone_high=zone_high,
        recent_candles=recent_m1,
    )

    # =====================================================
    # ENTRY PRICE
    # =====================================================

    if fill_status == "untouched":

        entry_price = zone_price

    else:

        entry_price = current_price

    # =====================================================
    # ENTRY PRICE SANITY
    # =====================================================

    if entry_price <= 0:

        raise NoTradeSignal(
            "Entry price tidak valid."
        )

    # =====================================================
    # ORDER TYPE
    # =====================================================

    (
        order_type,
        is_pending,
    ) = _determine_order_type(
        bias=m5_smc.bias,
        entry_price=entry_price,
        current_price=current_price,
        has_zone=True,
        fill_status=fill_status,
        m1_confirmation=m1_confirmation,
    )

    # =====================================================
    # WAIT
    # =====================================================

    if order_type == "WAIT":

        if fill_status == "partial":

            raise NoTradeSignal(
                f"{zone_type} {zone_timeframe} "
                "masih partial fill. "
                "Menunggu retracement atau rejection "
                "yang lebih jelas."
            )

        raise NoTradeSignal(
            f"{zone_type} {zone_timeframe} "
            "sudah tersentuh tetapi belum memberikan "
            "M1 rejection yang cukup."
        )

    # =====================================================
    # RISK
    # =====================================================

    (
        sl,
        tp1,
        tp2,
        rr_tp1,
        rr_tp2,
    ) = _calculate_risk(
        bias=m5_smc.bias,
        entry_price=entry_price,
    )

    # =====================================================
    # RR
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
        zone_timeframe=zone_timeframe,
    )

    # =====================================================
    # ENTRY REASON BANK
    # =====================================================

    reason_text = get_entry_reason(
        bias=m5_smc.bias,
        zone_type=zone_type,
        is_pending=is_pending,
        fill_status=fill_status,
        seed=(
            f"{now.isoformat()}-"
            f"{zone_type}-"
            f"{zone_timeframe}-"
            f"{m5_smc.bias}-"
            f"{fill_status}"
        ),
    )

    # =====================================================
    # REASONS
    # =====================================================

    reasons = []

    # =====================================================
    # SMC CONFLUENCES
    # =====================================================

    for reason in getattr(
        selected_smc,
        "confluences",
        [],
    ):

        if reason:

            reasons.append(
                str(reason)
            )

    # =====================================================
    # ENTRY REASON
    # =====================================================

    reasons.append(
        reason_text
    )

    # =====================================================
    # ZONE
    # =====================================================

    reasons.append(
        f"Area {zone_type} {zone_timeframe}: "
        f"{round(zone_low, 2)} - "
        f"{round(zone_high, 2)}."
    )

    # =====================================================
    # STATUS
    # =====================================================

    if fill_status == "untouched":

        reasons.append(
            f"Zona {zone_timeframe} masih fresh "
            "dan belum termitigasi oleh harga."
        )

    elif fill_status == "partial":

        reasons.append(
            f"Zona {zone_timeframe} baru mengalami "
            "partial fill; masih ada risiko harga "
            "melanjutkan retracement."
        )

    elif fill_status == "full":

        reasons.append(
            f"Zona {zone_timeframe} sudah mengalami "
            "mitigasi oleh pergerakan harga sebelumnya."
        )

    # =====================================================
    # M1 CONFIRMATION
    # =====================================================

    if m1_confirmation:

        if m5_smc.bias == "bullish":

            reasons.append(
                "M1 menunjukkan rejection bullish "
                "di sekitar zona entry."
            )

        else:

            reasons.append(
                "M1 menunjukkan rejection bearish "
                "di sekitar zona entry."
            )

    elif is_pending:

        reasons.append(
            "Harga belum kembali memberikan retest "
            "ke zona; pending order digunakan untuk "
            "menunggu harga datang ke area yang sudah dianalisa."
        )

    # =====================================================
    # DISTANCE
    # =====================================================

    reasons.append(
        f"Jarak harga sekarang ke zona sekitar "
        f"{round(zone_distance_pips, 1)} pip."
    )

    # =====================================================
    # ENTRY
    # =====================================================

    if is_pending:

        reasons.append(
            f"Harga sekarang {round(current_price, 2)}, "
            f"sedangkan entry ditempatkan di area "
            f"{round(entry_price, 2)}."
        )

    else:

        reasons.append(
            f"Entry market mengikuti harga terakhir "
            f"{round(current_price, 2)} setelah zona "
            "memberikan kondisi entry yang sesuai."
        )

    # =====================================================
    # TIMEFRAME
    # =====================================================

    if zone_timeframe == "M1":

        reasons.append(
            "Zona entry berasal dari M1, sehingga "
            "timing entry mengikuti struktur mikro "
            "dan price action M1."
        )

    else:

        reasons.append(
            "Zona entry berasal dari M5, sehingga "
            "M5 menjadi acuan utama area entry dan "
            "M1 digunakan untuk mencari timing konfirmasi."
        )

    # =====================================================
    # EDUCATION
    # =====================================================

    reasons.append(
        _build_educational_reason(
            bias=m5_smc.bias,
            zone_type=zone_type,
            zone_timeframe=zone_timeframe,
            fill_status=fill_status,
            m1_confirmation=m1_confirmation,
            is_pending=is_pending,
        )
    )

    # =====================================================
    # RR NOTE
    # =====================================================

    reasons.append(
        f"Risk/Reward TP1 = 1:{rr_tp1:.2f}, "
        f"TP2 = 1:{rr_tp2:.2f}."
    )

    # =====================================================
    # SESSION
    # =====================================================

    (
        session_name,
        session_note,
    ) = _get_session_info(now)

    extra_note = get_session_extra_note(
        session_name=session_name,
        seed=(
            f"{now.isoformat()}-"
            f"{session_name}"
        ),
    )

    if extra_note:

        session_note = (
            f"{session_note} "
            f"{extra_note}"
        )

    # =====================================================
    # PROBABILITY
    # =====================================================

    probability = _calculate_probability(
        smc_score=m5_smc.score,
        zone_type=zone_type,
        fill_status=fill_status,
        is_pending=is_pending,
        m1_confirmation=m1_confirmation,
        zone_timeframe=zone_timeframe,
        structure_event=m5_smc.structure_event,
    )

    # =====================================================
    # RETURN
    # =====================================================

    return TradeSignal(

        timestamp=now,

        bias=m5_smc.bias,

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

        reasons=reasons,

        smc=selected_smc,

        session_name=session_name,

        session_note=session_note,

        zone_touched=(
            fill_status != "untouched"
        ),

        zone_type=zone_type,

        fill_status=fill_status,

        zone_low=round(
            zone_low,
            2,
        ),

        zone_high=round(
            zone_high,
            2,
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

        zone_timeframe=zone_timeframe,

        pending_timeout_minutes=(
            PENDING_ORDER_TIMEOUT_MINUTES
        ),
    )


# =========================================================
# BUILD SIGNAL COMPATIBILITY
# =========================================================

def build_signal(
    structure_candle_count: Optional[int] = None,
) -> TradeSignal:

    return generate_signal(
        structure_candle_count=structure_candle_count
    )


# =========================================================
# PRICE DISPLAY
# =========================================================

def _price_display(
    price,
) -> str:

    if price is None:
        return "-"

    try:

        return str(
            int(
                float(price)
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return "-"


# =========================================================
# TEXT WRAPPER
# =========================================================

def _wrap_reason(
    text: str,
    width: int = 34,
) -> str:

    words = str(text).split(" ")

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
        lines.append(current)

    return "\n   ".join(lines)


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

        f"_Signal SMC — {time_str}_",

        f"_Sesi {sig.session_name}_",

        "",

        f"{arrow}  XAUUSD",

        f"Tipe entry : {sig.entry_type}",

        "",

        # ENTRY
        (
            f"{entry_label} : "
            f"`{_price_display(sig.entry_price)}`"
        ),

        # TIMEFRAME
        (
            f"⏱ Timeframe zona : "
            f"*{sig.zone_timeframe}*"
        ),

        # SL
        (
            f"🛑 SL     : "
            f"`{_price_display(sig.sl)}` "
            f"(-{SL_PIPS} pip)"
        ),

        # TP1
        (
            f"✅ TP1    : "
            f"`{_price_display(sig.tp1)}` "
            f"(+{TP1_PIPS} pip)"
        ),

        # TP2
        (
            f"✅ TP2    : "
            f"`{_price_display(sig.tp2)}` "
            f"(+{TP2_PIPS} pip)"
        ),

        "",

        # RR
        (
            f"📐 RR      : "
            f"TP1 1:{sig.rr_tp1:.2f} | "
            f"TP2 1:{sig.rr_tp2:.2f}"
        ),

        # Probability
        (
            f"📈 Probabilitas: "
            f"*{sig.probability}%*"
        ),

        "",

        # Zone
        (
            f"📍 Zona: "
            f"{sig.zone_type or '-'} "
            f"({sig.zone_timeframe})"
        ),
    ]

    # =====================================================
    # ZONE AREA
    # =====================================================

    if (
        sig.zone_low is not None
        and sig.zone_high is not None
    ):

        lines.append(
            (
                f"📏 Area: "
                f"`{_price_display(sig.zone_low)} - "
                f"{_price_display(sig.zone_high)}`"
            )
        )

    # =====================================================
    # ZONE STATUS
    # =====================================================

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

        f"🕐 *Catatan sesi {sig.session_name}:*",

        _wrap_reason(
            sig.session_note
        ),

        "",

        "🧠 *Alasan & pembelajaran entry:*",
    ]

    # =====================================================
    # REASONS
    # =====================================================

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
                f"di area entry di atas."
            ),

            _wrap_reason(
                f"Jika dalam "
                f"{sig.pending_timeout_minutes} menit "
                "harga belum menyentuh entry, "
                "anggap signal EXPIRED dan "
                "SKIP signal tersebut."
            ),

            _wrap_reason(
                "Jangan mengejar harga setelah "
                "signal expired. Tunggu setup baru "
                "dari analisa berikutnya."
            ),
        ]

    else:

        lines += [

            "",

            _wrap_reason(
                "📌 Entry mengikuti kondisi zona "
                "yang sudah dikonfirmasi. "
                "Tetap hindari mengejar harga "
                "jika kondisi entry sudah berubah."
            ),
        ]

    # =====================================================
    # FOOTER
    # =====================================================

    lines += [

        "",

        "━━━━━━━━━━━━━━━━━━",

        (
            f"📏 Radius pencarian zona: "
            f"*{MAX_ZONE_DISTANCE_PIPS} pip*"
        ),

        (
            f"⏳ Pending timeout: "
            f"*{PENDING_ORDER_TIMEOUT_MINUTES} menit*"
        ),

        "",

        "⚠️ _Signal berbasis AI (SMC), bukan jaminan profit._",

        "_Selalu gunakan money management pribadi._",

        "",

        "🤖 _Signal ini dihasilkan oleh AI Agent Gold_",
    ]

    return "\n".join(lines)


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
        f"Zone TF       : {sig.zone_timeframe}\n"
        f"Zone Low      : {sig.zone_low}\n"
        f"Zone High     : {sig.zone_high}\n"
        f"Fill Status   : {sig.fill_status}\n"
        f"M1 Confirm    : {sig.m1_confirmation}\n"
        f"SL            : {sig.sl}\n"
        f"TP1           : {sig.tp1}\n"
        f"TP2           : {sig.tp2}\n"
        f"SL Pips       : {SL_PIPS}\n"
        f"TP1 Pips      : {TP1_PIPS}\n"
        f"TP2 Pips      : {TP2_PIPS}\n"
        f"RR TP1        : {sig.rr_tp1}\n"
        f"RR TP2        : {sig.rr_tp2}\n"
        f"Probability   : {sig.probability}%\n"
        f"Session       : {sig.session_name}\n"
        f"Radius        : {MAX_ZONE_DISTANCE_PIPS} pip\n"
        f"Timeout       : {sig.pending_timeout_minutes} min\n"
        "==============================\n"
    )

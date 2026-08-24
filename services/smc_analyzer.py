"""
services/smc_analyzer.py

XAU AI SMC ANALYZER
===================

Analisa Smart Money Concept untuk XAUUSD.

TIMEFRAME UTAMA
---------------
M5 digunakan sebagai timeframe struktur.

KONSEP
------
1. Swing High / Swing Low
2. BOS
3. CHoCH
4. Order Block
5. Fair Value Gap
6. Liquidity Sweep
7. Zone freshness
8. Zone mitigation
9. Struktur ranging / trending
10. Score / confluence

IMPORTANT
---------
File ini bertugas menganalisa struktur dan zona SMC.

Keputusan entry final dilakukan oleh:

    services.signal_builder

Signal builder kemudian menentukan:

    M1 zone -> prioritas entry
    M5 zone -> fallback
    Market / Pending
    SL / TP
    RR
    Probability
    Reason
    Session note
    Pending timeout

Tidak ada logika radius USD di file ini.
Radius zona dikontrol oleh settings.py.
"""


from dataclasses import dataclass, field
from typing import List, Optional, Literal


from .twelvedata_client import Candle


# =========================================================
# TYPES
# =========================================================

Direction = Literal[
    "bullish",
    "bearish",
]


# =========================================================
# SWING POINT
# =========================================================

@dataclass
class SwingPoint:

    index: int

    price: float

    # bullish = swing low
    # bearish = swing high
    kind: Direction


# =========================================================
# ORDER BLOCK
# =========================================================

@dataclass
class OrderBlock:

    index: int

    high: float

    low: float

    direction: Direction

    # =====================================================
    # TAMBAHAN
    # =====================================================

    strength: float = 0.0

    mitigated: bool = False

    fresh: bool = True

    source_timeframe: str = "M5"


# =========================================================
# FAIR VALUE GAP
# =========================================================

@dataclass
class FVG:

    index: int

    top: float

    bottom: float

    direction: Direction

    # =====================================================
    # TAMBAHAN
    # =====================================================

    strength: float = 0.0

    fill_status: str = "untouched"

    fresh: bool = True

    source_timeframe: str = "M5"


# =========================================================
# SMC RESULT
# =========================================================

@dataclass
class SMCResult:

    # =====================================================
    # STRUCTURE
    # =====================================================

    bias: Direction

    structure_event: str

    last_bos_price: Optional[float]

    # =====================================================
    # ZONES
    # =====================================================

    order_blocks: List[
        OrderBlock
    ] = field(
        default_factory=list
    )

    fvgs: List[
        FVG
    ] = field(
        default_factory=list
    )

    # =====================================================
    # LIQUIDITY
    # =====================================================

    liquidity_swept: bool = False

    # =====================================================
    # REASONS
    # =====================================================

    confluences: List[
        str
    ] = field(
        default_factory=list
    )

    # =====================================================
    # SCORE
    # =====================================================

    score: int = 0

    # =====================================================
    # EXTRA STRUCTURE INFO
    # =====================================================

    swing_high: Optional[float] = None

    swing_low: Optional[float] = None

    higher_high: bool = False

    higher_low: bool = False

    lower_high: bool = False

    lower_low: bool = False


# =========================================================
# SAFE CANDLE HELPERS
# =========================================================

def _safe_float(
    value,
    default: float = 0.0,
) -> float:

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return default


# =========================================================
# FIND SWING POINTS
# =========================================================

def find_swing_points(
    candles: List[Candle],
    left: int = 2,
    right: int = 2,
) -> List[SwingPoint]:

    """
    Fractal swing detection.

    Swing High:
        high candle lebih tinggi
        dibanding candle kiri/kanan.

    Swing Low:
        low candle lebih rendah
        dibanding candle kiri/kanan.

    Candle yang belum memiliki cukup
    candle kanan tidak dianggap swing
    agar struktur tidak menggunakan
    candle yang belum terkonfirmasi.
    """

    points = []

    if not candles:

        return points

    n = len(
        candles
    )

    if n < (
        left
        + right
        + 1
    ):

        return points

    for i in range(
        left,
        n - right,
    ):

        current = candles[i]

        window = candles[
            i - left:
            i + right + 1
        ]

        current_high = _safe_float(
            current.high
        )

        current_low = _safe_float(
            current.low
        )

        highs = [
            _safe_float(
                candle.high
            )
            for candle in window
        ]

        lows = [
            _safe_float(
                candle.low
            )
            for candle in window
        ]

        # =================================================
        # SWING HIGH
        # =================================================

        if current_high >= max(
            highs
        ):

            # Hindari duplikasi high
            duplicate = any(
                point.index == i
                and point.kind == "bearish"
                for point in points
            )

            if not duplicate:

                points.append(
                    SwingPoint(
                        index=i,
                        price=current_high,
                        kind="bearish",
                    )
                )

        # =================================================
        # SWING LOW
        # =================================================

        if current_low <= min(
            lows
        ):

            duplicate = any(
                point.index == i
                and point.kind == "bullish"
                for point in points
            )

            if not duplicate:

                points.append(
                    SwingPoint(
                        index=i,
                        price=current_low,
                        kind="bullish",
                    )
                )

    points.sort(
        key=lambda point:
        point.index
    )

    return points


# =========================================================
# STRUCTURE CLASSIFICATION
# =========================================================

def _classify_swing_structure(
    highs: List[SwingPoint],
    lows: List[SwingPoint],
) -> dict:

    result = {

        "higher_high": False,

        "higher_low": False,

        "lower_high": False,

        "lower_low": False,

    }

    # =====================================================
    # HIGH STRUCTURE
    # =====================================================

    if len(highs) >= 2:

        previous_high = highs[-2].price

        latest_high = highs[-1].price

        if latest_high > previous_high:

            result[
                "higher_high"
            ] = True

        elif latest_high < previous_high:

            result[
                "lower_high"
            ] = True

    # =====================================================
    # LOW STRUCTURE
    # =====================================================

    if len(lows) >= 2:

        previous_low = lows[-2].price

        latest_low = lows[-1].price

        if latest_low > previous_low:

            result[
                "higher_low"
            ] = True

        elif latest_low < previous_low:

            result[
                "lower_low"
            ] = True

    return result


# =========================================================
# DETECT STRUCTURE
# =========================================================

def detect_structure(
    candles: List[Candle],
    swings: List[SwingPoint],
):

    """
    Menentukan:

        bullish
        bearish

    dan:

        BOS
        CHoCH
        Range/Belum Break

    Struktur tidak hanya melihat candle terakhir,
    tetapi juga mempertimbangkan swing yang sudah
    terkonfirmasi.
    """

    if not candles:

        return (
            "bullish",
            "Range/Belum Break",
            None,
        )

    highs = [
        swing
        for swing in swings
        if swing.kind == "bearish"
    ]

    lows = [
        swing
        for swing in swings
        if swing.kind == "bullish"
    ]

    if not highs or not lows:

        return (
            "bullish",
            "Range/Belum Break",
            None,
        )

    last_close = _safe_float(
        candles[-1].close
    )

    last_high = highs[-1]

    last_low = lows[-1]

    # =====================================================
    # DETERMINE PREVIOUS STRUCTURE
    # =====================================================

    structure = _classify_swing_structure(
        highs,
        lows,
    )

    # =====================================================
    # BULLISH BREAK
    # =====================================================

    if last_close > last_high.price:

        if (
            structure["higher_high"]
            or structure["higher_low"]
        ):

            event = "BOS"

        else:

            event = "CHoCH"

        return (
            "bullish",
            event,
            last_high.price,
        )

    # =====================================================
    # BEARISH BREAK
    # =====================================================

    if last_close < last_low.price:

        if (
            structure["lower_high"]
            or structure["lower_low"]
        ):

            event = "BOS"

        else:

            event = "CHoCH"

        return (
            "bearish",
            event,
            last_low.price,
        )

    # =====================================================
    # NO BREAK
    # =====================================================

    if (
        structure["higher_high"]
        or structure["higher_low"]
    ):

        return (
            "bullish",
            "Range/Belum Break",
            None,
        )

    if (
        structure["lower_high"]
        or structure["lower_low"]
    ):

        return (
            "bearish",
            "Range/Belum Break",
            None,
        )

    # =====================================================
    # FALLBACK
    # =====================================================

    latest_swing = swings[-1]

    if latest_swing.kind == "bullish":

        return (
            "bullish",
            "Range/Belum Break",
            None,
        )

    return (
        "bearish",
        "Range/Belum Break",
        None,
    )


# =========================================================
# ORDER BLOCK STRENGTH
# =========================================================

def _calculate_ob_strength(
    base: Candle,
    impulse: Candle,
) -> float:

    impulse_range = _safe_float(
        impulse.range
    )

    if impulse_range <= 0:

        return 0.0

    body = _safe_float(
        impulse.body
    )

    body_ratio = (
        body
        / impulse_range
    )

    displacement = abs(
        _safe_float(
            impulse.close
        )
        - _safe_float(
            base.close
        )
    )

    strength = (
        body_ratio * 70
        + min(
            displacement
            / impulse_range
            * 30,
            30,
        )
    )

    return max(
        0.0,
        min(
            100.0,
            strength,
        ),
    )


# =========================================================
# FIND ORDER BLOCKS
# =========================================================

def find_order_blocks(
    candles: List[Candle],
    bias: Direction,
    lookback: int = 20,
) -> List[OrderBlock]:

    """
    Bullish OB:

        bearish candle
        +
        bullish displacement
        +
        close menembus high candle OB.

    Bearish OB:

        bullish candle
        +
        bearish displacement
        +
        close menembus low candle OB.

    Hanya OB yang searah dengan bias
    yang dikembalikan.
    """

    obs = []

    if not candles:

        return obs

    recent = candles[
        -lookback:
    ]

    offset = (
        len(candles)
        - len(recent)
    )

    if len(recent) < 2:

        return obs

    for i in range(
        0,
        len(recent) - 1,
    ):

        base = recent[i]

        impulse = recent[
            i + 1
        ]

        base_high = _safe_float(
            base.high
        )

        base_low = _safe_float(
            base.low
        )

        impulse_close = _safe_float(
            impulse.close
        )

        impulse_body = _safe_float(
            impulse.body
        )

        impulse_range = _safe_float(
            impulse.range
        )

        if impulse_range <= 0:

            continue

        body_ratio = (
            impulse_body
            / impulse_range
        )

        # =================================================
        # BULLISH OB
        # =================================================

        if (
            bias == "bullish"
            and base.is_bearish
            and impulse.is_bullish
            and body_ratio >= 0.60
            and impulse_close > base_high
        ):

            strength = (
                _calculate_ob_strength(
                    base,
                    impulse,
                )
            )

            obs.append(
                OrderBlock(

                    index=(
                        offset + i
                    ),

                    high=base_high,

                    low=base_low,

                    direction="bullish",

                    strength=strength,

                    mitigated=False,

                    fresh=True,

                    source_timeframe="M5",

                )
            )

        # =================================================
        # BEARISH OB
        # =================================================

        elif (
            bias == "bearish"
            and base.is_bullish
            and impulse.is_bearish
            and body_ratio >= 0.60
            and impulse_close < base_low
        ):

            strength = (
                _calculate_ob_strength(
                    base,
                    impulse,
                )
            )

            obs.append(
                OrderBlock(

                    index=(
                        offset + i
                    ),

                    high=base_high,

                    low=base_low,

                    direction="bearish",

                    strength=strength,

                    mitigated=False,

                    fresh=True,

                    source_timeframe="M5",

                )
            )

    # =====================================================
    # REMOVE DUPLICATE / KEEP LATEST
    # =====================================================

    unique = {}

    for ob in obs:

        key = (
            round(ob.high, 3),
            round(ob.low, 3),
            ob.direction,
        )

        unique[key] = ob

    obs = list(
        unique.values()
    )

    # =====================================================
    # MOST RECENT FIRST
    # =====================================================

    obs.sort(
        key=lambda x: (
            x.strength,
            x.index,
        ),
        reverse=True,
    )

    # Maximum 5 candidate OB
    return obs[:5]


# =========================================================
# FVG STRENGTH
# =========================================================

def _calculate_fvg_strength(
    first: Candle,
    middle: Candle,
    third: Candle,
    gap_size: float,
) -> float:

    middle_range = _safe_float(
        middle.range
    )

    if middle_range <= 0:

        return 0.0

    body_ratio = (
        _safe_float(
            middle.body
        )
        / middle_range
    )

    gap_ratio = (
        gap_size
        / middle_range
    )

    strength = (
        body_ratio * 70
        + min(
            gap_ratio * 30,
            30,
        )
    )

    return max(
        0.0,
        min(
            100.0,
            strength,
        ),
    )


# =========================================================
# FVG FILL STATUS
# =========================================================

def _calculate_fvg_fill_status(
    fvg: FVG,
    candles: List[Candle],
) -> str:

    if not candles:

        return "untouched"

    touched = False

    fully_filled = False

    for candle in candles:

        high = _safe_float(
            candle.high
        )

        low = _safe_float(
            candle.low
        )

        close = _safe_float(
            candle.close
        )

        # =================================================
        # BULLISH FVG
        # =================================================

        if fvg.direction == "bullish":

            if (
                low <= fvg.top
                and high >= fvg.bottom
            ):

                touched = True

            if close <= fvg.bottom:

                fully_filled = True

        # =================================================
        # BEARISH FVG
        # =================================================

        else:

            if (
                high >= fvg.bottom
                and low <= fvg.top
            ):

                touched = True

            if close >= fvg.top:

                fully_filled = True

    if fully_filled:

        return "full"

    if touched:

        return "partial"

    return "untouched"


# =========================================================
# FIND FVG
# =========================================================

def find_fvgs(
    candles: List[Candle],
    bias: Direction,
    lookback: int = 20,
) -> List[FVG]:

    """
    FVG menggunakan model 3 candle.

    Bullish:

        candle 1 high
            <
        candle 3 low

    Bearish:

        candle 1 low
            >
        candle 3 high
    """

    fvgs = []

    if len(candles) < 3:

        return fvgs

    recent = candles[
        -lookback:
    ]

    offset = (
        len(candles)
        - len(recent)
    )

    for i in range(
        len(recent) - 2
    ):

        first = recent[i]

        middle = recent[
            i + 1
        ]

        third = recent[
            i + 2
        ]

        first_high = _safe_float(
            first.high
        )

        first_low = _safe_float(
            first.low
        )

        third_high = _safe_float(
            third.high
        )

        third_low = _safe_float(
            third.low
        )

        # =================================================
        # BULLISH FVG
        # =================================================

        if (
            bias == "bullish"
            and first_high < third_low
        ):

            bottom = first_high

            top = third_low

            gap_size = (
                top - bottom
            )

            if gap_size <= 0:

                continue

            strength = (
                _calculate_fvg_strength(
                    first,
                    middle,
                    third,
                    gap_size,
                )
            )

            fvgs.append(
                FVG(

                    index=(
                        offset + i + 1
                    ),

                    top=top,

                    bottom=bottom,

                    direction="bullish",

                    strength=strength,

                    fill_status="untouched",

                    fresh=True,

                    source_timeframe="M5",

                )
            )

        # =================================================
        # BEARISH FVG
        # =================================================

        elif (
            bias == "bearish"
            and first_low > third_high
        ):

            top = first_low

            bottom = third_high

            gap_size = (
                top - bottom
            )

            if gap_size <= 0:

                continue

            strength = (
                _calculate_fvg_strength(
                    first,
                    middle,
                    third,
                    gap_size,
                )
            )

            fvgs.append(
                FVG(

                    index=(
                        offset + i + 1
                    ),

                    top=top,

                    bottom=bottom,

                    direction="bearish",

                    strength=strength,

                    fill_status="untouched",

                    fresh=True,

                    source_timeframe="M5",

                )
            )

    # =====================================================
    # UPDATE FILL STATUS
    # =====================================================

    for fvg in fvgs:

        candles_after = candles[
            fvg.index + 2:
        ]

        fvg.fill_status = (
            _calculate_fvg_fill_status(
                fvg,
                candles_after,
            )
        )

        fvg.fresh = (
            fvg.fill_status
            == "untouched"
        )

    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================

    unique = {}

    for fvg in fvgs:

        key = (
            round(fvg.top, 3),
            round(fvg.bottom, 3),
            fvg.direction,
        )

        unique[key] = fvg

    fvgs = list(
        unique.values()
    )

    # =====================================================
    # PRIORITY
    # =====================================================

    fvgs.sort(
        key=lambda x: (
            x.strength,
            x.index,
        ),
        reverse=True,
    )

    return fvgs[:5]


# =========================================================
# LIQUIDITY SWEEP
# =========================================================

def check_liquidity_sweep(
    candles: List[Candle],
    swings: List[SwingPoint],
    bias: Direction,
) -> bool:

    """
    Bullish:

        price sweep swing low
        lalu close kembali di atasnya.

    Bearish:

        price sweep swing high
        lalu close kembali di bawahnya.
    """

    if len(swings) < 2:

        return False

    if bias == "bullish":

        relevant = [
            swing
            for swing in swings
            if swing.kind == "bullish"
        ]

    else:

        relevant = [
            swing
            for swing in swings
            if swing.kind == "bearish"
        ]

    if not relevant:

        return False

    target = relevant[-1]

    for candle in candles[-5:]:

        low = _safe_float(
            candle.low
        )

        high = _safe_float(
            candle.high
        )

        close = _safe_float(
            candle.close
        )

        # =================================================
        # BULLISH SWEEP
        # =================================================

        if (
            bias == "bullish"
            and low < target.price
            and close > target.price
        ):

            return True

        # =================================================
        # BEARISH SWEEP
        # =================================================

        if (
            bias == "bearish"
            and high > target.price
            and close < target.price
        ):

            return True

    return False


# =========================================================
# LIQUIDITY LEVELS
# =========================================================

def find_liquidity_levels(
    swings: List[SwingPoint],
    tolerance: float = 0.5,
) -> List[float]:

    """
    Mencari level equal high / equal low
    sederhana dari swing yang berdekatan.

    Dipakai sebagai informasi tambahan,
    bukan alasan entry tunggal.
    """

    levels = []

    for i in range(
        len(swings)
    ):

        current = swings[i]

        for j in range(
            i + 1,
            len(swings),
        ):

            other = swings[j]

            if (
                current.kind
                != other.kind
            ):

                continue

            if abs(
                current.price
                - other.price
            ) <= tolerance:

                levels.append(
                    (
                        current.price
                        + other.price
                    )
                    / 2
                )

    # Remove duplicates
    unique = []

    for level in levels:

        if not any(
            abs(level - x)
            <= tolerance
            for x in unique
        ):

            unique.append(
                level
            )

    return unique


# =========================================================
# CONFLUENCE BUILDER
# =========================================================

def _build_confluences(
    bias: Direction,
    event: str,
    obs: List[OrderBlock],
    fvgs: List[FVG],
    liquidity_swept: bool,
    structure: dict,
) -> List[str]:

    reasons = []

    # =====================================================
    # STRUCTURE
    # =====================================================

    if event == "BOS":

        if bias == "bullish":

            reasons.append(
                "BOS bullish terkonfirmasi pada struktur M5."
            )

        else:

            reasons.append(
                "BOS bearish terkonfirmasi pada struktur M5."
            )

    elif event == "CHoCH":

        if bias == "bullish":

            reasons.append(
                "CHoCH bullish terdeteksi sebagai perubahan karakter struktur."
            )

        else:

            reasons.append(
                "CHoCH bearish terdeteksi sebagai perubahan karakter struktur."
            )

    else:

        if bias == "bullish":

            reasons.append(
                "Struktur M5 masih cenderung bullish meskipun belum menghasilkan break baru."
            )

        else:

            reasons.append(
                "Struktur M5 masih cenderung bearish meskipun belum menghasilkan break baru."
            )

    # =====================================================
    # HIGHER / LOWER STRUCTURE
    # =====================================================

    if structure[
        "higher_high"
    ]:

        reasons.append(
            "Swing high terbaru membentuk Higher High."
        )

    if structure[
        "higher_low"
    ]:

        reasons.append(
            "Swing low terbaru membentuk Higher Low."
        )

    if structure[
        "lower_high"
    ]:

        reasons.append(
            "Swing high terbaru membentuk Lower High."
        )

    if structure[
        "lower_low"
    ]:

        reasons.append(
            "Swing low terbaru membentuk Lower Low."
        )

    # =====================================================
    # ORDER BLOCK
    # =====================================================

    if obs:

        fresh_obs = [
            ob
            for ob in obs
            if ob.fresh
        ]

        if fresh_obs:

            reasons.append(
                f"Ditemukan {len(fresh_obs)} Order Block "
                f"{bias} yang masih fresh."
            )

        else:

            reasons.append(
                f"Ditemukan Order Block {bias}, "
                "namun sebagian sudah mengalami mitigasi."
            )

    # =====================================================
    # FVG
    # =====================================================

    if fvgs:

        fresh_fvgs = [
            fvg
            for fvg in fvgs
            if fvg.fill_status
            == "untouched"
        ]

        partial_fvgs = [
            fvg
            for fvg in fvgs
            if fvg.fill_status
            == "partial"
        ]

        if fresh_fvgs:

            reasons.append(
                f"Ada {len(fresh_fvgs)} Fair Value Gap "
                f"{bias} yang masih fresh."
            )

        if partial_fvgs:

            reasons.append(
                f"Ada {len(partial_fvgs)} Fair Value Gap "
                "yang sudah mengalami partial fill."
            )

    # =====================================================
    # LIQUIDITY
    # =====================================================

    if liquidity_swept:

        if bias == "bullish":

            reasons.append(
                "Liquidity sweep bullish terdeteksi "
                "sebelum harga kembali naik."
            )

        else:

            reasons.append(
                "Liquidity sweep bearish terdeteksi "
                "sebelum harga kembali turun."
            )

    return reasons


# =========================================================
# SCORE
# =========================================================

def _calculate_score(
    event: str,
    obs: List[OrderBlock],
    fvgs: List[FVG],
    liquidity_swept: bool,
    structure: dict,
) -> int:

    score = 40

    # =====================================================
    # STRUCTURE EVENT
    # =====================================================

    if event == "BOS":

        score += 15

    elif event == "CHoCH":

        score += 12

    # =====================================================
    # STRUCTURE QUALITY
    # =====================================================

    if (
        structure["higher_high"]
        and structure["higher_low"]
    ):

        score += 10

    if (
        structure["lower_high"]
        and structure["lower_low"]
    ):

        score += 10

    # =====================================================
    # OB
    # =====================================================

    if obs:

        score += min(
            15,
            len(obs) * 5,
        )

    # =====================================================
    # FVG
    # =====================================================

    if fvgs:

        score += min(
            15,
            len(fvgs) * 5,
        )

    # =====================================================
    # LIQUIDITY
    # =====================================================

    if liquidity_swept:

        score += 10

    return int(
        max(
            35,
            min(
                95,
                score,
            ),
        )
    )


# =========================================================
# MAIN ANALYZER
# =========================================================

def analyze(
    candles: List[Candle],
) -> SMCResult:

    """
    Entry point utama.

    Input:

        candle M5 CLOSED

    Output:

        SMCResult

    Semua zona yang dikembalikan merupakan
    kandidat yang dapat diproses oleh
    signal_builder.
    """

    if not candles:

        raise ValueError(
            "Candles tidak boleh kosong."
        )

    # =====================================================
    # MINIMUM DATA
    # =====================================================

    if len(candles) < 7:

        raise ValueError(
            "Minimal 7 candle dibutuhkan "
            "untuk analisa SMC."
        )

    # =====================================================
    # SWINGS
    # =====================================================

    swings = find_swing_points(
        candles,
        left=2,
        right=2,
    )

    # =====================================================
    # STRUCTURE
    # =====================================================

    (
        bias,
        event,
        bos_price,
    ) = detect_structure(
        candles,
        swings,
    )

    # =====================================================
    # SWING HIGH / LOW
    # =====================================================

    highs = [
        swing
        for swing in swings
        if swing.kind == "bearish"
    ]

    lows = [
        swing
        for swing in swings
        if swing.kind == "bullish"
    ]

    last_swing_high = (
        highs[-1].price
        if highs
        else None
    )

    last_swing_low = (
        lows[-1].price
        if lows
        else None
    )

    # =====================================================
    # STRUCTURE CLASSIFICATION
    # =====================================================

    structure = _classify_swing_structure(
        highs,
        lows,
    )

    # =====================================================
    # ORDER BLOCK
    # =====================================================

    obs = find_order_blocks(
        candles=candles,
        bias=bias,
        lookback=min(
            30,
            len(candles),
        ),
    )

    # =====================================================
    # FVG
    # =====================================================

    fvgs = find_fvgs(
        candles=candles,
        bias=bias,
        lookback=min(
            30,
            len(candles),
        ),
    )

    # =====================================================
    # LIQUIDITY
    # =====================================================

    liquidity_swept = (
        check_liquidity_sweep(
            candles=candles,
            swings=swings,
            bias=bias,
        )
    )

    # =====================================================
    # CONFLUENCES
    # =====================================================

    confluences = (
        _build_confluences(
            bias=bias,
            event=event,
            obs=obs,
            fvgs=fvgs,
            liquidity_swept=liquidity_swept,
            structure=structure,
        )
    )

    # =====================================================
    # SCORE
    # =====================================================

    score = _calculate_score(
        event=event,
        obs=obs,
        fvgs=fvgs,
        liquidity_swept=liquidity_swept,
        structure=structure,
    )

    # =====================================================
    # RESULT
    # =====================================================

    return SMCResult(

        bias=bias,

        structure_event=event,

        last_bos_price=bos_price,

        order_blocks=obs,

        fvgs=fvgs,

        liquidity_swept=liquidity_swept,

        confluences=confluences,

        score=score,

        swing_high=last_swing_high,

        swing_low=last_swing_low,

        higher_high=structure[
            "higher_high"
        ],

        higher_low=structure[
            "higher_low"
        ],

        lower_high=structure[
            "lower_high"
        ],

        lower_low=structure[
            "lower_low"
        ],
    )


# =========================================================
# DEBUG HELPER
# =========================================================

def debug_smc(
    result: SMCResult,
) -> str:

    lines = [

        "",
        "==============================",
        "XAU AI SMC ANALYZER",
        "==============================",

        f"Bias          : {result.bias}",

        f"Structure     : {result.structure_event}",

        f"BOS Price     : {result.last_bos_price}",

        f"Swing High    : {result.swing_high}",

        f"Swing Low     : {result.swing_low}",

        f"Higher High   : {result.higher_high}",

        f"Higher Low    : {result.higher_low}",

        f"Lower High    : {result.lower_high}",

        f"Lower Low     : {result.lower_low}",

        f"Liquidity     : {result.liquidity_swept}",

        f"OB Count      : {len(result.order_blocks)}",

        f"FVG Count     : {len(result.fvgs)}",

        f"Score         : {result.score}%",

        "",
        "ORDER BLOCKS",
        "------------------------------",
    ]

    for i, ob in enumerate(
        result.order_blocks,
        1,
    ):

        lines.append(
            (
                f"{i}. "
                f"{ob.direction} | "
                f"{ob.low:.2f} - "
                f"{ob.high:.2f} | "
                f"strength={ob.strength:.1f} | "
                f"fresh={ob.fresh}"
            )
        )

    lines += [

        "",
        "FAIR VALUE GAPS",
        "------------------------------",
    ]

    for i, fvg in enumerate(
        result.fvgs,
        1,
    ):

        lines.append(
            (
                f"{i}. "
                f"{fvg.direction} | "
                f"{fvg.bottom:.2f} - "
                f"{fvg.top:.2f} | "
                f"fill={fvg.fill_status} | "
                f"strength={fvg.strength:.1f}"
            )
        )

    lines += [

        "",
        "CONFLUENCES",
        "------------------------------",
    ]

    for reason in result.confluences:

        lines.append(
            f"• {reason}"
        )

    lines += [

        "==============================",
        "",
    ]

    return "\n".join(
        lines
    )

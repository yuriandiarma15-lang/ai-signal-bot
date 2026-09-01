"""
services/signal_builder.py

XAU AI SMC REAL
===============

M5  = STRUCTURE
M1  = ENTRY TIMING

PRINSIP UTAMA
-------------
1. SIGNAL SELALU KELUAR:
   BUY atau SELL berdasarkan probability tertinggi.

2. M5 adalah struktur utama:
   - BOS
   - CHoCH
   - HH
   - HL
   - LH
   - LL
   - Order Block
   - FVG
   - Liquidity
   - Demand / Supply

3. M1 digunakan untuk:
   - entry timing
   - rejection
   - micro structure
   - retest

4. Tidak ada lagi:
   - NO TRADE karena score rendah
   - NO TRADE karena partial FVG
   - NO TRADE karena tidak ada rejection
   - NO TRADE karena RR
   - NO TRADE karena tidak ditemukan OB/FVG

5. Jika OB/FVG tidak tersedia:
   fallback ke Demand/Supply dan swing area.

6. Pending:
   BUY  -> Buy Limit
   SELL -> Sell Limit

7. Jika harga sudah dekat dengan entry:
   Market Buy / Market Sell.

8. Probability:
   memilih BUY atau SELL dengan skor tertinggi.

9. SL / TP:
   dihitung dari ENTRY PRICE.

10. Output:
    signal utama berada PALING ATAS.

11. Harga:
    4005.72 -> 4005
    3998.34 -> 3998

=============================================================
CHANGELOG (FIX)
=============================================================
FIX #1 — PARAMETER MISMATCH SAAT MEMANGGIL
          combine_smc_and_fundamental()

    SEBELUM (SALAH):
        combine_smc_and_fundamental(
            smc_bias=m5_smc.bias,
            probability_buy=smc_probability_buy,
            probability_sell=smc_probability_sell,
            fundamental=fundamental_context,
        )

    combined_service.py mendefinisikan parameter dengan nama
    BERBEDA:
        smc_result=None,
        fundamental_context=None,
        smc_probability_buy=None,
        smc_probability_sell=None,
        **kwargs,

    Karena signal_builder mengirim nama parameter yang tidak
    cocok sama sekali (smc_bias, probability_buy,
    probability_sell, fundamental), semuanya jatuh ke **kwargs
    dan TIDAK PERNAH dipakai. Akibatnya smc_probability_buy /
    smc_probability_sell di dalam combine_smc_and_fundamental
    selalu None -> fallback ke bias kosong -> 50/50 NEUTRAL.
    fundamental_context juga selalu None -> 50/50 NEUTRAL.
    Hasil combine selalu 50/50, lalu tie-breaker memilih BUY.

    SESUDAH (BENAR):
        combine_smc_and_fundamental(
            smc_result=m5_smc,
            smc_probability_buy=smc_probability_buy,
            smc_probability_sell=smc_probability_sell,
            fundamental_context=fundamental_context,
        )

FIX #2 — TIE-BREAKER _choose_direction() DIAM-DIAM SELALU BUY

    SEBELUM:
        final_bias = _choose_direction(
            probability_buy,
            probability_sell,
        )

        def _choose_direction(buy_probability, sell_probability):
            if buy_probability >= sell_probability:
                return "bullish"
            return "bearish"

    Kalau buy == sell (mis. 50/50 akibat FIX #1 belum ada),
    fungsi ini SELALU mengembalikan "bullish". Ini membuat bug
    parameter di atas semakin tidak kelihatan, karena hasilnya
    konsisten BUY bukan error/exception.

    SESUDAH:
    final_bias sekarang diambil dari `bias` yang sudah
    diputuskan oleh combine_smc_and_fundamental() (yang
    tie-break-nya memakai smc_probability_buy/sell ASLI,
    bukan hasil gabungan yang sudah dibulatkan). Fungsi
    _choose_direction() hanya dipakai sebagai fallback kalau
    combined_result ternyata tidak mengandung key "bias" sama
    sekali (mis. exception fallback dict lama).

FIX #3 — CACHE RATE-LIMITER "1 SIGNAL PER JAM" TIDAK SELARAS
          DENGAN JAM DINDING, SEHINGGA SIGNAL JAM BARU BISA
          IKUT MEMAKAI SIGNAL JAM SEBELUMNYA

    SEBELUM (SALAH):
        _cache_is_fresh() hanya menghitung selisih menit
        murni antara `now` dan `generated_at`:

            elapsed_minutes = (now - generated_at).total_seconds() / 60
            return elapsed_minutes < SIGNAL_INTERVAL_MINUTES

        Masalahnya: signal jam 14 sering baru selesai
        digenerate beberapa menit SETELAH jam 14:00 (proses
        fetch candle, fundamental, dsb butuh waktu, atau
        scheduler tidak presisi di menit 00). Kalau signal
        jam 14 baru "lahir" jam 14:05, maka saat scheduler
        mencoba generate signal jam 15:00, selisihnya baru
        55 menit (< 60 menit) -> cache dianggap masih segar
        -> signal jam 14 dipakai ulang dan dikirim sebagai
        signal jam 15.

    SESUDAH (BENAR):
        Cache sekarang juga mengecek apakah `now` dan
        `generated_at` masih berada di JAM DINDING yang sama
        (tanggal + jam yang sama). Begitu jam berganti
        (mis. dari jam 14 ke jam 15), cache otomatis dianggap
        TIDAK segar lagi -- terlepas dari berapa pun elapsed
        minutes-nya -- sehingga signal baru pasti dihasilkan
        di jam baru. Elapsed-minutes check tetap dipertahankan
        sebagai lapisan pengaman tambahan di dalam jam yang
        sama (mencegah spam analyze() kalau di-trigger berkali-
        kali dalam jam yang sama).
=============================================================
"""


# =========================================================
# IMPORT
# =========================================================

import logging

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo


# =========================================================
# LOGGER
#
# FIX: logger dipakai di beberapa tempat di file ini
# (fundamental news, combined analysis) tapi sebelumnya
# tidak pernah didefinisikan -> NameError saat runtime.
# =========================================================

logger = logging.getLogger(__name__)


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
# FUNDAMENTAL + COMBINED AI
# =========================================================

from .fundamental_service import (
    get_latest_fundamental_news,
    build_combined_fundamental_context,
)

from .combined_service import (
    combine_smc_and_fundamental,
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
    from config import M1_CONFIRMATION_CANDLES
except ImportError:
    M1_CONFIRMATION_CANDLES = 5


try:
    from config import REQUIRE_M1_REJECTION
except ImportError:
    REQUIRE_M1_REJECTION = False


try:
    from config import ALLOW_PARTIAL_FVG_MARKET
except ImportError:
    ALLOW_PARTIAL_FVG_MARKET = True


try:
    from config import MIN_SMC_SCORE
except ImportError:
    MIN_SMC_SCORE = 0


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

    # =====================================================
    # EXTRA EDUCATIONAL DATA
    # =====================================================

    current_price: float = 0.0

    probability_buy: int = 50

    probability_sell: int = 50

    structure_event: str = "-"

    structure_price_low: Optional[float] = None

    structure_price_high: Optional[float] = None

    swing_type: str = "-"

    swing_low: Optional[float] = None

    swing_high: Optional[float] = None

    liquidity_type: str = "-"

    liquidity_price: Optional[float] = None

    liquidity_low: Optional[float] = None

    liquidity_high: Optional[float] = None

    demand_low: Optional[float] = None

    demand_high: Optional[float] = None

    supply_low: Optional[float] = None

    supply_high: Optional[float] = None

    fvg_low: Optional[float] = None

    fvg_high: Optional[float] = None

    ob_low: Optional[float] = None

    ob_high: Optional[float] = None

    # =====================================================
    # ANALYSIS-BASED SL/TP DISTANCE (DISPLAY)
    # =====================================================

    sl_pips: int = 0

    tp1_pips: int = 0

    tp2_pips: int = 0


# =========================================================
# EXCEPTION
# =========================================================

class NoTradeSignal(Exception):
    """
    Dipertahankan untuk compatibility dengan code lama.

    generate_signal() sekarang hanya menggunakan exception
    untuk error DATA FATAL, bukan untuk kondisi market.
    """
    pass


# =========================================================
# GENERIC ATTRIBUTE HELPER
# =========================================================

def _get_attr(
    obj,
    names,
    default=None,
):
    """
    Membaca beberapa kemungkinan nama attribute.

    Berguna supaya signal_builder tetap compatible
    dengan versi SMCResult yang berbeda.
    """

    if obj is None:
        return default

    for name in names:

        try:

            value = getattr(
                obj,
                name,
                None,
            )

        except Exception:

            value = None

        if value is not None:
            return value

    return default


# =========================================================
# FLOAT HELPER
# =========================================================

def _safe_float(
    value,
    default=None,
):

    try:

        if value is None:
            return default

        return float(value)

    except (
        TypeError,
        ValueError,
    ):

        return default


# =========================================================
# TIMEZONE HELPER
# =========================================================

def _to_wib(
    dt: datetime,
) -> datetime:

    if dt.tzinfo is None:

        return dt.replace(
            tzinfo=WIB
        )

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
        "Pantau struktur market, liquidity "
        "dan reaksi harga dengan disiplin.",
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

    now = datetime.now(WIB)

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
        key=lambda c: _to_wib(
            c.time
        )
    )

    if len(closed) < count:

        raise ValueError(
            "Candle M5 CLOSED tidak cukup. "
            f"Tersedia {len(closed)}, "
            f"dibutuhkan {count}."
        )

    return closed[-count:]


# =========================================================
# CLOSED M1
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

            closed.append(
                candle
            )

    closed.sort(
        key=lambda c: _to_wib(
            c.time
        )
    )

    if count <= 0:
        return closed

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

    touched = (
        _zone_touched_by_recent_price(
            bottom,
            top,
            recent_candles,
        )
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
            candle.close
            - candle.low
        ) / candle_range

        lower_wick = (
            min(
                candle.open,
                candle.close,
            )
            - candle.low
        )

        body = abs(
            candle.close
            - candle.open
        )

        if not candle.is_bullish:
            continue

        if close_strength < 0.55:
            continue

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
            candle.high
            - candle.close
        ) / candle_range

        upper_wick = (
            candle.high
            - max(
                candle.open,
                candle.close,
            )
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
# ZONE MATCH
# =========================================================

def _zone_matches_bias(
    bias: str,
    current_price: float,
    zone_low: float,
    zone_high: float,
) -> bool:

    if bias == "bullish":

        return zone_low <= current_price

    if bias == "bearish":

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

        low = _safe_float(
            _get_attr(
                ob,
                ["low", "bottom"],
            )
        )

        high = _safe_float(
            _get_attr(
                ob,
                ["high", "top"],
            )
        )

        if low is None or high is None:
            continue

        zone_low = min(
            low,
            high,
        )

        zone_high = max(
            low,
            high,
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
                "distance_pips": _price_to_pips(
                    distance
                ),
                "price": mid,
                "type": "Order Block",
                "status": status,
                "low": zone_low,
                "high": zone_high,
                "timeframe": timeframe,
                "index": _get_attr(
                    ob,
                    ["index"],
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

        bottom = _safe_float(
            _get_attr(
                fvg,
                ["bottom", "low"],
            )
        )

        top = _safe_float(
            _get_attr(
                fvg,
                ["top", "high"],
            )
        )

        if bottom is None or top is None:
            continue

        zone_low = min(
            bottom,
            top,
        )

        zone_high = max(
            bottom,
            top,
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

        direction = str(
            _get_attr(
                fvg,
                ["direction"],
                "",
            )
        ).lower()

        status = _fvg_fill_status(
            direction,
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
                "index": _get_attr(
                    fvg,
                    ["index"],
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
            -x.get(
                "index",
                -1,
            ),
        )
    )

    return candidates[0]


# =========================================================
# FALLBACK DEMAND / SUPPLY
# =========================================================

def _build_fallback_zone(
    bias: str,
    candles: List[Candle],
    current_price: float,
    timeframe: str,
):

    """
    Jika OB/FVG tidak tersedia, gunakan area candle
    sebagai Demand/Supply.

    Ini membuat signal tetap bisa keluar.
    """

    if not candles:
        return None

    sample = candles[-6:]

    if bias == "bullish":

        lows = [
            float(c.low)
            for c in sample
        ]

        highs = [
            float(c.high)
            for c in sample
        ]

        low = min(lows)

        # Ambil area bawah market.
        below = [
            c for c in sample
            if c.low <= current_price
        ]

        if below:

            target = below[-1]

            zone_low = float(
                target.low
            )

            zone_high = float(
                min(
                    target.open,
                    target.close,
                )
            )

        else:

            zone_low = low

            zone_high = (
                low
                + (
                    max(highs) - low
                ) * 0.20
            )

        if zone_high > current_price:
            zone_high = current_price

        if zone_high <= zone_low:
            zone_high = (
                zone_low
                + _pips_to_price(10)
            )

        return {
            "distance": _zone_distance(
                current_price,
                zone_low,
                zone_high,
            ),
            "distance_pips": _zone_distance_pips(
                current_price,
                zone_low,
                zone_high,
            ),
            "price": (
                zone_low
                + zone_high
            ) / 2,
            "type": "Demand",
            "status": "untouched",
            "low": zone_low,
            "high": zone_high,
            "timeframe": timeframe,
            "index": -1,
        }

    # =====================================================
    # BEARISH SUPPLY
    # =====================================================

    highs = [
        float(c.high)
        for c in sample
    ]

    lows = [
        float(c.low)
        for c in sample
    ]

    high = max(highs)

    above = [
        c for c in sample
        if c.high >= current_price
    ]

    if above:

        target = above[-1]

        zone_high = float(
            target.high
        )

        zone_low = float(
            max(
                target.open,
                target.close,
            )
        )

    else:

        zone_high = high

        zone_low = (
            high
            - (
                high - min(lows)
            ) * 0.20
        )

    if zone_low < current_price:
        zone_low = current_price

    if zone_low >= zone_high:
        zone_low = (
            zone_high
            - _pips_to_price(10)
        )

    return {
        "distance": _zone_distance(
            current_price,
            zone_low,
            zone_high,
        ),
        "distance_pips": _zone_distance_pips(
            current_price,
            zone_low,
            zone_high,
        ),
        "price": (
            zone_low
            + zone_high
        ) / 2,
        "type": "Supply",
        "status": "untouched",
        "low": zone_low,
        "high": zone_high,
        "timeframe": timeframe,
        "index": -1,
    }


# =========================================================
# BEST ENTRY ZONE
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
    # M5
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

    # =====================================================
    # FALLBACK DEMAND / SUPPLY
    # =====================================================

    fallback = _build_fallback_zone(
        bias=m5_smc.bias,
        candles=m5_candles,
        current_price=current_price,
        timeframe="M5",
    )

    if fallback is not None:

        return (
            fallback,
            m5_smc,
        )

    # =====================================================
    # LAST RESORT
    # =====================================================

    zone_width = _pips_to_price(10)

    if m5_smc.bias == "bullish":

        zone_low = (
            current_price
            - zone_width
        )

        zone_high = current_price

    else:

        zone_low = current_price

        zone_high = (
            current_price
            + zone_width
        )

    fallback = {
        "distance": 0.0,
        "distance_pips": 0.0,
        "price": (
            zone_low
            + zone_high
        ) / 2,
        "type": (
            "Demand"
            if m5_smc.bias == "bullish"
            else "Supply"
        ),
        "status": "untouched",
        "low": zone_low,
        "high": zone_high,
        "timeframe": "M5",
        "index": -1,
    }

    return (
        fallback,
        m5_smc,
    )


# =========================================================
# RECENT SWING
# =========================================================

def _find_recent_swing(
    candles: List[Candle],
):

    if not candles:
        return (
            None,
            None,
        )

    highs = [
        float(c.high)
        for c in candles
    ]

    lows = [
        float(c.low)
        for c in candles
    ]

    swing_high = max(highs)
    swing_low = min(lows)

    return (
        swing_low,
        swing_high,
    )


# =========================================================
# SWING CLASSIFICATION
# =========================================================

def _classify_swings(
    candles: List[Candle],
) -> Tuple[
    str,
    Optional[float],
    Optional[float],
]:

    if len(candles) < 6:

        low, high = _find_recent_swing(
            candles
        )

        return (
            "-",
            low,
            high,
        )

    mid = len(candles) // 2

    first = candles[:mid]
    second = candles[mid:]

    first_high = max(
        float(c.high)
        for c in first
    )

    second_high = max(
        float(c.high)
        for c in second
    )

    first_low = min(
        float(c.low)
        for c in first
    )

    second_low = min(
        float(c.low)
        for c in second
    )

    latest_high = second_high
    latest_low = second_low

    if (
        latest_high > first_high
        and latest_low > first_low
    ):

        return (
            "HH + HL",
            latest_low,
            latest_high,
        )

    if (
        latest_high < first_high
        and latest_low < first_low
    ):

        return (
            "LH + LL",
            latest_low,
            latest_high,
        )

    if latest_low > first_low:

        return (
            "HL",
            latest_low,
            latest_high,
        )

    if latest_high < first_high:

        return (
            "LH",
            latest_low,
            latest_high,
        )

    return (
        "RANGE",
        latest_low,
        latest_high,
    )


# =========================================================
# STRUCTURE EVENT
# =========================================================

def _get_structure_event(
    smc: SMCResult,
    candles: List[Candle],
):

    event = _get_attr(
        smc,
        [
            "structure_event",
            "event",
            "last_event",
            "market_structure",
        ],
        None,
    )

    if event:

        event_text = str(
            event
        ).upper()

        if "CHOCH" in event_text:
            return "CHoCH"

        if "BOS" in event_text:
            return "BOS"

    # fallback dari bias
    bias = str(
        _get_attr(
            smc,
            ["bias"],
            "",
        )
    ).lower()

    if bias == "bullish":
        return "BOS"

    if bias == "bearish":
        return "BOS"

    return "-"


# =========================================================
# STRUCTURE RANGE
# =========================================================

def _get_structure_range(
    candles: List[Candle],
    event: str,
):

    if not candles:
        return (
            None,
            None,
        )

    recent = candles[-5:]

    highs = [
        float(c.high)
        for c in recent
    ]

    lows = [
        float(c.low)
        for c in recent
    ]

    return (
        min(lows),
        max(highs),
    )


# =========================================================
# LIQUIDITY
# =========================================================

def _get_liquidity(
    candles: List[Candle],
    bias: str,
):

    if not candles:
        return (
            "-",
            None,
            None,
            None,
        )

    highs = [
        float(c.high)
        for c in candles
    ]

    lows = [
        float(c.low)
        for c in candles
    ]

    liquidity_high = max(
        highs
    )

    liquidity_low = min(
        lows
    )

    if bias == "bullish":

        return (
            "Sell-side liquidity",
            liquidity_low,
            liquidity_low,
            liquidity_high,
        )

    return (
        "Buy-side liquidity",
        liquidity_high,
        liquidity_low,
        liquidity_high,
    )


# =========================================================
# EXTRACT OB
# =========================================================

def _extract_best_ob(
    smc: SMCResult,
):

    obs = getattr(
        smc,
        "order_blocks",
        [],
    )

    if not obs:
        return (
            None,
            None,
        )

    ob = obs[-1]

    low = _safe_float(
        _get_attr(
            ob,
            ["low", "bottom"],
        )
    )

    high = _safe_float(
        _get_attr(
            ob,
            ["high", "top"],
        )
    )

    return (
        low,
        high,
    )


# =========================================================
# EXTRACT FVG
# =========================================================

def _extract_best_fvg(
    smc: SMCResult,
):

    fvgs = getattr(
        smc,
        "fvgs",
        [],
    )

    if not fvgs:
        return (
            None,
            None,
        )

    fvg = fvgs[-1]

    low = _safe_float(
        _get_attr(
            fvg,
            ["bottom", "low"],
        )
    )

    high = _safe_float(
        _get_attr(
            fvg,
            ["top", "high"],
        )
    )

    return (
        low,
        high,
    )


# =========================================================
# DIRECTIONAL SCORE
# =========================================================

def _directional_probability(
    candles: List[Candle],
    smc: SMCResult,
    m1_smc: Optional[SMCResult],
    m1_confirmation_buy: bool,
    m1_confirmation_sell: bool,
) -> Tuple[int, int]:

    """
    Menghasilkan probability BUY dan SELL.

    Ini bukan probabilitas statistik broker.
    Ini adalah confidence score berbasis SMC.
    """

    buy = 50
    sell = 50

    bias = str(
        _get_attr(
            smc,
            ["bias"],
            "",
        )
    ).lower()

    score = _safe_float(
        _get_attr(
            smc,
            ["score"],
            50,
        ),
        50,
    )

    score = max(
        0,
        min(
            100,
            score,
        ),
    )

    # =====================================================
    # M5 BIAS
    # =====================================================

    bias_strength = int(
        max(
            5,
            min(
                25,
                score / 4,
            ),
        )
    )

    if bias == "bullish":

        buy += bias_strength
        sell -= bias_strength

    elif bias == "bearish":

        sell += bias_strength
        buy -= bias_strength

    # =====================================================
    # STRUCTURE
    # =====================================================

    event = str(
        _get_attr(
            smc,
            [
                "structure_event",
                "event",
            ],
            "",
        )
    ).upper()

    if "BOS" in event:

        if bias == "bullish":

            buy += 10

        elif bias == "bearish":

            sell += 10

    elif "CHOCH" in event:

        if bias == "bullish":

            buy += 7

        elif bias == "bearish":

            sell += 7

    # =====================================================
    # M1 BIAS
    # =====================================================

    if m1_smc is not None:

        m1_bias = str(
            _get_attr(
                m1_smc,
                ["bias"],
                "",
            )
        ).lower()

        if m1_bias == "bullish":

            buy += 8
            sell -= 4

        elif m1_bias == "bearish":

            sell += 8
            buy -= 4

    # =====================================================
    # M1 REJECTION
    # =====================================================

    if m1_confirmation_buy:

        buy += 8

    if m1_confirmation_sell:

        sell += 8

    # =====================================================
    # CANDLE MOMENTUM
    # =====================================================

    if candles:

        recent = candles[-5:]

        bullish_count = sum(
            1
            for c in recent
            if c.is_bullish
        )

        bearish_count = sum(
            1
            for c in recent
            if c.is_bearish
        )

        if bullish_count > bearish_count:

            buy += 5

        elif bearish_count > bullish_count:

            sell += 5

    # =====================================================
    # NORMALIZE
    # =====================================================

    buy = max(
        1,
        min(
            99,
            buy,
        ),
    )

    sell = max(
        1,
        min(
            99,
            sell,
        ),
    )

    total = buy + sell

    buy_probability = int(
        round(
            buy
            / total
            * 100
        )
    )

    sell_probability = (
        100
        - buy_probability
    )

    return (
        buy_probability,
        sell_probability,
    )


# =========================================================
# FINAL DIRECTION
#
# CATATAN (FIX):
# Fungsi ini sekarang HANYA dipakai sebagai FALLBACK kalau
# combined_result dari combine_smc_and_fundamental() tidak
# mengandung key "bias" sama sekali (mis. jika suatu saat
# combined_service diganti versi lama). Jalur utama sekarang
# memakai bias yang sudah diputuskan oleh
# combine_smc_and_fundamental(), yang tie-break-nya memakai
# probability SMC ASLI (smc_probability_buy/sell), bukan
# probability gabungan yang sudah dibulatkan.
# =========================================================

def _choose_direction(
    buy_probability: int,
    sell_probability: int,
) -> str:

    if buy_probability > sell_probability:

        return "bullish"

    if sell_probability > buy_probability:

        return "bearish"

    # Tie murni (jarang terjadi di jalur utama, tapi tetap
    # ditangani secara eksplisit -- TIDAK diam-diam ke bullish
    # tanpa alasan). Di sini kita tidak punya info tambahan,
    # jadi kita pilih berdasarkan nilai yang lebih besar dari
    # 50 (default netral) -- kalau sama-sama 50, default ke
    # bearish supaya tidak terus-menerus condong ke BUY seperti
    # bug sebelumnya. Jalur utama di generate_signal() seharusnya
    # tidak pernah sampai ke default ini.
    return "bearish"


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
            "Market",
            False,
        )

    # =====================================================
    # BULLISH
    # =====================================================

    if bias == "bullish":

        # Entry berada di bawah market.
        if entry_price < (
            current_price
            - MARKET_ENTRY_TOLERANCE
        ):

            return (
                "Buy Limit",
                True,
            )

        # Harga sudah sangat dekat.
        return (
            "Market",
            False,
        )

    # =====================================================
    # BEARISH
    # =====================================================

    if bias == "bearish":

        # Entry berada di atas market.
        if entry_price > (
            current_price
            + MARKET_ENTRY_TOLERANCE
        ):

            return (
                "Sell Limit",
                True,
            )

        return (
            "Market",
            False,
        )

    return (
        "Market",
        False,
    )


# =========================================================
# RISK  (ANALYSIS-BASED, DENGAN BATAS AMAN)
#
# SL/TP1/TP2 dihitung dari:
#   - lebar zona entry (OB/FVG/Demand/Supply)
#   - volatilitas candle M5 terakhir (proxy ATR)
#   - target struktur (swing high/low M5)
#
# TAPI dengan batas keamanan supaya jarak tidak liar:
#   - SL DIJAMIN berada di antara SL_MIN_PIPS - SL_MAX_PIPS.
#   - RR (TP1) dipilih dari daftar tetap RR_LEVELS,
#     berdasarkan kekuatan sinyal (probability arah yang
#     dipilih). Sinyal lebih kuat -> RR lebih tinggi.
#   - TP2 = RR TP1 + RR2_EXTRA (tetap dari daftar yang sama,
#     satu tingkat di atas RR1), supaya TP2 selalu lebih jauh
#     dari TP1 tapi tidak melebihi rentang yang wajar.
# =========================================================

SL_MIN_PIPS = 40
SL_MAX_PIPS = 70

# Daftar RR yang boleh dipakai untuk TP1.
# Dipilih berdasarkan kekuatan/probability sinyal.
RR_LEVELS = [1.1, 1.2, 1.3, 1.4, 1.5]

# Selisih RR yang ditambahkan untuk TP2 relatif ke RR1.
RR2_EXTRA = 0.8


def _select_rr1(
    probability: int,
) -> float:
    """
    Memilih RR (TP1) dari RR_LEVELS berdasarkan probability
    arah sinyal yang terpilih.

    Probability rendah (~50%) -> RR paling kecil (1.1).
    Probability tinggi (~99%) -> RR paling besar (1.5).
    """

    probability = max(
        50,
        min(99, int(probability)),
    )

    span = 99 - 50

    step = span / (len(RR_LEVELS) - 1)

    idx = int(
        round(
            (probability - 50) / step
        )
    )

    idx = max(
        0,
        min(len(RR_LEVELS) - 1, idx),
    )

    return RR_LEVELS[idx]


def _calculate_risk(
    bias: str,
    entry_price: float,
    zone_low: Optional[float] = None,
    zone_high: Optional[float] = None,
    candles: Optional[List[Candle]] = None,
    swing_low: Optional[float] = None,
    swing_high: Optional[float] = None,
    probability: int = 50,
):

    candles = candles or []

    # =====================================================
    # VOLATILITAS (PROXY ATR)
    #
    # Rata-rata range candle M5 terakhir dipakai sebagai
    # dasar jarak SL, supaya SL tetap mengikuti kondisi
    # market — tapi hasilnya tetap di-clamp di bawah.
    # =====================================================

    ranges = [
        (c.high - c.low)
        for c in candles[-10:]
        if (c.high - c.low) > 0
    ]

    atr = (
        sum(ranges) / len(ranges)
        if ranges
        else _pips_to_price(
            (SL_MIN_PIPS + SL_MAX_PIPS) / 2
        )
    )

    # =====================================================
    # JARAK SL DARI ANALISA (SEBELUM DI-CLAMP)
    #
    # Dasar jarak = jarak ke tepi zona entry (kalau ada)
    # ditambah setengah ATR sebagai buffer noise, atau
    # ATR penuh kalau zona tidak tersedia.
    # =====================================================

    if bias == "bullish":

        zone_reference = (
            zone_low
            if zone_low is not None
            else entry_price - atr
        )

        raw_risk = (
            (entry_price - zone_reference)
            + atr * 0.5
        )

    else:

        zone_reference = (
            zone_high
            if zone_high is not None
            else entry_price + atr
        )

        raw_risk = (
            (zone_reference - entry_price)
            + atr * 0.5
        )

    if raw_risk <= 0:
        raw_risk = atr

    # =====================================================
    # CLAMP SL KE RENTANG 40 - 70 PIP
    #
    # Ini batas keras: berapa pun hasil analisa di atas,
    # SL akhir TIDAK PERNAH lebih kecil dari SL_MIN_PIPS
    # dan TIDAK PERNAH lebih besar dari SL_MAX_PIPS.
    # =====================================================

    sl_min_price = _pips_to_price(SL_MIN_PIPS)
    sl_max_price = _pips_to_price(SL_MAX_PIPS)

    risk = max(
        sl_min_price,
        min(sl_max_price, raw_risk),
    )

    # =====================================================
    # RR DARI ANALISA (KEKUATAN SINYAL) — DIBATASI DAFTAR
    # =====================================================

    rr1 = _select_rr1(probability)

    rr2 = round(rr1 + RR2_EXTRA, 1)

    # =====================================================
    # SL / TP1 / TP2
    # =====================================================

    if bias == "bullish":

        sl = entry_price - risk
        tp1 = entry_price + risk * rr1
        tp2 = entry_price + risk * rr2

    else:

        sl = entry_price + risk
        tp1 = entry_price - risk * rr1
        tp2 = entry_price - risk * rr2

    # =====================================================
    # RISK / REWARD AKTUAL
    # =====================================================

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
        round(sl, 2),
        round(tp1, 2),
        round(tp2, 2),
        round(rr_tp1, 2),
        round(rr_tp2, 2),
    )

# =====================================================
# ENTRY DESCRIPTION — REALTIME
# =====================================================

def _build_entry_description(
    order_type: str,
    is_pending: bool,
    current_price: float,
    entry_price: float,
    zone_type: str,
) -> str:

    # =================================================
    # SEMUA ENTRY REALTIME
    # =================================================

    if order_type == "Market":

        return (
            f"MARKET ENTRY — "
            f"entry realtime "
            f"{_price_display(entry_price)}"
        )

    # =================================================
    # FALLBACK
    # =================================================

    return (
        f"MARKET ENTRY — "
        f"{_price_display(entry_price)}"
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

    if is_pending:

        if bias == "bullish":

            return (
                "Pelajaran entry: market sedang "
                "dipantau untuk retracement ke Demand/"
                "OB/FVG. Karena harga entry berada di "
                "bawah market, BUY LIMIT digunakan agar "
                "tidak mengejar harga."
            )

        return (
            "Pelajaran entry: market sedang "
            "dipantau untuk retracement ke Supply/"
            "OB/FVG. Karena harga entry berada di "
            "atas market, SELL LIMIT digunakan agar "
            "tidak mengejar harga."
        )

    if zone_type == "Order Block":

        return (
            f"Pelajaran entry: Order Block {zone_timeframe} "
            f"menunjukkan area institusional yang sedang "
            f"dipantau. {direction} menjadi pihak yang "
            f"lebih dominan berdasarkan struktur."
        )

    if zone_type == "Fair Value Gap":

        return (
            f"Pelajaran entry: FVG {zone_timeframe} "
            "menunjukkan imbalance. Harga dapat "
            "melakukan retracement untuk mengisi "
            "sebagian atau seluruh imbalance tersebut."
        )

    if zone_type == "Demand":

        return (
            f"Pelajaran entry: Demand {zone_timeframe} "
            "digunakan sebagai area di mana buyer "
            "berpotensi kembali masuk setelah retracement."
        )

    if zone_type == "Supply":

        return (
            f"Pelajaran entry: Supply {zone_timeframe} "
            "digunakan sebagai area di mana seller "
            "berpotensi kembali masuk setelah retracement."
        )

    return (
        "Pelajaran entry: keputusan menggabungkan "
        "market structure, liquidity, zone dan "
        "price action M1."
    )


# =========================================================
# SIGNAL RATE LIMITER — 1 SIGNAL PER JAM
#
# CATATAN PENTING:
# Cache ini disimpan di MEMORY proses (module-level
# variable). Ini cukup untuk service yang berjalan terus
# (long-running process / worker / bot polling).
#
# Kalau generate_signal() dipanggil dari lingkungan
# serverless / setiap request selalu proses baru
# (misal setiap panggilan = cold start baru), cache ini
# TIDAK akan bertahan antar panggilan, dan rate-limit
# jam-an harus dipindah ke penyimpanan persisten
# (file/DB/Redis) di luar modul ini.
#
# FIX #3 (PENTING):
# Sebelumnya "segar" HANYA dicek dari selisih menit murni
# terhadap generated_at. Ini menyebabkan signal jam 14 yang
# baru selesai digenerate beberapa menit setelah jam 14:00
# bisa dianggap "masih segar" saat scheduler mencoba
# generate signal jam 15:00 (karena selisihnya belum genap
# 60 menit) -- sehingga signal jam 14 dikirim ulang sebagai
# signal jam 15.
#
# Sekarang cache HARUS ganti begitu jam dinding berganti
# (tanggal + jam berbeda dari generated_at), terlepas dari
# elapsed minutes-nya. Elapsed-minutes tetap dipakai sebagai
# pengaman tambahan di DALAM jam yang sama.
# =========================================================

SIGNAL_INTERVAL_MINUTES = 60


def _hour_slot(
    dt: datetime,
) -> Tuple[
    int,
    int,
    int,
    int,
]:
    """
    Merepresentasikan "jam dinding" dari sebuah datetime
    sebagai tuple (tahun, bulan, hari, jam) di timezone WIB.

    Dua datetime dianggap berada di jam yang sama kalau
    tuple ini identik.
    """

    dt = _to_wib(dt)

    return (
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
    )


_LAST_SIGNAL_CACHE = {
    "signal": None,
    "generated_at": None,
}


def _cache_is_fresh(
    now: datetime,
) -> bool:

    generated_at = _LAST_SIGNAL_CACHE.get(
        "generated_at"
    )

    if generated_at is None:
        return False

    # =====================================================
    # CEK JAM DINDING
    #
    # Kalau jam sudah berganti (mis. dari 14 ke 15),
    # cache TIDAK PERNAH dianggap segar lagi, berapa pun
    # elapsed minutes-nya.
    # =====================================================

    if _hour_slot(now) != _hour_slot(generated_at):

        return False

    # =====================================================
    # CEK ELAPSED MINUTES (PENGAMAN TAMBAHAN)
    #
    # Masih di jam yang sama -> tetap hormati interval
    # menit supaya tidak spam analyze() kalau di-trigger
    # berkali-kali dalam jam yang sama.
    # =====================================================

    elapsed_minutes = (
        (now - generated_at).total_seconds()
        / 60
    )

    return elapsed_minutes < SIGNAL_INTERVAL_MINUTES


def get_cached_signal() -> Optional["TradeSignal"]:
    """
    Mengambil signal terakhir dari cache tanpa memicu
    analisa baru. Berguna untuk endpoint/handler yang
    hanya ingin menampilkan signal jam ini tanpa
    ikut memutuskan apakah harus generate baru.

    CATATAN: fungsi ini TIDAK mengecek kesegaran cache.
    Kalau dipakai untuk mengirim signal ke Telegram di
    proses/job yang terpisah dari generate_signal(),
    pastikan job tersebut memanggil generate_signal()
    (bukan get_cached_signal()) supaya rate-limiter jam
    dinding di atas ikut berlaku, dan signal jam baru
    tidak ikut memakai signal jam sebelumnya.
    """

    return _LAST_SIGNAL_CACHE.get("signal")


def force_refresh_signal(
    structure_candle_count: Optional[int] = None,
) -> "TradeSignal":
    """
    Melewati rate-limiter dan memaksa analisa baru
    walaupun belum genap 1 jam sejak signal terakhir.
    Gunakan hanya untuk keperluan manual/testing.
    """

    _LAST_SIGNAL_CACHE["generated_at"] = None

    return generate_signal(
        structure_candle_count=structure_candle_count
    )


# =========================================================
# GENERATE SIGNAL
# =========================================================

def generate_signal(
    structure_candle_count: Optional[int] = None,
) -> TradeSignal:

    now = datetime.now(WIB)

    # =====================================================
    # RATE LIMIT — 1 SIGNAL PER JAM (SELARAS JAM DINDING)
    #
    # Kalau signal terakhir masih "segar" -- yaitu masih di
    # JAM DINDING yang sama DAN belum genap 60 menit --
    # kembalikan signal yang sama alih-alih menganalisa
    # ulang. Begitu jam berganti, signal baru SELALU
    # dihasilkan meskipun signal sebelumnya baru berumur
    # beberapa menit.
    # =====================================================

    if (
        _cache_is_fresh(now)
        and _LAST_SIGNAL_CACHE["signal"] is not None
    ):

        return _LAST_SIGNAL_CACHE["signal"]

    # =====================================================
    # M5 OUTPUT
    # =====================================================

    if structure_candle_count is None:

        m5_outputsize = max(
            CANDLES_LOOKBACK,
            CANDLES_FOR_STRUCTURE + 12,
        )

    else:

        m5_outputsize = max(
            structure_candle_count + 12,
            24,
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

    # =====================================================
    # LOG MANUAL
    # =====================================================

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

    # =====================================================
    # ANALYZE M5
    # =====================================================

    m5_smc = analyze(
        structure_candles
    )

    # =====================================================
    # M5 BIAS
    #
    # Tidak lagi membatalkan signal hanya karena
    # score rendah.
    # =====================================================

    m5_bias = str(
        _get_attr(
            m5_smc,
            ["bias"],
            "",
        )
    ).lower()

    if m5_bias not in (
        "bullish",
        "bearish",
    ):

        # Fallback berdasarkan candle.
        bullish = sum(
            1
            for c in structure_candles[-5:]
            if c.is_bullish
        )

        bearish = sum(
            1
            for c in structure_candles[-5:]
            if c.is_bearish
        )

        if bullish >= bearish:

            m5_smc.bias = "bullish"

        else:

            m5_smc.bias = "bearish"

    # =====================================================
    # FETCH M1
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

        raise ValueError(
            "Tidak tersedia candle M1 CLOSED."
        )

    # =====================================================
    # CURRENT PRICE
    # =====================================================

    current_price = float(
        entry_candles[-1].close
    )

    if current_price <= 0:

        raise ValueError(
            "Harga XAUUSD tidak valid."
        )

    # =====================================================
    # RECENT DATA
    # =====================================================

    recent_m5 = (
        structure_candles[-10:]
    )

    recent_m1 = (
        entry_candles[-10:]
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

            m1_smc = temp_m1_smc

    except Exception as exc:

        print(
            "[M1 SMC] Analyzer gagal: "
            f"{exc}"
        )

        m1_smc = None

    # =====================================================
    # M1 REJECTION BOTH SIDES
    # =====================================================

    m1_low, m1_high = (
        _find_recent_swing(
            recent_m1
        )
    )

    if m1_low is None:

        m1_low = current_price

    if m1_high is None:

        m1_high = current_price

    m1_confirmation_buy = (
        _bullish_rejection(
            recent_m1,
            m1_low,
            current_price,
        )
    )

    m1_confirmation_sell = (
        _bearish_rejection(
            recent_m1,
            current_price,
            m1_high,
        )
    )

        # =====================================================
    # PROBABILITY BUY / SELL — SMC ORIGINAL
    # =====================================================

    (
        probability_buy,
        probability_sell,
    ) = _directional_probability(
        candles=recent_m5,
        smc=m5_smc,
        m1_smc=m1_smc,
        m1_confirmation_buy=(
            m1_confirmation_buy
        ),
        m1_confirmation_sell=(
            m1_confirmation_sell
        ),
    )


    # =====================================================
    # SAVE ORIGINAL SMC PROBABILITY
    #
    # PENTING:
    # Probability asli SMC tetap disimpan.
    # Kita tidak mengubah engine SMC.
    # =====================================================

    smc_probability_buy = int(
        probability_buy
    )

    smc_probability_sell = int(
        probability_sell
    )


    # =====================================================
    # FUNDAMENTAL NEWS
    # =====================================================

    fundamental_news = None

    fundamental_context = (
        build_combined_fundamental_context(
            None
        )
    )


    try:

        fundamental_news = (
            get_latest_fundamental_news()
        )

        fundamental_context = (
            build_combined_fundamental_context(
                fundamental_news
            )
        )


        logger.info(
            "Fundamental loaded | "
            "available=%s | "
            "impact=%s | "
            "source=%s",
            fundamental_context.get(
                "available"
            ),
            fundamental_context.get(
                "gold_impact"
            ),
            fundamental_context.get(
                "source"
            ),
        )


    except Exception as exc:

        logger.exception(
            "Fundamental gagal dimuat: %s",
            exc,
        )


        # =================================================
        # JIKA FUNDAMENTAL ERROR
        #
        # SIGNAL SMC TETAP BERJALAN NORMAL.
        # =================================================

        fundamental_news = None

        fundamental_context = (
            build_combined_fundamental_context(
                None
            )
        )


    # =====================================================
    # COMBINED SMC + FUNDAMENTAL
    #
    # FIX (PENTING):
    # Sebelumnya fungsi ini dipanggil dengan nama parameter
    # yang TIDAK COCOK dengan definisi combine_smc_and_
    # fundamental() di combined_service.py (smc_bias,
    # probability_buy, probability_sell, fundamental).
    # Karena fungsi punya **kwargs, tidak ada error yang
    # muncul -- tapi smc_probability_buy/sell dan
    # fundamental_context di dalam fungsi selalu None,
    # sehingga hasilnya selalu netral 50/50, lalu tie-
    # breaker lama selalu memilih BUY.
    #
    # Sekarang dipanggil dengan nama parameter yang BENAR:
    #   smc_result             -> objek/dict SMC (untuk bias)
    #   smc_probability_buy    -> probability SMC asli
    #   smc_probability_sell   -> probability SMC asli
    #   fundamental_context    -> context fundamental
    # =====================================================

    try:

        combined_result = (
            combine_smc_and_fundamental(

                smc_result=m5_smc,

                smc_probability_buy=(
                    smc_probability_buy
                ),

                smc_probability_sell=(
                    smc_probability_sell
                ),

                fundamental_context=(
                    fundamental_context
                ),

            )
        )


    except Exception as exc:

        logger.exception(
            "Combined analysis gagal: %s",
            exc,
        )


        # =================================================
        # FALLBACK
        #
        # Jika Combined error,
        # kembali 100% ke SMC lama.
        # =================================================

        combined_result = {

            "bias": (
                "BUY"
                if smc_probability_buy
                >= smc_probability_sell
                else "SELL"
            ),

            "probability_buy": (
                smc_probability_buy
            ),

            "probability_sell": (
                smc_probability_sell
            ),

            "smc_probability_buy": (
                smc_probability_buy
            ),

            "smc_probability_sell": (
                smc_probability_sell
            ),

            "fundamental_impact": (
                "NEUTRAL"
            ),

            "fundamental_available": False,

            "fundamental_weight": 0,

            "reasons": [],

        }


    # =====================================================
    # GET COMBINED PROBABILITY
    # =====================================================

    probability_buy = int(
        combined_result.get(
            "probability_buy",
            smc_probability_buy,
        )
    )

    probability_sell = int(
        combined_result.get(
            "probability_sell",
            smc_probability_sell,
        )
    )


    # =====================================================
    # SAFETY CLAMP
    # =====================================================

    probability_buy = max(
        0,
        min(
            100,
            probability_buy,
        ),
    )

    probability_sell = max(
        0,
        min(
            100,
            probability_sell,
        ),
    )


    # =====================================================
    # FINAL DIRECTION
    #
    # FIX (PENTING):
    # Sebelumnya arah akhir DIHITUNG ULANG dari
    # probability_buy/sell yang sudah dibulatkan memakai
    # _choose_direction(), yang tie-breaker-nya diam-diam
    # selalu memilih "bullish" saat seri (>=). Ini membuat
    # bug parameter di atas tidak kelihatan, karena hasilnya
    # selalu konsisten BUY, bukan error.
    #
    # Sekarang kita pakai LANGSUNG bias yang sudah diputuskan
    # oleh combine_smc_and_fundamental(), karena tie-breaker
    # DI SANA memakai smc_probability_buy/sell ASLI (bukan
    # hasil gabungan yang sudah dibulatkan) sebagai penentu,
    # yang lebih akurat mencerminkan struktur market. Fungsi
    # _choose_direction() hanya dipakai sebagai fallback kalau
    # combined_result ternyata tidak mengandung key "bias".
    # =====================================================

    combined_bias_str = combined_result.get(
        "bias",
        None,
    )

    if combined_bias_str == "BUY":

        final_bias = "bullish"

    elif combined_bias_str == "SELL":

        final_bias = "bearish"

    else:

        # Fallback defensif -- seharusnya tidak pernah
        # terpakai selama combine_smc_and_fundamental()
        # selalu mengembalikan key "bias".
        final_bias = _choose_direction(
            probability_buy,
            probability_sell,
        )


    # =====================================================
    # FORCE FINAL BIAS INTO SMC
    #
    # Ini tetap mengikuti struktur lama.
    # =====================================================

    m5_smc.bias = final_bias


    # =====================================================
    # COMBINED REASONS
    # =====================================================

    combined_reasons = (
        combined_result.get(
            "reasons",
            []
        )
    )


    if not isinstance(
        combined_reasons,
        list,
    ):

        combined_reasons = []


    # =====================================================
    # BEST ZONE
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


    # =====================================================
    # ZONE
    # =====================================================

    zone_price = float(
        selected_zone["price"]
    )

    zone_type = selected_zone[
        "type"
    ]

    fill_status = selected_zone[
        "status"
    ]

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
    # MAKE ZONE MATCH FINAL BIAS
    # =====================================================

    if final_bias == "bullish":

        if zone_price >= current_price:

            zone_width = (
                _pips_to_price(10)
            )

            zone_high = current_price

            zone_low = (
                current_price
                - zone_width
            )

            zone_price = (
                zone_low
                + zone_high
            ) / 2

            zone_type = (
                "Demand"
            )

            zone_timeframe = "M5"

    else:

        if zone_price <= current_price:

            zone_width = (
                _pips_to_price(10)
            )

            zone_low = current_price

            zone_high = (
                current_price
                + zone_width
            )

            zone_price = (
                zone_low
                + zone_high
            ) / 2

            zone_type = (
                "Supply"
            )

            zone_timeframe = "M5"

    # =====================================================
    # ENTRY PRICE — REALTIME
    # =====================================================

    # Entry selalu menggunakan harga market saat ini.
    # OB / FVG tidak lagi digunakan sebagai harga entry.

    entry_price = current_price


    # =====================================================
    # ENTRY ORDER — REALTIME
    # =====================================================

    # Tidak ada lagi Buy Limit / Sell Limit.
    # Semua signal menggunakan market entry.

    order_type = "Market"

    is_pending = False


    # =====================================================
    # SWING — DIHITUNG DI SINI (SEBELUM RISK)
    #
    # Dipindah ke atas karena _calculate_risk sekarang
    # butuh swing_low/swing_high sebagai target TP
    # berbasis struktur, bukan lagi pip tetap.
    # =====================================================

    (
        swing_type,
        swing_low,
        swing_high,
    ) = _classify_swings(
        structure_candles
    )


    # =====================================================
    # RISK — ANALYSIS BASED
    # =====================================================

    (
        sl,
        tp1,
        tp2,
        rr_tp1,
        rr_tp2,
    ) = _calculate_risk(
        bias=final_bias,
        entry_price=entry_price,
        zone_low=zone_low,
        zone_high=zone_high,
        candles=recent_m5,
        swing_low=swing_low,
        swing_high=swing_high,
        probability=(
            probability_buy
            if final_bias == "bullish"
            else probability_sell
        ),
    )

    # =====================================================
    # SL/TP DISPLAY DISTANCE (PIP)
    #
    # Dihitung dari hasil analisa di atas, BUKAN dari
    # SL_PIPS/TP1_PIPS/TP2_PIPS config lagi. Config hanya
    # dipakai sebagai batas minimum di dalam _calculate_risk.
    # =====================================================

    sl_pips_actual = int(
        round(
            _price_to_pips(
                abs(entry_price - sl)
            )
        )
    )

    tp1_pips_actual = int(
        round(
            _price_to_pips(
                abs(tp1 - entry_price)
            )
        )
    )

    tp2_pips_actual = int(
        round(
            _price_to_pips(
                abs(tp2 - entry_price)
            )
        )
    )


    # =====================================================
    # STRUCTURE
    # =====================================================

    structure_event = (
        _get_structure_event(
            m5_smc,
            structure_candles,
        )
    )

    (
        structure_low,
        structure_high,
    ) = _get_structure_range(
        structure_candles,
        structure_event,
    )


    # =====================================================
    # LIQUIDITY
    # =====================================================

    (
        liquidity_type,
        liquidity_price,
        liquidity_low,
        liquidity_high,
    ) = _get_liquidity(
        structure_candles,
        final_bias,
    )


    # =====================================================
    # OB
    # =====================================================

    (
        ob_low,
        ob_high,
    ) = _extract_best_ob(
        m5_smc
    )

    # =====================================================
    # FVG
    # =====================================================

    (
        fvg_low,
        fvg_high,
    ) = _extract_best_fvg(
        m5_smc
    )

    # =====================================================
    # DEMAND / SUPPLY
    # =====================================================

    demand_low = None
    demand_high = None

    supply_low = None
    supply_high = None

    if final_bias == "bullish":

        demand_low = zone_low
        demand_high = zone_high

    else:

        supply_low = zone_low
        supply_high = zone_high

    # =====================================================
    # FINAL M1 CONFIRMATION
    # =====================================================

    m1_confirmation = (
        m1_confirmation_buy
        if final_bias == "bullish"
        else m1_confirmation_sell
    )

    # =====================================================
    # ENTRY DESCRIPTION
    # =====================================================

    entry_type = (
        _build_entry_description(
            order_type=order_type,
            is_pending=is_pending,
            current_price=current_price,
            entry_price=entry_price,
            zone_type=zone_type,
        )
    )

    # =====================================================
    # ENTRY REASON BANK
    # =====================================================

    reason_text = get_entry_reason(
        bias=final_bias,
        zone_type=zone_type,
        is_pending=is_pending,
        fill_status=fill_status,
        seed=(
            f"{now.isoformat()}-"
            f"{zone_type}-"
            f"{zone_timeframe}-"
            f"{final_bias}-"
            f"{fill_status}"
        ),
    )

    # =====================================================
    # REASONS
    # =====================================================

    reasons = []

    # =====================================================
    # SIGNAL DECISION
    # =====================================================

    reasons.append(
        (
            f"Probability tertinggi: "
            f"BUY {probability_buy}% vs "
            f"SELL {probability_sell}%. "
            f"Arah dipilih: "
            f"{'BUY' if final_bias == 'bullish' else 'SELL'}."
        )
    )

    # =====================================================
    # COMBINED (SMC + FUNDAMENTAL) BREAKDOWN
    #
    # FIX: reasons dari combine_smc_and_fundamental() kini
    # benar-benar mencerminkan angka yang dipakai (karena
    # parameter yang dikirim sudah benar), jadi kita
    # sertakan supaya member bisa melihat breakdown SMC vs
    # Fundamental secara transparan.
    # =====================================================

    for reason in combined_reasons:

        reasons.append(
            reason
        )

    # =====================================================
    # STRUCTURE
    # =====================================================

    reasons.append(
        (
            f"Struktur M5: {structure_event}. "
            f"Range struktur sekitar "
            f"{_price_display(structure_low)} - "
            f"{_price_display(structure_high)}."
        )
    )

    # =====================================================
    # SWING
    # =====================================================

    reasons.append(
        (
            f"Swing M5: {swing_type}. "
            f"Area swing "
            f"{_price_display(swing_low)} - "
            f"{_price_display(swing_high)}."
        )
    )

    # =====================================================
    # OB
    # =====================================================

    if (
        ob_low is not None
        and ob_high is not None
    ):

        reasons.append(
            (
                f"Order Block M5 berada di "
                f"{_price_display(ob_low)} - "
                f"{_price_display(ob_high)}."
            )
        )

    else:

        reasons.append(
            "Order Block M5 tidak terdeteksi kuat; "
            "Demand/Supply digunakan sebagai fallback."
        )

    # =====================================================
    # FVG
    # =====================================================

    if (
        fvg_low is not None
        and fvg_high is not None
    ):

        reasons.append(
            (
                f"FVG M5 berada di "
                f"{_price_display(fvg_low)} - "
                f"{_price_display(fvg_high)}."
            )
        )

    else:

        reasons.append(
            "FVG M5 tidak tersedia pada struktur terakhir."
        )

    # =====================================================
    # LIQUIDITY
    # =====================================================

    reasons.append(
        (
            f"Liquidity: {liquidity_type}. "
            f"Area liquidity sekitar "
            f"{_price_display(liquidity_low)} - "
            f"{_price_display(liquidity_high)}."
        )
    )

    # =====================================================
    # ENTRY AREA
    # =====================================================

    reasons.append(
        (
            f"Entry Area {zone_type} {zone_timeframe}: "
            f"{_price_display(zone_low)} - "
            f"{_price_display(zone_high)}."
        )
    )

    # =====================================================
    # CURRENT MARKET
    # =====================================================

    reasons.append(
        (
            f"Market sekarang berada di "
            f"{_price_display(current_price)}."
        )
    )

    # =====================================================
    # PENDING EXPLANATION
    # =====================================================

    if order_type == "Buy Limit":

        reasons.append(
            (
                f"BUY LIMIT ditempatkan di sekitar "
                f"{_price_display(entry_price)}. "
                f"Tunggu market turun dari "
                f"{_price_display(current_price)} "
                f"menuju area entry, kemudian BUY."
            )
        )

    elif order_type == "Sell Limit":

        reasons.append(
            (
                f"SELL LIMIT ditempatkan di sekitar "
                f"{_price_display(entry_price)}. "
                f"Tunggu market naik dari "
                f"{_price_display(current_price)} "
                f"menuju area entry, kemudian SELL."
            )
        )

    else:

        reasons.append(
            (
                f"Market entry digunakan karena harga "
                f"sudah berada dekat dengan area entry "
                f"{_price_display(entry_price)}."
            )
        )

    # =====================================================
    # M1
    # =====================================================

    if m1_confirmation:

        reasons.append(
            (
                f"M1 memberikan rejection "
                f"{'bullish' if final_bias == 'bullish' else 'bearish'} "
                "sebagai timing tambahan."
            )
        )

    else:

        reasons.append(
            (
                "M1 belum memberikan rejection yang kuat. "
                "Karena engine harus tetap menghasilkan signal, "
                "probability disesuaikan tanpa membatalkan setup."
            )
        )

    # =====================================================
    # ENTRY BANK
    # =====================================================

    reasons.append(
        reason_text
    )

    # =====================================================
    # EDUCATION
    # =====================================================

    reasons.append(
        _build_educational_reason(
            bias=final_bias,
            zone_type=zone_type,
            zone_timeframe=zone_timeframe,
            fill_status=fill_status,
            m1_confirmation=m1_confirmation,
            is_pending=is_pending,
        )
    )

    # =====================================================
    # RR
    # =====================================================

    reasons.append(
        (
            f"SL/TP dihitung dari analisa (zona entry + "
            f"volatilitas candle + target swing), bukan "
            f"pip tetap. Risk/Reward: "
            f"TP1 1:{rr_tp1:.2f}, "
            f"TP2 1:{rr_tp2:.2f}."
        )
    )

    # =====================================================
    # SESSION
    # =====================================================

    (
        session_name,
        session_note,
    ) = _get_session_info(
        now
    )

    try:

        extra_note = get_session_extra_note(
            session_name=session_name,
            seed=(
                f"{now.isoformat()}-"
                f"{session_name}"
            ),
        )

    except Exception:

        extra_note = ""

    if extra_note:

        session_note = (
            f"{session_note} "
            f"{extra_note}"
        )

    # =====================================================
    # RETURN
    # =====================================================

    signal = TradeSignal(

        timestamp=now,

        bias=final_bias,

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

        probability=(
            probability_buy
            if final_bias == "bullish"
            else probability_sell
        ),

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

        current_price=round(
            current_price,
            2,
        ),

        probability_buy=(
            probability_buy
        ),

        probability_sell=(
            probability_sell
        ),

        structure_event=(
            structure_event
        ),

        structure_price_low=(
            structure_low
        ),

        structure_price_high=(
            structure_high
        ),

        swing_type=swing_type,

        swing_low=swing_low,

        swing_high=swing_high,

        liquidity_type=(
            liquidity_type
        ),

        liquidity_price=(
            liquidity_price
        ),

        liquidity_low=(
            liquidity_low
        ),

        liquidity_high=(
            liquidity_high
        ),

        demand_low=demand_low,

        demand_high=demand_high,

        supply_low=supply_low,

        supply_high=supply_high,

        fvg_low=fvg_low,

        fvg_high=fvg_high,

        ob_low=ob_low,

        ob_high=ob_high,

        sl_pips=sl_pips_actual,

        tp1_pips=tp1_pips_actual,

        tp2_pips=tp2_pips_actual,
    )

    # =====================================================
    # SIMPAN KE CACHE (RATE LIMIT 1 JAM, SELARAS JAM DINDING)
    # =====================================================

    _LAST_SIGNAL_CACHE["signal"] = signal
    _LAST_SIGNAL_CACHE["generated_at"] = now

    return signal


# =========================================================
# BUILD SIGNAL COMPATIBILITY
# =========================================================

def build_signal(
    structure_candle_count: Optional[int] = None,
) -> TradeSignal:

    return generate_signal(
        structure_candle_count=(
            structure_candle_count
        )
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

        # =================================================
        # CONTOH:
        # 4005.72 -> 4005
        # 3998.91 -> 3998
        # =================================================

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
# RANGE DISPLAY
# =========================================================

def _range_display(
    low,
    high,
) -> str:

    if low is None or high is None:
        return "-"

    return (
        f"{_price_display(low)} - "
        f"{_price_display(high)}"
    )


# =========================================================
# TEXT WRAPPER
# =========================================================

def _wrap_reason(
    text: str,
    width: int = 42,
) -> str:

    words = str(
        text
    ).split(" ")

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
# FORMAT SIGNAL — SHORT
#
# Format utama untuk member.
#
# KONSEP:
# - ENTRY = harga realtime
# - Tidak ada Buy Limit / Sell Limit
# - Tidak ada "tunggu turun/naik"
# - Tidak menampilkan Market sekarang
# - OB/FVG ditampilkan sebagai LOW RISK ZONE
# - SL / TP dihitung dari ANALISA (zona + volatilitas +
#   target struktur), bukan pip tetap dari config.
# =========================================================

def format_signal_short(
    sig: TradeSignal,
) -> str:

    # =====================================================
    # DIRECTION
    # =====================================================

    if sig.bias == "bullish":

        emoji = "🟢"
        direction_text = "BUY"

    else:

        emoji = "🔴"
        direction_text = "SELL"


    # =====================================================
    # TIME
    # =====================================================

    time_str = (
        sig.timestamp.strftime(
            "%d-%m-%Y %H:%M"
        )
    )


    # =====================================================
    # ENTRY REALTIME
    #
    # PENTING:
    # Entry sekarang menggunakan current_price,
    # bukan lagi entry dari pending order / zona.
    # =====================================================

    realtime_entry = sig.current_price


    # =====================================================
    # LOW RISK ZONE
    # =====================================================

    zone_text = _range_display(
        sig.zone_low,
        sig.zone_high
    )


    # =====================================================
    # ZONE TYPE
    # =====================================================

    zone_type = (
        sig.zone_type
        if sig.zone_type
        else "SMC Zone"
    )


    # =====================================================
    # LINES
    # =====================================================

    lines = [

        "🚨 *XAU AI SMC REAL*",

        "━━━━━━━━━━━━━━━━━━",

        f"{emoji} *{direction_text} XAUUSD*",

        f"🕐 *{time_str} WIB*",

        (
            f"🏆 Probability tertinggi: "
            f"*{sig.probability}%* "
            f"→ *{direction_text}*"
        ),

        "",

        # =============================================
        # REALTIME ENTRY
        # =============================================

        (
            f"🎯 ENTRY: "
            f"`{_price_display(realtime_entry)}`"
        ),

        "",

        # =============================================
        # SL / TP — ANALYSIS BASED
        # =============================================

        (
            f"🛑 SL  : "
            f"`{_price_display(sig.sl)}` "
            f"(-{sig.sl_pips} pip)"
        ),

        (
            f"✅ TP1 : "
            f"`{_price_display(sig.tp1)}` "
            f"(+{sig.tp1_pips} pip)"
        ),

        (
            f"🏆 TP2 : "
            f"`{_price_display(sig.tp2)}` "
            f"(+{sig.tp2_pips} pip)"
        ),

        (
            f"📐 RR  : "
            f"TP1 1:{sig.rr_tp1:.2f} | "
            f"TP2 1:{sig.rr_tp2:.2f}"
        ),

        "━━━━━━━━━━━━━━━━━━",

        # =============================================
        # LOW RISK ZONE
        # =============================================

        "",

        "🛡 *LOW RISK ZONE*",

        (
            f"📍 `{zone_text}`"
        ),

        (
            f"🧩 *{zone_type}*"
        ),

        "━━━━━━━━━━━━━━━━━━",

        "",

        # =============================================
        # DETAIL CTA
        # =============================================

        "👇 Klik tombol di bawah untuk mengetahui Detail Analisanya",

        "",

        # =============================================
        # DISCLAIMER
        # =============================================

        (
            "⚠️ _Probability adalah confidence "
            "analisa AI/SMC, bukan jaminan profit._"
        ),

        (
            "_Selalu gunakan money management pribadi._"
        ),

        "",

        (
            "🤖 _XAU AI SMC REAL — "
            "AI Agent Gold_"
        ),
    ]


    return "\n".join(
        lines
    )

# =========================================================
# FORMAT SIGNAL — DETAIL (BARU)
#
# Berisi seluruh breakdown analisa SMC:
# struktur, swing, OB, FVG, demand/supply,
# liquidity, M1 timing, sesi, alasan AI,
# dan instruksi pending (jika ada).
#
# Dikirim terpisah saat member klik tombol
# "Detail Analisa".
# =========================================================

def format_signal_detail(
    sig: TradeSignal,
) -> str:

    direction_text = (
        "BUY"
        if sig.bias == "bullish"
        else "SELL"
    )

    lines = [

        f"📊 *Detail Analisa — {direction_text} XAUUSD*",

        "━━━━━━━━━━━━━━━━━━",

        "",

        # ================================================
        # MARKET NOW
        # ================================================

        "📍 *MARKET & ENTRY MAP*",

        (
            f"💰 Market sekarang : "
            f"`{_price_display(sig.current_price)}`"
        ),

        (
            f"🎯 Entry Area      : "
            f"`{_range_display(sig.zone_low, sig.zone_high)}`"
        ),

        (
            f"🧩 Zona             : "
            f"*{sig.zone_type or '-'} "
            f"{sig.zone_timeframe}*"
        ),

        (
            f"📌 Status zona      : "
            f"*{sig.fill_status}*"
        ),

        "",

        # ================================================
        # SL / TP — ANALYSIS BASED
        # ================================================

        "🎯 *SL / TP (ANALISA)*",

        (
            f"🛑 SL  : `{_price_display(sig.sl)}` "
            f"(-{sig.sl_pips} pip)"
        ),

        (
            f"✅ TP1 : `{_price_display(sig.tp1)}` "
            f"(+{sig.tp1_pips} pip)"
        ),

        (
            f"🏆 TP2 : `{_price_display(sig.tp2)}` "
            f"(+{sig.tp2_pips} pip)"
        ),

        (
            f"📐 RR  : TP1 1:{sig.rr_tp1:.2f} | "
            f"TP2 1:{sig.rr_tp2:.2f}"
        ),

        "",

        # ================================================
        # STRUCTURE
        # ================================================

        "🧠 *M5 SMC STRUCTURE*",

        (
            f"🔀 Struktur : "
            f"*{sig.structure_event}*"
        ),

        (
            f"📐 Area BOS/CHoCH : "
            f"`{_range_display(sig.structure_price_low, sig.structure_price_high)}`"
        ),

        (
            f"🔺 Swing : "
            f"*{sig.swing_type}*"
        ),

        (
            f"📏 Swing Range : "
            f"`{_range_display(sig.swing_low, sig.swing_high)}`"
        ),

        "",

        # ================================================
        # ORDER BLOCK
        # ================================================

        "🏦 *ORDER BLOCK*",

        (
            f"OB M5 : "
            f"`{_range_display(sig.ob_low, sig.ob_high)}`"
        ),

        "",

        # ================================================
        # DEMAND SUPPLY
        # ================================================

        "🟦 *DEMAND / SUPPLY*",

        (
            f"Demand : "
            f"`{_range_display(sig.demand_low, sig.demand_high)}`"
        ),

        (
            f"Supply : "
            f"`{_range_display(sig.supply_low, sig.supply_high)}`"
        ),

        "",

        # ================================================
        # FVG
        # ================================================

        "🕳 *FAIR VALUE GAP*",

        (
            f"FVG M5 : "
            f"`{_range_display(sig.fvg_low, sig.fvg_high)}`"
        ),

        "",

        # ================================================
        # LIQUIDITY
        # ================================================

        "💧 *LIQUIDITY*",

        (
            f"Jenis : "
            f"*{sig.liquidity_type}*"
        ),

        (
            f"Liquidity Range : "
            f"`{_range_display(sig.liquidity_low, sig.liquidity_high)}`"
        ),

        (
            f"Liquidity utama : "
            f"`{_price_display(sig.liquidity_price)}`"
        ),

        "",

        # ================================================
        # M1
        # ================================================

        "🔎 *M1 ENTRY TIMING*",

        (
            f"M1 Confirmation : "
            f"*{'YES' if sig.m1_confirmation else 'NO'}*"
        ),

        (
            f"Timeframe zona : "
            f"*{sig.zone_timeframe}*"
        ),

        "",

        # ================================================
        # SESSION
        # ================================================

        (
            f"🕐 *Sesi {sig.session_name}*"
        ),

        _wrap_reason(
            sig.session_note
        ),

        "",

        # ================================================
        # REASONS
        # ================================================

        "🧠 *ALASAN & ANALISA AI*",
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

            "⏳ *PENDING INSTRUCTION*",

            _wrap_reason(
                (
                    f"Pasang {sig.order_type} "
                    f"di `{_price_display(sig.entry_price)}`."
                )
            ),

            _wrap_reason(
                (
                    f"Market sekarang "
                    f"`{_price_display(sig.current_price)}`. "
                    f"Jangan mengejar harga."
                )
            ),

            _wrap_reason(
                (
                    f"Jika harga tidak menyentuh "
                    f"entry dalam "
                    f"{sig.pending_timeout_minutes} menit, "
                    "anggap signal EXPIRED."
                )
            ),

        ]

    # =====================================================
    # FOOTER
    # =====================================================

    lines += [

        "",

        "━━━━━━━━━━━━━━━━━━",

        (
            f"📏 Radius zona: "
            f"*{MAX_ZONE_DISTANCE_PIPS} pip*"
        ),

        (
            f"⏳ Pending timeout: "
            f"*{PENDING_ORDER_TIMEOUT_MINUTES} menit*"
        ),

        (
            f"🕐 Interval signal: "
            f"*{SIGNAL_INTERVAL_MINUTES} menit*"
        ),
    ]

    return "\n".join(
        lines
    )


# =========================================================
# FORMAT SIGNAL MESSAGE (LAMA — tetap dipertahankan
# untuk compatibility jika masih dipanggil di tempat lain)
# =========================================================

def format_signal_message(
    sig: TradeSignal,
) -> str:

    # =====================================================
    # DIRECTION
    # =====================================================

    if sig.bias == "bullish":

        arrow = "🟢 BUY"

        direction_text = (
            "BUY"
        )

    else:

        arrow = "🔴 SELL"

        direction_text = (
            "SELL"
        )

    # =====================================================
    # TIME
    # =====================================================

    time_str = (
        sig.timestamp.strftime(
            "%d %b %Y, %H:%M WIB"
        )
    )

    # =====================================================
    # ENTRY INSTRUCTION
    # =====================================================

    if sig.order_type == "Buy Limit":

        instruction = (
            f"⏳ Market sekarang "
            f"`{_price_display(sig.current_price)}`\n"
            f"⬇️ Tunggu turun ke "
            f"`{_price_display(sig.entry_price)}`\n"
            f"🎯 Lalu lakukan BUY"
        )

    elif sig.order_type == "Sell Limit":

        instruction = (
            f"⏳ Market sekarang "
            f"`{_price_display(sig.current_price)}`\n"
            f"⬆️ Tunggu naik ke "
            f"`{_price_display(sig.entry_price)}`\n"
            f"🎯 Lalu lakukan SELL"
        )

    else:

        instruction = (
            f"⚡ Market entry sekitar "
            f"`{_price_display(sig.entry_price)}`"
        )

    # =====================================================
    # SIGNAL UTAMA
    #
    # SENGAJA PALING ATAS
    # =====================================================

    lines = [

        "🚨 *XAU AI SMC REAL*",


        # ================================================
        # SIGNAL PALING ATAS
        # ================================================

        "━━━━━━━━━━━━━━━━━━",

        f"{arrow} *{direction_text} XAUUSD*",

        (
            f"🕐 *{datetime.now(WIB).strftime('%d-%m-%Y %H:%M')} WIB*"
        ),

        (
            f"🏆 Probability tertinggi: "
            f"*{sig.probability}%* "
            f"→ *{direction_text}*"
        ),

        "",

        (
            f"🎯 ENTRY: "
            f"`{_price_display(sig.entry_price)}`"
        ),

        (
            f"📌 ORDER: "
            f"*{sig.order_type}*"
        ),

        "",

        instruction,

        "━━━━━━━━━━━━━━━━━━",

        "",

        # ================================================
        # RISK — ANALYSIS BASED
        # ================================================

        (
            f"🛑 SL  : "
            f"`{_price_display(sig.sl)}` "
            f"(-{sig.sl_pips} pip)"
        ),

        (
            f"✅ TP1 : "
            f"`{_price_display(sig.tp1)}` "
            f"(+{sig.tp1_pips} pip)"
        ),

        (
            f"✅ TP2 : "
            f"`{_price_display(sig.tp2)}` "
            f"(+{sig.tp2_pips} pip)"
        ),

        (
            f"📐 RR  : "
            f"TP1 1:{sig.rr_tp1:.2f} | "
            f"TP2 1:{sig.rr_tp2:.2f}"
        ),

        "",

        # ================================================
        # MARKET NOW
        # ================================================

        "📍 *MARKET & ENTRY MAP*",

        (
            f"💰 Market sekarang : "
            f"`{_price_display(sig.current_price)}`"
        ),

        (
            f"🎯 Entry Area      : "
            f"`{_range_display(sig.zone_low, sig.zone_high)}`"
        ),

        (
            f"🧩 Zona             : "
            f"*{sig.zone_type or '-'} "
            f"{sig.zone_timeframe}*"
        ),

        (
            f"📌 Status zona      : "
            f"*{sig.fill_status}*"
        ),

        "",

        # ================================================
        # STRUCTURE
        # ================================================

        "🧠 *M5 SMC STRUCTURE*",

        (
            f"🔀 Struktur : "
            f"*{sig.structure_event}*"
        ),

        (
            f"📐 Area BOS/CHoCH : "
            f"`{_range_display(sig.structure_price_low, sig.structure_price_high)}`"
        ),

        (
            f"🔺 Swing : "
            f"*{sig.swing_type}*"
        ),

        (
            f"📏 Swing Range : "
            f"`{_range_display(sig.swing_low, sig.swing_high)}`"
        ),

        "",

        # ================================================
        # ORDER BLOCK
        # ================================================

        "🏦 *ORDER BLOCK*",

        (
            f"OB M5 : "
            f"`{_range_display(sig.ob_low, sig.ob_high)}`"
        ),

        "",

        # ================================================
        # DEMAND SUPPLY
        # ================================================

        "🟦 *DEMAND / SUPPLY*",

        (
            f"Demand : "
            f"`{_range_display(sig.demand_low, sig.demand_high)}`"
        ),

        (
            f"Supply : "
            f"`{_range_display(sig.supply_low, sig.supply_high)}`"
        ),

        "",

        # ================================================
        # FVG
        # ================================================

        "🕳 *FAIR VALUE GAP*",

        (
            f"FVG M5 : "
            f"`{_range_display(sig.fvg_low, sig.fvg_high)}`"
        ),

        "",

        # ================================================
        # LIQUIDITY
        # ================================================

        "💧 *LIQUIDITY*",

        (
            f"Jenis : "
            f"*{sig.liquidity_type}*"
        ),

        (
            f"Liquidity Range : "
            f"`{_range_display(sig.liquidity_low, sig.liquidity_high)}`"
        ),

        (
            f"Liquidity utama : "
            f"`{_price_display(sig.liquidity_price)}`"
        ),

        "",

        # ================================================
        # M1
        # ================================================

        "🔎 *M1 ENTRY TIMING*",

        (
            f"M1 Confirmation : "
            f"*{'YES' if sig.m1_confirmation else 'NO'}*"
        ),

        (
            f"Timeframe zona : "
            f"*{sig.zone_timeframe}*"
        ),

        "",

        # ================================================
        # SESSION
        # ================================================

        (
            f"🕐 *Sesi {sig.session_name}*"
        ),

        _wrap_reason(
            sig.session_note
        ),

        "",


        # ================================================
        # REASONS
        # ================================================

        "🧠 *ALASAN & ANALISA AI*",
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

            "⏳ *PENDING INSTRUCTION*",

            _wrap_reason(
                (
                    f"Pasang {sig.order_type} "
                    f"di `{_price_display(sig.entry_price)}`."
                )
            ),

            _wrap_reason(
                (
                    f"Market sekarang "
                    f"`{_price_display(sig.current_price)}`. "
                    f"Jangan mengejar harga."
                )
            ),

            _wrap_reason(
                (
                    f"Jika harga tidak menyentuh "
                    f"entry dalam "
                    f"{sig.pending_timeout_minutes} menit, "
                    "anggap signal EXPIRED."
                )
            ),

        ]

    # =====================================================
    # FOOTER
    # =====================================================

    lines += [

        "",

        "━━━━━━━━━━━━━━━━━━",

        (
            f"📏 Radius zona: "
            f"*{MAX_ZONE_DISTANCE_PIPS} pip*"
        ),

        (
            f"⏳ Pending timeout: "
            f"*{PENDING_ORDER_TIMEOUT_MINUTES} menit*"
        ),

        (
            f"🕐 Interval signal: "
            f"*{SIGNAL_INTERVAL_MINUTES} menit*"
        ),

        "",

        (
            "⚠️ _Probability adalah confidence "
            "analisa AI/SMC, bukan jaminan profit._"
        ),

        (
            "_Selalu gunakan money management pribadi._"
        ),

        "",

        (
            "🤖 _XAU AI SMC REAL — "
            "AI Agent Gold_"
        ),
    ]

    return "\n".join(
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
        "====================================\n"
        "XAU AI SMC REAL DEBUG\n"
        "====================================\n"
        f"Bias              : {sig.bias}\n"
        f"Current Price     : {sig.current_price}\n"
        f"Entry             : {sig.entry_price}\n"
        f"Order             : {sig.order_type}\n"
        f"Pending           : {sig.is_pending}\n"
        f"Probability BUY   : {sig.probability_buy}%\n"
        f"Probability SELL  : {sig.probability_sell}%\n"
        f"Probability FINAL : {sig.probability}%\n"
        f"Zone              : {sig.zone_type}\n"
        f"Zone TF           : {sig.zone_timeframe}\n"
        f"Zone Low          : {sig.zone_low}\n"
        f"Zone High         : {sig.zone_high}\n"
        f"Fill Status       : {sig.fill_status}\n"
        f"Structure Event   : {sig.structure_event}\n"
        f"Structure Low     : {sig.structure_price_low}\n"
        f"Structure High    : {sig.structure_price_high}\n"
        f"Swing Type        : {sig.swing_type}\n"
        f"Swing Low         : {sig.swing_low}\n"
        f"Swing High        : {sig.swing_high}\n"
        f"OB Low            : {sig.ob_low}\n"
        f"OB High           : {sig.ob_high}\n"
        f"Demand Low        : {sig.demand_low}\n"
        f"Demand High       : {sig.demand_high}\n"
        f"Supply Low        : {sig.supply_low}\n"
        f"Supply High       : {sig.supply_high}\n"
        f"FVG Low           : {sig.fvg_low}\n"
        f"FVG High          : {sig.fvg_high}\n"
        f"Liquidity Type    : {sig.liquidity_type}\n"
        f"Liquidity Price   : {sig.liquidity_price}\n"
        f"Liquidity Low     : {sig.liquidity_low}\n"
        f"Liquidity High    : {sig.liquidity_high}\n"
        f"M1 Confirm        : {sig.m1_confirmation}\n"
        f"SL                : {sig.sl} ({sig.sl_pips} pip)\n"
        f"TP1               : {sig.tp1} ({sig.tp1_pips} pip)\n"
        f"TP2               : {sig.tp2} ({sig.tp2_pips} pip)\n"
        f"RR TP1            : {sig.rr_tp1}\n"
        f"RR TP2            : {sig.rr_tp2}\n"
        f"Session           : {sig.session_name}\n"
        f"Radius            : {MAX_ZONE_DISTANCE_PIPS} pip\n"
        f"Timeout           : {sig.pending_timeout_minutes} min\n"
        f"Signal interval   : {SIGNAL_INTERVAL_MINUTES} min\n"
        "====================================\n"
    )

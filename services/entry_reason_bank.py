"""
ENTRY REASON BANK
=================

Bank alasan entry berbasis SMC.

Digunakan oleh:

    services.signal_builder

Function utama:

    get_entry_reason()
    get_session_extra_note()

Tujuan:
- membuat alasan signal lebih natural
- tidak mengulang kalimat yang sama terus-menerus
- menyesuaikan bias
- menyesuaikan zona
- menyesuaikan pending / market
- menyesuaikan fill status
"""

import random
from typing import Optional


# =========================================================
# BULLISH REASONS
# =========================================================

BULLISH_OB_PENDING = [

    "Struktur bullish mendukung retracement menuju Order Block demand.",

    "Harga masih berada di atas struktur demand dan OB bullish menjadi area mitigasi potensial.",

    "Order Block bullish berada di bawah harga dan masih relatif fresh untuk retest.",

    "Zona demand teridentifikasi sebagai area potensial untuk continuation bullish.",

    "Harga berpotensi melakukan retracement sebelum melanjutkan struktur naik.",

    "OB bullish menjadi area menarik untuk menunggu pullback yang lebih terukur.",

]


BULLISH_FVG_PENDING = [

    "Bullish Fair Value Gap berada di bawah harga dan berpotensi menjadi area imbalance yang diretest.",

    "Imbalance bullish masih relatif fresh dan dapat menjadi area retracement.",

    "FVG bullish memberikan area entry retracement dengan struktur yang masih mendukung buyer.",

    "Harga berpotensi mengisi kembali imbalance sebelum melanjutkan pergerakan bullish.",

    "Bullish FVG menjadi area potensial untuk menunggu re-entry buyer.",

]


BULLISH_MARKET = [

    "Buyer menunjukkan rejection di sekitar area demand sehingga entry market mulai mendapatkan konfirmasi.",

    "Rejection bullish pada M1 mendukung kemungkinan continuation dari zona demand.",

    "Harga telah melakukan retest zona dan buyer mulai menunjukkan respons.",

    "Konfirmasi M1 menunjukkan seller gagal mempertahankan tekanan di area demand.",

    "Reaksi bullish setelah retest memberikan konfirmasi tambahan untuk entry.",

    "Buyer kembali aktif setelah harga memasuki area SMC.",

]


BULLISH_PARTIAL = [

    "FVG bullish baru terisi sebagian sehingga retracement masih berpotensi berlanjut.",

    "Imbalance belum sepenuhnya termitigasi sehingga entry agresif belum disarankan.",

    "Partial fill menunjukkan harga sudah memasuki FVG namun belum memberikan konfirmasi penuh.",

    "Zona masih membutuhkan validasi tambahan sebelum entry market.",

]


# =========================================================
# BEARISH REASONS
# =========================================================

BEARISH_OB_PENDING = [

    "Struktur bearish mendukung retracement menuju Order Block supply.",

    "Harga masih berada di bawah struktur supply dan OB bearish menjadi area mitigasi potensial.",

    "Order Block bearish berada di atas harga dan masih relatif fresh untuk retest.",

    "Zona supply teridentifikasi sebagai area potensial untuk continuation bearish.",

    "Harga berpotensi melakukan retracement sebelum melanjutkan struktur turun.",

    "OB bearish menjadi area menarik untuk menunggu pullback yang lebih terukur.",

]


BEARISH_FVG_PENDING = [

    "Bearish Fair Value Gap berada di atas harga dan berpotensi menjadi area imbalance yang diretest.",

    "Imbalance bearish masih relatif fresh dan dapat menjadi area retracement.",

    "FVG bearish memberikan area entry retracement dengan struktur yang masih mendukung seller.",

    "Harga berpotensi mengisi kembali imbalance sebelum melanjutkan pergerakan bearish.",

    "Bearish FVG menjadi area potensial untuk menunggu re-entry seller.",

]


BEARISH_MARKET = [

    "Seller menunjukkan rejection di sekitar area supply sehingga entry market mulai mendapatkan konfirmasi.",

    "Rejection bearish pada M1 mendukung kemungkinan continuation dari zona supply.",

    "Harga telah melakukan retest zona dan seller mulai menunjukkan respons.",

    "Konfirmasi M1 menunjukkan buyer gagal mempertahankan tekanan di area supply.",

    "Reaksi bearish setelah retest memberikan konfirmasi tambahan untuk entry.",

    "Seller kembali aktif setelah harga memasuki area SMC.",

]


BEARISH_PARTIAL = [

    "FVG bearish baru terisi sebagian sehingga retracement masih berpotensi berlanjut.",

    "Imbalance belum sepenuhnya termitigasi sehingga entry agresif belum disarankan.",

    "Partial fill menunjukkan harga sudah memasuki FVG namun belum memberikan konfirmasi penuh.",

    "Zona masih membutuhkan validasi tambahan sebelum entry market.",

]


# =========================================================
# GENERAL
# =========================================================

GENERAL_REASONS = [

    "Analisa mempertimbangkan struktur M5 dan timing entry M1.",

    "Setup dipilih berdasarkan konfluensi struktur dan zona SMC.",

    "Entry tidak hanya mengandalkan arah harga, tetapi juga posisi terhadap zona.",

    "Harga masih berada dalam radius zona yang diperbolehkan oleh sistem.",

    "Setup mempertimbangkan hubungan antara struktur, liquidity dan area imbalance.",

    "Risk management tetap menjadi bagian utama validasi setup.",

]


# =========================================================
# SESSION NOTES
# =========================================================

SESSION_NOTES = {

    "Asian Session": [

        "Sesi Asia cenderung membentuk range yang dapat menjadi referensi liquidity untuk sesi berikutnya.",

        "Perhatikan high dan low sesi Asia karena area tersebut sering menjadi target liquidity.",

        "Volatilitas dapat lebih rendah sehingga hindari mengejar pergerakan harga.",

        "Gunakan struktur dan zona sebagai acuan utama, bukan sekadar momentum candle.",

    ],

    "London Session": [

        "Pembukaan London dapat meningkatkan volatilitas dan memicu liquidity sweep.",

        "Perhatikan kemungkinan false breakout sebelum displacement yang lebih jelas.",

        "London sering menjadi fase penting untuk validasi BOS atau CHoCH.",

        "Jika liquidity Asia tersapu, tunggu reaksi harga sebelum mengambil keputusan.",

    ],

    "New York Session": [

        "Volatilitas XAUUSD dapat meningkat ketika likuiditas New York masuk.",

        "Perhatikan displacement dan kemungkinan liquidity sweep di sekitar high/low sebelumnya.",

        "News Amerika dapat meningkatkan volatilitas sehingga ukuran risiko perlu tetap terkontrol.",

        "Konfirmasi M1 menjadi semakin penting ketika range bergerak cepat.",

    ],

    "New York Late": [

        "Pasar mulai memasuki fase akhir sesi New York sehingga continuation perlu dikonfirmasi.",

        "Waspadai exhaustion setelah pergerakan besar.",

        "Retracement dapat lebih dominan setelah volatility spike.",

        "Hindari mengejar harga jika sudah terlalu jauh dari zona SMC.",

    ],

}


# =========================================================
# DETERMINISTIC RANDOM
# =========================================================

def _choose(
    items,
    seed: Optional[str] = None,
) -> str:

    if not items:

        return ""

    if seed:

        rng = random.Random(
            str(seed)
        )

        return rng.choice(
            items
        )

    return random.choice(
        items
    )


# =========================================================
# GET ENTRY REASON
# =========================================================

def get_entry_reason(
    bias: str,
    zone_type: Optional[str],
    is_pending: bool,
    fill_status: str,
    seed: Optional[str] = None,
) -> str:
    """
    Menghasilkan alasan entry berdasarkan kondisi SMC.

    Parameter:

        bias:
            bullish / bearish

        zone_type:
            Order Block / Fair Value Gap

        is_pending:
            True jika Buy Limit / Sell Limit

        fill_status:
            untouched / partial / full

        seed:
            membuat hasil konsisten untuk signal yang sama.
    """

    bias = (
        bias or ""
    ).lower()

    zone_type = (
        zone_type or ""
    ).lower()

    fill_status = (
        fill_status or "untouched"
    ).lower()


    # =====================================================
    # PARTIAL FVG
    # =====================================================

    if (
        "fair value gap" in zone_type
        and fill_status == "partial"
    ):

        if bias == "bullish":

            return _choose(
                BULLISH_PARTIAL,
                seed,
            )

        if bias == "bearish":

            return _choose(
                BEARISH_PARTIAL,
                seed,
            )


    # =====================================================
    # MARKET
    # =====================================================

    if not is_pending:

        if bias == "bullish":

            return _choose(
                BULLISH_MARKET,
                seed,
            )

        if bias == "bearish":

            return _choose(
                BEARISH_MARKET,
                seed,
            )


    # =====================================================
    # PENDING ORDER BLOCK
    # =====================================================

    if (
        is_pending
        and "order block" in zone_type
    ):

        if bias == "bullish":

            return _choose(
                BULLISH_OB_PENDING,
                seed,
            )

        if bias == "bearish":

            return _choose(
                BEARISH_OB_PENDING,
                seed,
            )


    # =====================================================
    # PENDING FVG
    # =====================================================

    if (
        is_pending
        and "fair value gap" in zone_type
    ):

        if bias == "bullish":

            return _choose(
                BULLISH_FVG_PENDING,
                seed,
            )

        if bias == "bearish":

            return _choose(
                BEARISH_FVG_PENDING,
                seed,
            )


    # =====================================================
    # FALLBACK
    # =====================================================

    return _choose(
        GENERAL_REASONS,
        seed,
    )


# =========================================================
# SESSION EXTRA NOTE
# =========================================================

def get_session_extra_note(
    session_name: str,
    seed: Optional[str] = None,
) -> str:

    notes = SESSION_NOTES.get(
        session_name,
        [],
    )

    if not notes:

        return ""

    return _choose(
        notes,
        seed,
    )


# =========================================================
# COMPATIBILITY
# =========================================================

def get_reason(
    bias: str,
    zone_type: Optional[str] = None,
    is_pending: bool = False,
    fill_status: str = "untouched",
    seed: Optional[str] = None,
) -> str:

    return get_entry_reason(
        bias=bias,
        zone_type=zone_type,
        is_pending=is_pending,
        fill_status=fill_status,
        seed=seed,
    )

import json
import logging
import os

from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from config.settings import TIMEZONE


# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# TIMEZONE
# =========================================================

try:
    from zoneinfo import ZoneInfo

    WIB = ZoneInfo(TIMEZONE)

except Exception:

    import pytz

    WIB = pytz.timezone(TIMEZONE)


# =========================================================
# FILE
# =========================================================

DATA_DIR = "data"

DATA_FILE = os.path.join(
    DATA_DIR,
    "pending_signal.json",
)


# =========================================================
# JSON SERIALIZER
# =========================================================

def _json_safe(value: Any) -> Any:
    """
    Mengubah object Python menjadi object yang bisa
    disimpan oleh JSON.

    Support:

    - TradeSignal
    - SMCResult
    - dataclass nested
    - datetime
    - list
    - tuple
    - dict
    - primitive
    """

    # -----------------------------------------------------
    # DATACLASS
    # -----------------------------------------------------

    if is_dataclass(value):

        return _json_safe(
            asdict(value)
        )

    # -----------------------------------------------------
    # DATETIME
    # -----------------------------------------------------

    if isinstance(
        value,
        datetime,
    ):

        return value.isoformat()

    # -----------------------------------------------------
    # DICT
    # -----------------------------------------------------

    if isinstance(
        value,
        dict,
    ):

        return {
            str(key): _json_safe(val)
            for key, val in value.items()
        }

    # -----------------------------------------------------
    # LIST / TUPLE
    # -----------------------------------------------------

    if isinstance(
        value,
        (list, tuple),
    ):

        return [
            _json_safe(item)
            for item in value
        ]

    # -----------------------------------------------------
    # SET
    # -----------------------------------------------------

    if isinstance(
        value,
        set,
    ):

        return [
            _json_safe(item)
            for item in value
        ]

    # -----------------------------------------------------
    # PRIMITIVE
    # -----------------------------------------------------

    if value is None:
        return None

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):

        return value

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    return str(value)


# =========================================================
# INTERNAL LOAD
# =========================================================

def _load() -> List[Dict[str, Any]]:
    """
    Membaca pending signal dari JSON.

    Jika file belum ada / kosong / rusak,
    mengembalikan list kosong.
    """

    if not os.path.exists(
        DATA_FILE
    ):

        return []

    try:

        with open(
            DATA_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        if not isinstance(
            data,
            list,
        ):

            logger.warning(
                "Format pending_signal.json tidak valid. "
                "Reset ke list kosong."
            )

            return []

        return data

    except (
        json.JSONDecodeError,
        OSError,
    ):

        logger.exception(
            "Gagal membaca %s",
            DATA_FILE,
        )

        return []


# =========================================================
# INTERNAL SAVE
# =========================================================

def _save(
    data: List[Dict[str, Any]],
):
    """
    Menyimpan pending signal ke JSON.

    Semua object akan dikonversi menjadi
    JSON-safe terlebih dahulu.
    """

    os.makedirs(
        DATA_DIR,
        exist_ok=True,
    )

    temp_file = (
        DATA_FILE
        + ".tmp"
    )

    try:

        safe_data = _json_safe(
            data
        )

        with open(
            temp_file,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                safe_data,
                f,
                ensure_ascii=False,
                indent=4,
            )

            f.flush()

            # Pastikan data benar-benar ditulis
            os.fsync(
                f.fileno()
            )

        # Atomic replace
        os.replace(
            temp_file,
            DATA_FILE,
        )

    except Exception:

        logger.exception(
            "Gagal menyimpan %s",
            DATA_FILE,
        )

        # Bersihkan file temporary jika ada
        try:

            if os.path.exists(
                temp_file
            ):

                os.remove(
                    temp_file
                )

        except OSError:

            pass

        raise


# =========================================================
# TIME HELPERS
# =========================================================

def _now() -> datetime:
    """
    Waktu sekarang sesuai TIMEZONE config.
    """

    return datetime.now(
        WIB
    )


def _parse_datetime(
    value: Any,
) -> Optional[datetime]:
    """
    Parse datetime ISO.

    Menghasilkan timezone-aware datetime WIB.
    """

    if not value:

        return None

    # -----------------------------------------------------
    # Jika sudah datetime
    # -----------------------------------------------------

    if isinstance(
        value,
        datetime,
    ):

        dt = value

    else:

        try:

            dt = datetime.fromisoformat(
                str(value)
            )

        except (
            ValueError,
            TypeError,
        ):

            return None

    # -----------------------------------------------------
    # TIMEZONE
    # -----------------------------------------------------

    if dt.tzinfo is None:

        dt = dt.replace(
            tzinfo=WIB
        )

    else:

        dt = dt.astimezone(
            WIB
        )

    return dt


# =========================================================
# SIMPAN SIGNAL
# =========================================================

def save_pending_signal(
    signal,
    send_at: Optional[datetime] = None,
    delay_minutes: Optional[int] = None,
):
    """
    Menyimpan signal pending.

    Bisa menerima:

        TradeSignal

    atau object lain yang bisa dikonversi
    menjadi JSON-safe.

    Contoh:

        save_pending_signal(
            signal,
            delay_minutes=60,
        )
    """

    data = _load()

    now = _now()

    # =====================================================
    # TENTUKAN WAKTU KIRIM
    # =====================================================

    if send_at is not None:

        if send_at.tzinfo is None:

            send_at = send_at.replace(
                tzinfo=WIB
            )

        else:

            send_at = send_at.astimezone(
                WIB
            )

    elif delay_minutes is not None:

        send_at = (
            now
            + timedelta(
                minutes=delay_minutes
            )
        )

    else:

        send_at = now

    # =====================================================
    # KONVERSI SIGNAL
    # =====================================================

    safe_signal = _json_safe(
        signal
    )

    # =====================================================
    # DATA ITEM
    # =====================================================

    item = {

        "signal": safe_signal,

        "created_at":
            now.isoformat(),

        "send_at":
            send_at.isoformat(),

        "sent":
            False,

    }

    # =====================================================
    # APPEND
    # =====================================================

    data.append(
        item
    )

    _save(
        data
    )

    logger.info(
        "Pending signal disimpan | "
        "send_at=%s | "
        "bias=%s | "
        "entry=%s | "
        "order=%s",
        send_at.isoformat(),
        getattr(
            signal,
            "bias",
            "-",
        ),
        getattr(
            signal,
            "entry_price",
            "-",
        ),
        getattr(
            signal,
            "order_type",
            "-",
        ),
    )


# =========================================================
# AMBIL SIGNAL SIAP KIRIM
# =========================================================

def get_ready_signals() -> List[Dict[str, Any]]:
    """
    Mengambil semua signal yang sudah waktunya diproses.
    """

    data = _load()

    now = _now()

    ready = []

    for item in data:

        if item.get(
            "sent",
            False,
        ):

            continue

        send_at = _parse_datetime(
            item.get(
                "send_at"
            )
        )

        if send_at is None:

            logger.warning(
                "Pending signal memiliki "
                "send_at invalid: %s",
                item,
            )

            continue

        if now >= send_at:

            ready.append(
                item
            )

    return ready


# =========================================================
# TANDAI SUDAH TERKIRIM
# =========================================================

def mark_as_sent(
    signal,
):
    """
    Menandai signal sebagai sudah terkirim.

    Support object TradeSignal maupun dict.
    """

    data = _load()

    target_signal = _json_safe(
        signal
    )

    changed = False

    for item in data:

        stored_signal = item.get(
            "signal"
        )

        if stored_signal == target_signal:

            if not item.get(
                "sent",
                False,
            ):

                item["sent"] = True

                item["sent_at"] = (
                    _now().isoformat()
                )

                changed = True

    if changed:

        _save(
            data
        )


# =========================================================
# TANDAI ITEM BERDASARKAN OBJECT
# =========================================================

def mark_item_as_sent(
    item: Dict[str, Any],
):
    """
    Menandai satu item pending
    sebagai terkirim.

    Menggunakan kombinasi:

    - signal
    - send_at
    """

    data = _load()

    target_signal = _json_safe(
        item.get(
            "signal"
        )
    )

    target_send_at = item.get(
        "send_at"
    )

    changed = False

    for current in data:

        current_signal = current.get(
            "signal"
        )

        current_send_at = current.get(
            "send_at"
        )

        if (
            current_signal
            == target_signal
            and
            current_send_at
            == target_send_at
        ):

            if not current.get(
                "sent",
                False,
            ):

                current["sent"] = True

                current["sent_at"] = (
                    _now().isoformat()
                )

                changed = True

            break

    if changed:

        _save(
            data
        )


# =========================================================
# HAPUS SIGNAL TERKIRIM
# =========================================================

def clean_sent():
    """
    Menghapus seluruh pending signal
    yang sudah terkirim.
    """

    data = _load()

    before = len(
        data
    )

    data = [

        item

        for item in data

        if not item.get(
            "sent",
            False,
        )

    ]

    after = len(
        data
    )

    if before != after:

        _save(
            data
        )

        logger.info(
            "Pending signal dibersihkan: %s item",
            before - after,
        )


# =========================================================
# HAPUS SIGNAL EXPIRED
# =========================================================

def clean_expired(
    max_age_hours: int = 48,
):
    """
    Menghapus pending signal yang lebih
    lama dari max_age_hours.

    Default = 48 jam.
    """

    data = _load()

    now = _now()

    cleaned = []

    removed = 0

    for item in data:

        created_at = _parse_datetime(
            item.get(
                "created_at"
            )
        )

        if created_at is None:

            # Jangan langsung hapus data
            # yang timestamp-nya invalid.
            cleaned.append(
                item
            )

            continue

        age = (
            now - created_at
        ).total_seconds()

        if age > (
            max_age_hours * 3600
        ):

            removed += 1

            continue

        cleaned.append(
            item
        )

    if removed:

        _save(
            cleaned
        )

        logger.info(
            "Pending signal expired "
            "dihapus: %s",
            removed,
        )


# =========================================================
# HITUNG PENDING
# =========================================================

def count_pending() -> int:
    """
    Menghitung jumlah signal yang
    belum terkirim.
    """

    data = _load()

    return sum(

        1

        for item in data

        if not item.get(
            "sent",
            False,
        )

    )


# =========================================================
# GET ALL PENDING
# =========================================================

def get_all_pending() -> List[Dict[str, Any]]:
    """
    Mengambil seluruh pending signal.
    """

    return _load()


# =========================================================
# GET UNSENT PENDING
# =========================================================

def get_unsent_pending() -> List[Dict[str, Any]]:
    """
    Mengambil pending signal yang
    belum terkirim.
    """

    data = _load()

    return [

        item

        for item in data

        if not item.get(
            "sent",
            False,
        )

    ]

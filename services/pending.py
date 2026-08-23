import json
import logging
import os

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

    WIB = ZoneInfo(
        TIMEZONE
    )

except Exception:

    import pytz

    WIB = pytz.timezone(
        TIMEZONE
    )


# =========================================================
# FILE
# =========================================================

DATA_DIR = "data"

DATA_FILE = os.path.join(
    DATA_DIR,
    "pending_signal.json"
)


# =========================================================
# INTERNAL LOAD
# =========================================================

def _load() -> List[Dict[str, Any]]:
    """
    Membaca pending signal dari JSON.

    Kalau file belum ada atau rusak,
    otomatis mengembalikan list kosong.
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
                "Format pending_signal.json tidak valid."
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
    data: List[Dict[str, Any]]
):
    """
    Menyimpan pending signal ke JSON.
    """

    try:

        os.makedirs(
            DATA_DIR,
            exist_ok=True,
        )

        temp_file = (
            DATA_FILE
            + ".tmp"
        )

        with open(
            temp_file,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4,
            )

        # Atomic replace
        os.replace(
            temp_file,
            DATA_FILE,
        )

    except OSError:

        logger.exception(
            "Gagal menyimpan %s",
            DATA_FILE,
        )

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
    value: str
) -> Optional[datetime]:
    """
    Parse datetime ISO dan memastikan timezone-aware.
    """

    if not value:

        return None

    try:

        dt = datetime.fromisoformat(
            value
        )

    except (
        ValueError,
        TypeError,
    ):

        return None

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
    Menyimpan signal yang akan dikirim.

    Pilihan:

    1. send_at diberikan
       -> gunakan waktu tersebut.

    2. delay_minutes diberikan
       -> waktu kirim = sekarang + delay.

    3. Keduanya tidak diberikan
       -> signal langsung dianggap siap dikirim.

    Contoh:

        save_pending_signal(
            signal,
            delay_minutes=60
        )

    atau:

        save_pending_signal(
            signal,
            send_at=datetime(...)
        )
    """

    data = _load()

    now = _now()

    # -----------------------------------------------------
    # TENTUKAN WAKTU KIRIM
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # SIMPAN
    # -----------------------------------------------------

    item = {

        "signal": signal,

        "created_at":
            now.isoformat(),

        "send_at":
            send_at.isoformat(),

        "sent":
            False,

    }

    data.append(
        item
    )

    _save(
        data
    )

    logger.info(
        "Pending signal disimpan. "
        "send_at=%s",
        send_at.isoformat(),
    )


# =========================================================
# AMBIL SIGNAL SIAP KIRIM
# =========================================================

def get_ready_signals() -> List[Dict[str, Any]]:
    """
    Mengambil semua signal yang sudah waktunya dikirim.
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
                "Pending signal memiliki send_at invalid: %s",
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
    signal
):
    """
    Menandai signal sebagai sudah terkirim.
    """

    data = _load()

    changed = False

    for item in data:

        if item.get(
            "signal"
        ) == signal:

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
    item: Dict[str, Any]
):
    """
    Menandai satu item pending sebagai terkirim.

    Lebih aman digunakan scheduler dibanding mencari
    berdasarkan isi signal.
    """

    data = _load()

    target_signal = item.get(
        "signal"
    )

    target_send_at = item.get(
        "send_at"
    )

    changed = False

    for current in data:

        if (
            current.get("signal")
            == target_signal
            and
            current.get("send_at")
            == target_send_at
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
    Menghapus seluruh pending signal yang sudah terkirim.
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
    Menghapus pending signal yang terlalu lama.

    Default:
        48 jam
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
    Jumlah signal yang belum terkirim.
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

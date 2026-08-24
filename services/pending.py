"""
services/pending.py

PENDING SIGNAL STORAGE
======================

Fungsi:

- Menyimpan TradeSignal ke JSON
- Mendukung object dataclass seperti TradeSignal
- Mendukung nested dataclass seperti SMCResult
- Mendukung datetime timezone-aware
- Mengembalikan object asli saat dibaca
- Aman digunakan scheduler
- Mendukung delay pengiriman website
- Atomic JSON write
- Tidak lagi menghasilkan:

    TypeError:
    Object of type TradeSignal is not JSON serializable
"""


import json
import logging
import os
import importlib

from dataclasses import (
    is_dataclass,
    fields,
)

from datetime import (
    datetime,
    timedelta,
)

from enum import Enum

from typing import (
    Any,
    Dict,
    List,
    Optional,
)


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
    "pending_signal.json",
)


# =========================================================
# SERIALIZATION
# =========================================================

def _serialize(
    value: Any,
) -> Any:
    """
    Mengubah object Python menjadi object
    yang dapat disimpan sebagai JSON.

    Mendukung:

    - None
    - str
    - int
    - float
    - bool
    - list
    - tuple
    - dict
    - datetime
    - Enum
    - dataclass
    - nested dataclass
    """

    # -----------------------------------------------------
    # NONE / PRIMITIVE
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
    # DATETIME
    # -----------------------------------------------------

    if isinstance(
        value,
        datetime,
    ):

        return {
            "__type__": "datetime",
            "value": value.isoformat(),
        }


    # -----------------------------------------------------
    # ENUM
    # -----------------------------------------------------

    if isinstance(
        value,
        Enum,
    ):

        enum_class = type(
            value
        )

        return {

            "__type__": "enum",

            "module":
                enum_class.__module__,

            "class":
                enum_class.__qualname__,

            "value":
                _serialize(
                    value.value
                ),
        }


    # -----------------------------------------------------
    # DATACLASS
    # -----------------------------------------------------

    if is_dataclass(
        value
    ):

        cls = type(
            value
        )

        result = {

            "__type__":
                "dataclass",

            "module":
                cls.__module__,

            "class":
                cls.__qualname__,

            "fields": {},
        }


        for field in fields(
            value
        ):

            field_value = getattr(
                value,
                field.name,
            )

            result["fields"][
                field.name
            ] = _serialize(
                field_value
            )


        return result


    # -----------------------------------------------------
    # DICT
    # -----------------------------------------------------

    if isinstance(
        value,
        dict,
    ):

        return {

            "__type__":
                "dict",

            "items": [

                [
                    _serialize(key),
                    _serialize(val),
                ]

                for key, val in value.items()

            ],
        }


    # -----------------------------------------------------
    # LIST / TUPLE / SET
    # -----------------------------------------------------

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):

        return [

            _serialize(item)

            for item in value

        ]


    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    logger.warning(
        "Object tidak memiliki serializer khusus: %s",
        type(value),
    )

    return {
        "__type__":
            "repr",

        "value":
            repr(value),
    }


# =========================================================
# IMPORT CLASS
# =========================================================

def _get_class(
    module_name: str,
    class_name: str,
):
    """
    Mengambil class berdasarkan module + qualname.

    Contoh:

        services.signal_builder.TradeSignal
    """

    module = importlib.import_module(
        module_name
    )

    obj = module

    for part in class_name.split("."):

        obj = getattr(
            obj,
            part,
        )

    return obj


# =========================================================
# DESERIALIZATION
# =========================================================

def _deserialize(
    value: Any,
) -> Any:
    """
    Mengembalikan object JSON menjadi
    object Python semula.
    """

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
    # LIST
    # -----------------------------------------------------

    if isinstance(
        value,
        list,
    ):

        return [

            _deserialize(item)

            for item in value

        ]


    # -----------------------------------------------------
    # NON-DICT
    # -----------------------------------------------------

    if not isinstance(
        value,
        dict,
    ):

        return value


    object_type = value.get(
        "__type__"
    )


    # -----------------------------------------------------
    # DATETIME
    # -----------------------------------------------------

    if object_type == "datetime":

        dt = datetime.fromisoformat(
            value["value"]
        )

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=WIB
            )

        return dt.astimezone(
            WIB
        )


    # -----------------------------------------------------
    # ENUM
    # -----------------------------------------------------

    if object_type == "enum":

        cls = _get_class(

            value["module"],

            value["class"],

        )

        enum_value = _deserialize(
            value["value"]
        )

        return cls(
            enum_value
        )


    # -----------------------------------------------------
    # DATACLASS
    # -----------------------------------------------------

    if object_type == "dataclass":

        cls = _get_class(

            value["module"],

            value["class"],

        )

        kwargs = {}

        for name, field_value in (
            value.get(
                "fields",
                {}
            ).items()
        ):

            kwargs[name] = _deserialize(
                field_value
            )


        return cls(
            **kwargs
        )


    # -----------------------------------------------------
    # DICT
    # -----------------------------------------------------

    if object_type == "dict":

        result = {}

        for pair in value.get(
            "items",
            [],
        ):

            if (
                not isinstance(
                    pair,
                    list,
                )
                or len(pair) != 2
            ):

                continue

            key = _deserialize(
                pair[0]
            )

            val = _deserialize(
                pair[1]
            )

            result[key] = val

        return result


    # -----------------------------------------------------
    # FALLBACK / UNKNOWN
    # -----------------------------------------------------

    if object_type == "repr":

        return value.get(
            "value"
        )


    # -----------------------------------------------------
    # NORMAL DICT
    # -----------------------------------------------------

    return {

        key:
            _deserialize(val)

        for key, val in value.items()

    }


# =========================================================
# INTERNAL LOAD
# =========================================================

def _load() -> List[Dict[str, Any]]:
    """
    Membaca pending_signal.json.

    Jika file belum ada:
        []

    Jika JSON rusak:
        []

    Jika format bukan list:
        []
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

            data = json.load(
                f
            )


        if not isinstance(
            data,
            list,
        ):

            logger.warning(
                "Format pending_signal.json tidak valid."
            )

            return []


        # -------------------------------------------------
        # DESERIALIZE
        # -------------------------------------------------

        result = []


        for item in data:

            if not isinstance(
                item,
                dict,
            ):

                continue


            restored = dict(
                item
            )


            if "signal" in restored:

                try:

                    restored["signal"] = (
                        _deserialize(
                            restored["signal"]
                        )
                    )

                except Exception:

                    logger.exception(
                        "Gagal deserialize pending signal."
                    )

                    continue


            result.append(
                restored
            )


        return result


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

    Semua object complex akan diserialisasi
    terlebih dahulu.

    Penulisan menggunakan temporary file
    kemudian os.replace().
    """

    try:

        os.makedirs(
            DATA_DIR,
            exist_ok=True,
        )


        # -------------------------------------------------
        # SERIALIZE
        # -------------------------------------------------

        serialized_data = _serialize(
            data
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

                serialized_data,

                f,

                ensure_ascii=False,

                indent=4,

            )


        # -------------------------------------------------
        # ATOMIC REPLACE
        # -------------------------------------------------

        os.replace(
            temp_file,
            DATA_FILE,
        )


        logger.debug(
            "Pending signal JSON berhasil disimpan."
        )


    except OSError:

        logger.exception(
            "Gagal menyimpan %s",
            DATA_FILE,
        )

        raise


    except Exception:

        logger.exception(
            "Gagal serialize pending signal."
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


# =========================================================
# PARSE DATETIME
# =========================================================

def _parse_datetime(
    value: Any,
) -> Optional[datetime]:
    """
    Parse datetime ISO.

    Mendukung:
        datetime object
        string ISO
    """

    if not value:

        return None


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
# NORMALIZE DATETIME
# =========================================================

def _normalize_datetime(
    value: datetime,
) -> datetime:
    """
    Memastikan datetime timezone-aware WIB.
    """

    if value.tzinfo is None:

        return value.replace(
            tzinfo=WIB
        )


    return value.astimezone(
        WIB
    )


# =========================================================
# SIMPAN SIGNAL
# =========================================================

def save_pending_signal(
    signal,
    send_at: Optional[datetime] = None,
    delay_minutes: Optional[int] = None,
):
    """
    Menyimpan signal yang akan diproses scheduler.

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

    FIX:

    TradeSignal sekarang diserialisasi menjadi JSON,
    sehingga tidak lagi menghasilkan:

        TypeError:
        Object of type TradeSignal is not JSON serializable
    """

    data = _load()

    now = _now()


    # -----------------------------------------------------
    # TENTUKAN WAKTU KIRIM
    # -----------------------------------------------------

    if send_at is not None:

        send_at = _normalize_datetime(
            send_at
        )


    elif delay_minutes is not None:

        send_at = (
            now
            + timedelta(
                minutes=int(
                    delay_minutes
                )
            )
        )


    else:

        send_at = now


    # -----------------------------------------------------
    # VALIDASI
    # -----------------------------------------------------

    if signal is None:

        raise ValueError(
            "Signal tidak boleh None."
        )


    # -----------------------------------------------------
    # ITEM
    # -----------------------------------------------------

    item = {

        "signal":
            signal,

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


    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    _save(
        data
    )


    logger.info(
        "Pending signal disimpan | "
        "send_at=%s | type=%s",
        send_at.isoformat(),
        type(signal).__name__,
    )


# =========================================================
# AMBIL SIGNAL SIAP KIRIM
# =========================================================

def get_ready_signals() -> List[Dict[str, Any]]:
    """
    Mengambil seluruh signal yang sudah
    waktunya diproses.

    signal yang dikembalikan sudah berupa
    object TradeSignal asli.
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

        current_signal = item.get(
            "signal"
        )


        if current_signal == signal:

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
    Menandai satu pending item.

    Lebih aman digunakan scheduler.
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
    Menghapus pending signal yang
    terlalu lama.

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

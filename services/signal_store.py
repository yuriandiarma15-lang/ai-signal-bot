"""
services/signal_store.py

Temporary Signal Store
======================

Menyimpan:
- Signal short
- Detail analisa

Tujuan:
Saat user klik:

📊 Detail Analisa
    ↓
pesan yang sama berubah menjadi detail

🔽 Hide Detail
    ↓
pesan yang sama kembali menjadi signal awal

Tidak mengirim pesan baru.

Data disimpan sementara di memory.
Tidak menggunakan database permanen.
"""

import time
import uuid

from typing import Dict, Optional, Tuple


# =========================================================
# STORE
# =========================================================

_store: Dict[
    str,
    Tuple[str, str, float]
] = {}


# =========================================================
# TTL
# =========================================================

# Data signal disimpan selama 6 jam.
TTL_SECONDS = 6 * 60 * 60


# =========================================================
# SAVE SIGNAL
# =========================================================

def save_signal(
    signal_text: str,
    detail_text: str,
) -> str:

    _cleanup()

    signal_id = uuid.uuid4().hex[:12]

    _store[signal_id] = (
        signal_text,
        detail_text,
        time.time(),
    )

    return signal_id


# =========================================================
# GET SIGNAL SHORT
# =========================================================

def get_signal(
    signal_id: str,
) -> Optional[str]:

    _cleanup()

    entry = _store.get(
        signal_id
    )

    if not entry:
        return None

    return entry[0]


# =========================================================
# GET DETAIL
# =========================================================

def get_detail(
    signal_id: str,
) -> Optional[str]:

    _cleanup()

    entry = _store.get(
        signal_id
    )

    if not entry:
        return None

    return entry[1]


# =========================================================
# DELETE SIGNAL
# =========================================================

def delete_signal(
    signal_id: str,
) -> None:

    _store.pop(
        signal_id,
        None,
    )


# =========================================================
# CLEANUP EXPIRED DATA
# =========================================================

def _cleanup() -> None:

    now = time.time()

    expired = []

    for signal_id, entry in _store.items():

        created_at = entry[2]

        if (
            now - created_at
            > TTL_SECONDS
        ):

            expired.append(
                signal_id
            )

    for signal_id in expired:

        _store.pop(
            signal_id,
            None,
        )

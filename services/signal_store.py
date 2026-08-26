"""
services/signal_store.py

Temporary Signal Store
======================

Menyimpan:
- Signal short
- Detail analisa

Fungsi:
- save_signal()
- get_signal()
- save_detail()
- get_detail()

save_detail() tetap dipertahankan agar
services/sender.py lama tidak error.
"""

import time
import uuid

from typing import Dict, Optional, Tuple


# =========================================================
# STORE
# =========================================================

_store: Dict[
    str,
    Tuple[str, Optional[str], float]
] = {}


# =========================================================
# TTL
# =========================================================

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
# SAVE DETAIL
#
# COMPATIBILITY DENGAN sender.py LAMA
# =========================================================

def save_detail(
    detail_text: str,
) -> str:

    _cleanup()

    signal_id = uuid.uuid4().hex[:12]

    _store[signal_id] = (
        "",
        detail_text,
        time.time(),
    )

    return signal_id


# =========================================================
# GET SIGNAL
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

    signal_text = entry[0]

    if not signal_text:
        return None

    return signal_text


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
# CLEANUP
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

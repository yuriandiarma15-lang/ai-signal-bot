"""
services/signal_store.py

Simpan teks "Detail Analisa" sementara di memory,
supaya saat member klik tombol, bot bisa ambil lagi
tanpa perlu database permanen.
"""

import time
import uuid
from typing import Dict, Optional, Tuple

_store: Dict[str, Tuple[str, float]] = {}

TTL_SECONDS = 6 * 60 * 60  # 6 jam


def save_detail(detail_text: str) -> str:
    _cleanup()
    signal_id = uuid.uuid4().hex[:12]
    _store[signal_id] = (detail_text, time.time())
    return signal_id


def get_detail(signal_id: str) -> Optional[str]:
    _cleanup()
    entry = _store.get(signal_id)
    return entry[0] if entry else None


def _cleanup() -> None:
    now = time.time()
    expired = [sid for sid, (_, t) in _store.items() if now - t > TTL_SECONDS]
    for sid in expired:
        _store.pop(sid, None)

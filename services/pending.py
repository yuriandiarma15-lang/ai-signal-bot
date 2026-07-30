import json
import os
from datetime import datetime, timedelta

import pytz

WIB = pytz.timezone("Asia/Jakarta")

DATA_FILE = "data/pending_signal.json"


def _load():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def _save(data):
    os.makedirs("data", exist_ok=True)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


# ==========================
# SIMPAN SIGNAL
# ==========================

def save_pending_signal(signal):

    data = _load()

    send_time = datetime.now(WIB) + timedelta(hours=1)

    data.append({

        "signal": signal,

        "send_at": send_time.isoformat(),

        "sent": False

    })

    _save(data)


# ==========================
# AMBIL SIGNAL SIAP KIRIM
# ==========================

def get_ready_signals():

    data = _load()

    now = datetime.now(WIB)

    ready = []

    for item in data:

        if item["sent"]:
            continue

        send_at = datetime.fromisoformat(
            item["send_at"]
        )

        if now >= send_at:

            ready.append(item)

    return ready


# ==========================
# TANDAI SUDAH TERKIRIM
# ==========================

def mark_as_sent(signal):

    data = _load()

    for item in data:

        if item["signal"] == signal:

            item["sent"] = True

    _save(data)


# ==========================
# HAPUS SIGNAL YANG SUDAH TERKIRIM
# ==========================

def clean_sent():

    data = _load()

    data = [

        x

        for x in data

        if not x["sent"]

    ]

    _save(data)

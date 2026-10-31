import os
import json
import logging
import threading

import gspread

from oauth2client.service_account import ServiceAccountCredentials

from config.settings import SPREADSHEET_ID


logger = logging.getLogger(__name__)


# =========================================================
# GOOGLE SHEET CONNECTION
# =========================================================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


# =========================================================
# GOOGLE CREDENTIALS
# =========================================================

google_credentials_raw = os.getenv("GOOGLE_CREDENTIALS")

if not google_credentials_raw:
    raise RuntimeError(
        "GOOGLE_CREDENTIALS belum diset di Environment Variables hosting."
    )

try:
    google_credentials = json.loads(
        google_credentials_raw
    )
except json.JSONDecodeError as exc:
    raise RuntimeError(
        "GOOGLE_CREDENTIALS bukan JSON yang valid."
    ) from exc


# =========================================================
# GOOGLE AUTH
# =========================================================

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    google_credentials,
    scope,
)

client = gspread.authorize(creds)


# =========================================================
# OPEN SPREADSHEET
# =========================================================

if not SPREADSHEET_ID:
    raise RuntimeError(
        "SPREADSHEET_ID belum diset di Environment Variables."
    )

spreadsheet = client.open_by_key(
    SPREADSHEET_ID
)

sheet = spreadsheet.sheet1

logger.info(
    "[SHEET] Koneksi Google Sheets berhasil. Worksheet: %s",
    sheet.title,
)


# =========================================================
# GET MEMBERS
# =========================================================

def get_members():
    """
    Mengambil data member dari worksheet pertama.

    Header kosong dan duplikat ditangani otomatis.
    Kolom D (broker) juga dipetakan ke paket.
    """

    try:
        values = sheet.get_all_values()

        if not values:
            logger.warning("[SHEET] Worksheet kosong.")
            return []

        headers = [
            str(value).strip()
            for value in values[0]
        ]

        last_used = len(headers)

        for column_index in range(last_used - 1, -1, -1):

            header_empty = not headers[column_index]

            column_data_empty = all(
                len(row) <= column_index
                or not str(row[column_index]).strip()
                for row in values[1:]
            )

            if header_empty and column_data_empty:
                last_used -= 1
            else:
                break

        headers = headers[:last_used]

        if not headers:
            logger.warning(
                "[SHEET] Header tidak ditemukan."
            )
            return []

        unique_headers = []
        seen_headers = set()

        for index, header in enumerate(headers, start=1):

            if not header:
                header = f"_column_{index}"

            base_header = header
            suffix = 2

            while header in seen_headers:
                header = f"{base_header}_{suffix}"
                suffix += 1

            seen_headers.add(header)
            unique_headers.append(header)

        members = []

        for row_number, row in enumerate(values[1:], start=2):

            row = row[:last_used]

            if not any(str(value).strip() for value in row):
                continue

            if len(row) < last_used:
                row += [""] * (last_used - len(row))

            member = dict(
                zip(unique_headers, row)
            )

            # Kolom D berisi nama paket.
            if not member.get("paket"):
                member["paket"] = member.get("broker", "")

            members.append(member)

        logger.info(
            "[SHEET] Berhasil membaca %s member.",
            len(members),
        )

        return members

    except Exception:
        logger.exception(
            "[SHEET] Gagal mengambil data member."
        )
        raise


# =========================================================
# MANUAL SIGNAL USAGE
# =========================================================

SIGNAL_USAGE_SHEET = "Signal_Usage"

SIGNAL_USAGE_HEADERS = [
    "telegram_id",
    "tanggal",
    "jumlah_request",
]

_SIGNAL_USAGE_LOCK = threading.Lock()


# =========================================================
# GET / CREATE USAGE WORKSHEET
# =========================================================

def get_signal_usage_sheet():

    try:
        ws = spreadsheet.worksheet(
            SIGNAL_USAGE_SHEET
        )

    except gspread.WorksheetNotFound:

        ws = spreadsheet.add_worksheet(
            title=SIGNAL_USAGE_SHEET,
            rows=2000,
            cols=3,
        )

        ws.update(
            range_name="A1:C1",
            values=[SIGNAL_USAGE_HEADERS],
        )

        return ws

    headers = ws.row_values(1)

    if not headers:

        ws.update(
            range_name="A1:C1",
            values=[SIGNAL_USAGE_HEADERS],
        )

    elif headers[:3] != SIGNAL_USAGE_HEADERS:

        raise RuntimeError(
            "Header Signal_Usage tidak sesuai."
        )

    return ws


# =========================================================
# RESERVE SIGNAL REQUEST
# =========================================================

def reserve_signal_request(
    telegram_id,
    usage_date,
    daily_limit,
):
    """
    Mencatat satu request manual.

    Return:
        (True, jumlah_request)
        (False, jumlah_request)
    """

    telegram_id = str(telegram_id).strip()
    usage_date = str(usage_date).strip()
    daily_limit = int(daily_limit)

    with _SIGNAL_USAGE_LOCK:

        ws = get_signal_usage_sheet()

        rows = ws.get_all_values()

        for row_number, row in enumerate(
            rows[1:],
            start=2,
        ):

            if len(row) < 3:
                continue

            if (
                str(row[0]).strip() == telegram_id
                and str(row[1]).strip() == usage_date
            ):

                try:
                    current = int(row[2] or 0)
                except (TypeError, ValueError):
                    current = 0

                if current >= daily_limit:
                    return False, current

                updated = current + 1

                ws.update_cell(
                    row_number,
                    3,
                    updated,
                )

                return True, updated

        ws.append_row(
            [
                telegram_id,
                usage_date,
                1,
            ],
            value_input_option="USER_ENTERED",
        )

        return True, 1


# =========================================================
# REFUND SIGNAL REQUEST
# =========================================================

def refund_signal_request(
    telegram_id,
    usage_date,
):
    """
    Mengembalikan satu kuota jika proses signal gagal.
    """

    telegram_id = str(telegram_id).strip()
    usage_date = str(usage_date).strip()

    with _SIGNAL_USAGE_LOCK:

        ws = get_signal_usage_sheet()

        rows = ws.get_all_values()

        for row_number, row in enumerate(
            rows[1:],
            start=2,
        ):

            if len(row) < 3:
                continue

            if (
                str(row[0]).strip() == telegram_id
                and str(row[1]).strip() == usage_date
            ):

                try:
                    current = int(row[2] or 0)
                except (TypeError, ValueError):
                    return

                updated = max(
                    0,
                    current - 1,
                )

                ws.update_cell(
                    row_number,
                    3,
                    updated,
                )

                return

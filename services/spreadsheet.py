
import os
import json
import logging

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

google_credentials_raw = os.getenv(
    "GOOGLE_CREDENTIALS"
)

if not google_credentials_raw:
    raise RuntimeError(
        "GOOGLE_CREDENTIALS belum diset di "
        "Environment Variables hosting."
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
        "SPREADSHEET_ID belum diset di "
        "Environment Variables."
    )

spreadsheet = client.open_by_key(
    SPREADSHEET_ID
)

# Mempertahankan perilaku lama: gunakan worksheet pertama.
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
    Mengambil member dari Google Sheets tanpa get_all_records(),
    sehingga header kosong atau duplikat tidak langsung
    menyebabkan GSpreadException.

    Fungsi ini hanya membaca spreadsheet, tidak mengubah data.
    """

    try:
        values = sheet.get_all_values()

        if not values:
            logger.warning(
                "[SHEET] Worksheet kosong."
            )
            return []

        # Header dari baris pertama.
        headers = [
            str(value).strip()
            for value in values[0]
        ]

        # Hapus hanya kolom kosong di ujung kanan apabila
        # seluruh data pada kolom tersebut juga kosong.
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
                "[SHEET] Baris header tidak berisi nama kolom."
            )
            return []

        # Pastikan setiap nama kolom unik.
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

        # Baris pertama adalah header; data dimulai baris kedua.
        for row_number, row in enumerate(values[1:], start=2):
            row = row[:last_used]

            # Lewati baris yang benar-benar kosong.
            if not any(str(value).strip() for value in row):
                continue

            # Lengkapi kolom yang kosong agar panjangnya sama.
            if len(row) < last_used:
                row += [""] * (last_used - len(row))

            member = dict(
                zip(unique_headers, row)
            )

            members.append(member)

        logger.info(
            "[SHEET] Berhasil membaca %s baris member.",
            len(members),
        )

        return members

    except Exception:
        logger.exception(
            "[SHEET] Gagal mengambil data member."
        )
        raise

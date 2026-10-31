from datetime import datetime
import time
import logging

import gspread

from services.spreadsheet import get_members


# =========================================================
# CONFIG
# =========================================================

DATE_FORMAT = "%d-%m-%Y"

logger = logging.getLogger(__name__)


# =========================================================
# PACKAGE ACCESS
# =========================================================

# Paket yang mendapatkan fitur Fundamental + Combined AI
PREMIUM_PACKAGES = {
    "6 bulan",
    "12 bulan",
    "lifetime",
}


# Paket yang hanya mendapatkan AI SMC
BASIC_PACKAGES = {
    "1 bulan",
    "mitra hfm",
}


# =========================================================
# NORMALIZE PACKAGE
# =========================================================

def normalize_package(package):
    """
    Menormalisasi nama paket dari Google Sheet.

    Contoh:
    '1 Bulan'   -> '1 bulan'
    '6 BULAN'   -> '6 bulan'
    '12 Bulan'  -> '12 bulan'
    'Lifetime'  -> 'lifetime'
    'MITRA HFM' -> 'mitra hfm'
    """

    if package is None:
        return ""

    return str(package).strip().lower()


# =========================================================
# CHECK FUNDAMENTAL ACCESS
# =========================================================

def has_fundamental_access(member):
    """
    Menentukan apakah member boleh menggunakan
    fitur Fundamental.

    1 Bulan    -> NO
    MITRA HFM  -> NO
    6 Bulan    -> YES
    12 Bulan   -> YES
    Lifetime   -> YES
    """

    if not member:
        return False

    if not member.get("active", False):
        return False

    package = normalize_package(
        member.get("package", "")
    )

    return package in PREMIUM_PACKAGES


# =========================================================
# CHECK COMBINED AI ACCESS
# =========================================================

def has_combined_access(member):
    """
    Combined AI mengikuti akses Fundamental.
    """

    return has_fundamental_access(member)


# =========================================================
# CHECK SMC ACCESS
# =========================================================

def has_smc_access(member):
    """
    Semua member ACTIVE mendapatkan akses AI SMC.
    """

    if not member:
        return False

    return bool(
        member.get("active", False)
    )


# =========================================================
# GET MEMBERS WITH RETRY
# =========================================================

def _get_members_with_retry(
    max_retries=3,
    retry_delay=2
):
    """
    Mengambil member dari Google Sheets.

    Jika Google Sheets mengalami error sementara
    seperti HTTP 503, lakukan retry otomatis.
    """

    for attempt in range(1, max_retries + 1):

        try:

            return get_members()

        except gspread.exceptions.APIError as e:

            logger.warning(
                "Google Sheets error | attempt=%s/%s | error=%s",
                attempt,
                max_retries,
                e
            )

            if attempt < max_retries:

                delay = retry_delay * attempt

                logger.info(
                    "Retry Google Sheets dalam %s detik...",
                    delay
                )

                time.sleep(delay)

            else:

                logger.error(
                    "Google Sheets gagal setelah %s percobaan.",
                    max_retries
                )

        except Exception:

            logger.exception(
                "Unexpected error saat mengambil member."
            )

            break

    return None


# =========================================================
# PARSE EXPIRED DATE
# =========================================================

def _parse_expired_date(value):
    """
    Mengubah nilai expired menjadi datetime.

    Return:
        datetime
        None

    Lifetime dapat diproses tanpa tanggal expired.
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    try:

        return datetime.strptime(
            value,
            DATE_FORMAT
        )

    except ValueError:

        return None


# =========================================================
# IS LIFETIME PACKAGE
# =========================================================

def is_lifetime_package(package):
    """
    Mengecek apakah paket adalah Lifetime.
    """

    return (
        normalize_package(package)
        == "lifetime"
    )


# =========================================================
# CHECK MEMBER
# =========================================================

def check_member(telegram_id):
    """
    Mengecek membership berdasarkan telegram_id.

    Return aktif:

    {
        "found": True,
        "active": True,
        "expired": "...",
        "package": "...",
        "username": "...",
        "data": {...}
    }

    Return jika Google Sheet gagal:

    {
        "found": False,
        "active": False,
        "expired": None,
        "package": None,
        "error": "spreadsheet_unavailable"
    }
    """

    members = _get_members_with_retry()

    # =====================================================
    # GOOGLE SHEETS GAGAL
    # =====================================================

    if members is None:

        return {
            "found": False,
            "active": False,
            "expired": None,
            "package": None,
            "error": "spreadsheet_unavailable"
        }

    # =====================================================
    # CARI USER
    # =====================================================

    user_rows = []

    for member in members:

        sheet_id = str(
            member.get(
                "telegram_id",
                ""
            )
        ).strip()

        if sheet_id == str(telegram_id):

            user_rows.append(member)

    # =====================================================
    # USER BELUM ADA
    # =====================================================

    if not user_rows:

        return {
            "found": False,
            "active": False,
            "expired": None,
            "package": None
        }

    # =====================================================
    # CARI DATA VALID
    # =====================================================

    valid_rows = []

    for row in user_rows:

        package = normalize_package(
            row.get("paket") or row.get("broker", "")
        )

        status = str(
            row.get(
                "status",
                ""
            )
        ).strip().upper()

        # =================================================
        # LIFETIME
        # =================================================

        if (
            package == "lifetime"
            and
            status == "ACTIVE"
        ):

            valid_rows.append(
                (
                    datetime.max,
                    row
                )
            )

            continue

        # =================================================
        # MEMBERSHIP NORMAL
        # =================================================

        expired = _parse_expired_date(
            row.get(
                "expired",
                ""
            )
        )

        if expired is not None:

            valid_rows.append(
                (
                    expired,
                    row
                )
            )

    # =====================================================
    # DATA TIDAK VALID
    # =====================================================

    if not valid_rows:

        return {
            "found": True,
            "active": False,
            "expired": None,
            "package": None
        }

    # =====================================================
    # AMBIL MEMBERSHIP TERBARU
    # =====================================================

    latest_date, latest = max(
        valid_rows,
        key=lambda x: x[0]
    )

    today = datetime.now().date()

    status = str(
        latest.get(
            "status",
            ""
        )
    ).strip().upper()

    package = latest.get("paket") or latest.get("broker", "")

    # =====================================================
    # LIFETIME ACTIVE
    # =====================================================

    if (
        is_lifetime_package(package)
        and
        status == "ACTIVE"
    ):

        return {
            "found": True,
            "active": True,
            "expired": latest.get(
                "expired",
                ""
            ),
            "package": package,
            "username": latest.get(
                "username",
                ""
            ),
            "data": latest
        }

    # =====================================================
    # MEMBER ACTIVE
    # =====================================================

    if (
        latest_date.date() > today
        and
        status == "ACTIVE"
    ):

        return {
            "found": True,
            "active": True,
            "expired": latest.get("expired"),
            "package": package,
            "username": latest.get(
                "username",
                ""
            ),
            "data": latest
        }

    # =====================================================
    # MEMBER EXPIRED / INACTIVE
    # =====================================================

    return {
        "found": True,
        "active": False,
        "expired": latest.get("expired"),
        "package": package,
        "username": latest.get(
            "username",
            ""
        ),
        "data": latest
    }


# =========================================================
# GET ACTIVE MEMBERS
# =========================================================

def get_active_members():
    """
    Mengambil semua member yang masih ACTIVE.

    Lifetime juga dianggap ACTIVE tanpa
    memperhatikan tanggal expired.
    """

    members = _get_members_with_retry()

    # =====================================================
    # GOOGLE SHEETS GAGAL
    # =====================================================

    if members is None:

        logger.error(
            "Tidak bisa mengambil active members "
            "karena Google Sheets unavailable."
        )

        return None

    checked = {}

    for member in members:

        telegram_id = str(
            member.get(
                "telegram_id",
                ""
            )
        ).strip()

        if not telegram_id:
            continue

        package = normalize_package(
            member.get("paket") or member.get("broker", "")
        )

        status = str(
            member.get(
                "status",
                ""
            )
        ).strip().upper()

        # =================================================
        # LIFETIME
        # =================================================

        if (
            package == "lifetime"
            and
            status == "ACTIVE"
        ):

            checked[telegram_id] = (
                datetime.max,
                member
            )

            continue

        # =================================================
        # NORMAL MEMBERSHIP
        # =================================================

        expired = _parse_expired_date(
            member.get(
                "expired",
                ""
            )
        )

        if expired is None:
            continue

        # =================================================
        # AMBIL EXPIRED TERBARU
        # =================================================

        if telegram_id not in checked:

            checked[telegram_id] = (
                expired,
                member
            )

        else:

            old_expired = checked[telegram_id][0]

            if expired > old_expired:

                checked[telegram_id] = (
                    expired,
                    member
                )

    # =====================================================
    # FILTER ACTIVE
    # =====================================================

    result = []

    today = datetime.now().date()

    for expired, member in checked.values():

        status = str(
            member.get(
                "status",
                ""
            )
        ).strip().upper()

        package = normalize_package(
            member.get("paket") or member.get("broker", "")
        )

        # =================================================
        # LIFETIME
        # =================================================

        if (
            package == "lifetime"
            and
            status == "ACTIVE"
        ):

            result.append(member)

            continue

        # =================================================
        # NORMAL ACTIVE
        # =================================================

        if (
            expired.date() > today
            and
            status == "ACTIVE"
        ):

            result.append(member)

    return result


# =========================================================
# MANUAL SIGNAL PACKAGE LIMIT
# =========================================================

def get_manual_signal_limit(member):
    """
    Paket yang boleh request manual signal:

    1 Tahun / 12 Bulan: 2 kali per hari
    3 Tahun / 36 Bulan: 5 kali per hari

    Paket 1 Bulan dan 6 Bulan tidak mendapat akses.
    Admin ditangani terpisah di handler signal.py.
    """

    if not member or not member.get("active", False):
        return 0

    package = normalize_package(
        member.get("package")
        or member.get("paket")
        or member.get("broker")
        or ""
    )

    package = " ".join(
        package.replace("_", " ").split()
    )

    limits = {
        "1 tahun": 2,
        "12 bulan": 2,
        "3 tahun": 5,
        "36 bulan": 5,
    }

    return limits.get(package, 0)

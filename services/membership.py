from datetime import datetime
import time
import logging

import gspread

from services.spreadsheet import get_members


DATE_FORMAT = "%d-%m-%Y"

logger = logging.getLogger(__name__)


# ==========================
# GET MEMBERS WITH RETRY
# ==========================

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


# ==========================
# CHECK MEMBER
# ==========================

def check_member(
    telegram_id
):

    members = _get_members_with_retry()

    # Google Sheets benar-benar gagal
    if members is None:

        return {
            "found": False,
            "active": False,
            "expired": None,
            "package": None,
            "error": "spreadsheet_unavailable"
        }


    user_rows = []


    for member in members:

        sheet_id = str(
            member.get(
                "telegram_id",
                ""
            )
        )


        if sheet_id == str(telegram_id):

            user_rows.append(
                member
            )


    # ==========================
    # USER BELUM ADA DI SHEET
    # ==========================

    if not user_rows:

        return {
            "found": False,
            "active": False,
            "expired": None,
            "package": None
        }


    valid_rows = []


    for row in user_rows:

        try:

            expired = datetime.strptime(
                row.get(
                    "expired",
                    ""
                ),
                DATE_FORMAT
            )

            valid_rows.append(
                (
                    expired,
                    row
                )
            )

        except Exception:

            continue


    # ==========================
    # DATA EXPIRED TIDAK VALID
    # ==========================

    if not valid_rows:

        return {
            "found": True,
            "active": False,
            "expired": None,
            "package": None
        }


    # ==========================
    # AMBIL EXPIRED TERBARU
    # ==========================

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
    ).upper()


    # ==========================
    # MEMBER ACTIVE
    # ==========================

    if (
        latest_date.date() > today
        and
        status == "ACTIVE"
    ):

        return {
            "found": True,
            "active": True,

            "expired":
                latest.get(
                    "expired"
                ),

            "package":
                latest.get(
                    "paket"
                ),

            "username":
                latest.get(
                    "username",
                    ""
                ),

            "data":
                latest
        }


    # ==========================
    # MEMBER EXPIRED
    # ==========================

    return {
        "found": True,
        "active": False,

        "expired":
            latest.get(
                "expired"
            ),

        "package":
            latest.get(
                "paket"
            ),

        "data":
            latest
    }


# ==========================
# GET ACTIVE MEMBERS
# ==========================

def get_active_members():

    members = _get_members_with_retry()


    # ==========================
    # GOOGLE SHEETS GAGAL
    # ==========================

    if members is None:

        logger.error(
            "Tidak bisa mengambil active members karena Google Sheets unavailable."
        )

        return None


    checked = {}


    for member in members:

        telegram_id = str(
            member.get(
                "telegram_id",
                ""
            )
        )


        if not telegram_id:

            continue


        try:

            expired = datetime.strptime(
                member.get(
                    "expired",
                    ""
                ),
                DATE_FORMAT
            )

        except Exception:

            continue


        # ==========================
        # AMBIL EXPIRED TERBARU
        # ==========================

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


    result = []


    today = datetime.now().date()


    for expired, member in checked.values():

        status = str(
            member.get(
                "status",
                ""
            )
        ).upper()


        if (
            expired.date() > today
            and
            status == "ACTIVE"
        ):

            result.append(
                member
            )


    return result

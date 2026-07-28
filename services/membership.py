from datetime import datetime

from services.spreadsheet import get_members



DATE_FORMAT = "%d-%m-%Y"





# ==========================
# CHECK MEMBER
# ==========================


def check_member(
    telegram_id
):


    members = get_members()



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


        except:


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
    # AMBIL EXPIRED TERLAMA
    # ==========================


    latest_date, latest = max(

        valid_rows,

        key=lambda x:x[0]

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
    #
    # contoh:
    # expired 23-07-2026
    # hari ini 22-07-2026
    #
    # ACTIVE
    #
    # expired 22-07-2026
    # hari ini 22-07-2026
    #
    # EXPIRED
    #
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


    members = get_members()



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


        except:


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

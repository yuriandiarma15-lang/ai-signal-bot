import asyncio

from datetime import datetime, timedelta

import pytz


from services.signal_builder import (
    build_signal
)


from services.sender import (
    send_signal_to_members
)



WIB = pytz.timezone(
    "Asia/Jakarta"
)



# =====================================
# CHECK TRADING SESSION
# =====================================
def trading_open():

    now = datetime.now(WIB)

    weekday = now.weekday()  # Senin=0 ... Minggu=6

    hour = now.hour
    minute = now.minute

    current_minutes = (
        hour * 60
        +
        minute
    )


    # Mulai signal
    start = (
        6 * 60
        +
        55
    )


    # Berakhir sesi malam
    end = (
        2 * 60
        +
        15
    )


    # ==========================
    # MINGGU
    # FULL CLOSED
    # ==========================
    if weekday == 6:

        return False



    # ==========================
    # SABTU
    # HANYA SAMPAI 02:15
    # ==========================
    if weekday == 5:

        if current_minutes <= end:

            return True

        return False



    # ==========================
    # SENIN
    # ==========================
    if weekday == 0:


        # Senin dini hari tutup
        # Tunggu sesi baru jam 07:00

        if current_minutes < start:

            return False



        return True



    # ==========================
    # SELASA - JUMAT
    # ==========================
    if weekday in [1, 2, 3, 4]:


        # 00:00 - 02:15
        # lanjutan sesi sebelumnya

        if current_minutes <= end:

            return True



        # 06:55 - 23:59

        if current_minutes >= start:

            return True



    return False




# =====================================
# NEXT SIGNAL TIME
# =====================================
def next_signal_time():

    now = datetime.now(WIB)

    target = now.replace(
        minute=0,
        second=0,
        microsecond=0
    )

    target += timedelta(hours=1)


    while True:

        weekday = target.weekday()

        current_minutes = (
            target.hour * 60
            +
            target.minute
        )


        start = (
            6 * 60
            +
            55
        )

        end = (
            2 * 60
            +
            15
        )


        # ==========================
        # MINGGU
        # ==========================
        if weekday == 6:

            target = (
                target
                +
                timedelta(days=1)
            ).replace(
                hour=7,
                minute=0,
                second=0,
                microsecond=0
            )

            continue



        # ==========================
        # SABTU SETELAH 02:15
        # ==========================
        if weekday == 5:

            if current_minutes > end:

                target = (
                    target
                    +
                    timedelta(days=2)
                ).replace(
                    hour=7,
                    minute=0,
                    second=0,
                    microsecond=0
                )

                continue



        # ==========================
        # SENIN DINI HARI
        # ==========================
        if weekday == 0:

            if current_minutes < start:

                target = target.replace(
                    hour=7,
                    minute=0,
                    second=0,
                    microsecond=0
                )

                break



        # ==========================
        # SELASA - JUMAT
        # ==========================
        if weekday in [1,2,3,4]:

            if end < current_minutes < start:

                target = target.replace(
                    hour=7,
                    minute=0,
                    second=0,
                    microsecond=0
                )

                break


        break


    return target




# =====================================
# SIGNAL LOOP
# =====================================

async def signal_scheduler(
    bot
):


    print(
        "⏰ SIGNAL SCHEDULER ACTIVE"
    )



    while True:


        now = datetime.now(
            WIB
        )


        next_run = next_signal_time()



        wait = (

            next_run - now

        ).total_seconds()



        print(

            "NEXT SIGNAL:",

            next_run.strftime(

                "%d-%m-%Y %H:%M WIB"

            )

        )



        await asyncio.sleep(
            max(
                wait,
                1
            )
        )




        if not trading_open():


            print(

                "MARKET SESSION CLOSED"

            )


            continue




        print(

            "GENERATING SIGNAL..."

        )



        signal = build_signal()



        print(

            signal

        )



        result = await send_signal_to_members(

            bot,

            signal

        )



        print(

            "SEND RESULT:",

            result

        )

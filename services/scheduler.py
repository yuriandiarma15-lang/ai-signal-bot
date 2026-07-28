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

    now = datetime.now(
        WIB
    )


    hour = now.hour

    minute = now.minute



    current_minutes = (

        hour * 60

        +

        minute

    )



    # Mulai 06:55

    start = (

        6 * 60

        +

        55

    )



    # Berakhir 02:15 hari berikutnya

    end = (

        2 * 60

        +

        15

    )



    # sesi melewati tengah malam

    if current_minutes >= start:

        return True


    if current_minutes <= end:

        return True


    return False





# =====================================
# NEXT SIGNAL TIME
# =====================================

def next_signal_time():

    now = datetime.now(
        WIB
    )


    target = now.replace(

        minute=0,

        second=0,

        microsecond=0

    )


    if now.minute >= 0:

        target += timedelta(

            hours=1

        )


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

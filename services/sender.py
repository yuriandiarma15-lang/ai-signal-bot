from services.membership import (
    get_active_members
)



# =====================================
# SEND SIGNAL TO MEMBERS
# =====================================

async def send_signal_to_members(
    bot,
    signal_text
):


    members = get_active_members()



    print(
        "TOTAL MEMBER:",
        len(members)
    )



    success = 0

    failed = 0



    for member in members:


        telegram_id = member.get(
            "telegram_id"
        )



        if not telegram_id:


            print(
                "Telegram ID kosong:",
                member
            )


            failed += 1

            continue




        try:


            await bot.send_message(

                chat_id=int(
                    telegram_id
                ),

                text=signal_text,

                parse_mode="HTML"

            )



            print(

                "TERKIRIM:",
                telegram_id

            )


            success += 1




        except Exception as e:



            print(

                "GAGAL KIRIM:",

                telegram_id,

                e

            )


            failed += 1





    return {


        "success": success,


        "failed": failed,


        "total": len(members)

    }

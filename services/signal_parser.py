from datetime import datetime



from database.cache import (
    get_signal_number,
    increase_signal_number
)





# ==========================
# FORMAT SIGNAL
# ==========================


def format_signal(
    message_text
):


    number = get_signal_number()



    increase_signal_number()



    now = datetime.now().strftime(
        "%d-%m-%Y %H:%M WIB"
    )



    text = f"""

🔥 <b>SIGNAL #{number}</b>


📊 <b>XAUUSD SIGNAL</b>


🕒 {now}


━━━━━━━━━━━━━━


{message_text}


━━━━━━━━━━━━━━


🧠 <b>Smart Money Concept</b>


⚠️ Gunakan money management
yang baik.


🤖 <b>XAU AI ASSISTANT</b>


"""



    return text

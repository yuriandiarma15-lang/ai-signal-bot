import json

import os

from datetime import datetime





CACHE_FILE = "database/cache.json"





def load_cache():


    if not os.path.exists(
        CACHE_FILE
    ):


        return {

            "date":"",
            
            "signal":0

        }





    with open(
        CACHE_FILE,
        "r"
    ) as file:


        return json.load(file)







def save_cache(data):


    with open(

        CACHE_FILE,

        "w"

    ) as file:


        json.dump(

            data,

            file,

            indent=4

        )







# ==========================
# SIGNAL COUNTER
# ==========================


def get_signal_number():


    data = load_cache()


    today = datetime.now().strftime(

        "%Y-%m-%d"

    )



    if data["date"] != today:


        data = {


            "date":today,


            "signal":1


        }


        save_cache(data)


        return 1




    return data["signal"]







def increase_signal_number():


    data = load_cache()



    today = datetime.now().strftime(

        "%Y-%m-%d"

    )




    if data["date"] != today:


        data = {


            "date":today,


            "signal":1


        }



    else:


        data["signal"] += 1




    save_cache(data)

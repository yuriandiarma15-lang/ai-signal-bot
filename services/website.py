import aiohttp

from config.settings import WEBSITE_URL, API_KEY


async def send_signal_to_website(signal):

    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:

        async with session.post(
            WEBSITE_URL,
            json=signal,
            headers=headers
        ) as response:

            print(await response.text())

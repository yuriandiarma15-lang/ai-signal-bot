import aiohttp
from config.settings import WEBSITE_URL, API_KEY


async def send_signal_to_website(signal):
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    async with aiohttp.ClientSession() as session:
        await session.post(
            WEBSITE_URL,
            json=signal,
            headers=headers
        )

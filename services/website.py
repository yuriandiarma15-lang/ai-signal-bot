import aiohttp
from config.settings import WEBSITE_URL


async def send_to_website(signal):

    async with aiohttp.ClientSession() as session:

        await session.post(
            WEBSITE_URL,
            json=signal
        )

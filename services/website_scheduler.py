import asyncio
from datetime import datetime

import pytz

from services.pending import (
    load_pending_signal,
    clear_pending_signal
)

from services.website import (
    send_signal_to_website
)


WIB = pytz.timezone(
    "Asia/Jakarta"
)


async def website_scheduler():

    print(
        "🌐 WEBSITE SCHEDULER ACTIVE"
    )

    last_hour = None

    while True:

        now = datetime.now(WIB)

        # Jalankan tepat di menit 00 setiap jam
        if now.minute == 0 and now.hour != last_hour:

            last_hour = now.hour

            signal = load_pending_signal()

            if signal:

                print(
                    "📤 MENGIRIM SIGNAL KE WEBSITE..."
                )

                success = await send_signal_to_website(
                    signal
                )

                if success:

                    clear_pending_signal()

                    print(
                        "✅ WEBSITE UPDATE BERHASIL"
                    )

                else:

                    print(
                        "❌ WEBSITE UPDATE GAGAL"
                    )

            else:

                print(
                    "📭 TIDAK ADA SIGNAL PENDING"
                )

        await asyncio.sleep(
            20
        )

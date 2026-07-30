import asyncio

from services.pending import (
    get_ready_signals,
    mark_as_sent,
    clean_sent
)

from services.website import (
    send_signal_to_website
)


async def website_scheduler():

    print(
        "🌐 WEBSITE SCHEDULER ACTIVE"
    )

    while True:

        ready = get_ready_signals()

        for item in ready:

            print(
                "📤 MENGIRIM SIGNAL KE WEBSITE..."
            )

            success = await send_signal_to_website(
                item["signal"]
            )

            if success:

                mark_as_sent(
                    item["signal"]
                )

                print(
                    "✅ WEBSITE UPDATE BERHASIL"
                )

            else:

                print(
                    "❌ WEBSITE UPDATE GAGAL"
                )

        clean_sent()

        await asyncio.sleep(
            30
        )

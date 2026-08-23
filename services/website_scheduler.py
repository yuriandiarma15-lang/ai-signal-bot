import asyncio
import logging

from services.pending import (
    get_ready_signals,
    mark_as_sent,
    clean_sent,
)

from services.website import (
    send_signal_to_website,
)


# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger(
    "website_scheduler"
)


# =========================================================
# LOCK
# =========================================================

_website_running = False


# =========================================================
# PROCESS READY SIGNAL
# =========================================================

async def process_ready_signal(
    item
):
    """
    Kirim satu signal yang sudah waktunya
    dipublikasikan ke website.
    """

    signal = item.get(
        "signal"
    )

    if not signal:

        logger.warning(
            "Pending signal kosong. Dilewati."
        )

        return False

    logger.info(
        "📤 MENGIRIM SIGNAL KE WEBSITE..."
    )

    # =====================================================
    # SEND
    # =====================================================

    try:

        success = await send_signal_to_website(
            signal
        )

    except Exception:

        logger.exception(
            "Website send error."
        )

        return False

    # =====================================================
    # SUCCESS
    # =====================================================

    if success:

        try:

            mark_as_sent(
                signal
            )

        except Exception:

            logger.exception(
                "Signal berhasil dikirim website "
                "tetapi gagal ditandai sebagai sent."
            )

            return False

        logger.info(
            "✅ WEBSITE UPDATE BERHASIL"
        )

        return True

    # =====================================================
    # FAILED
    # =====================================================

    logger.warning(
        "❌ WEBSITE UPDATE GAGAL. "
        "Signal tetap disimpan untuk retry."
    )

    return False


# =========================================================
# WEBSITE SCHEDULER
# =========================================================

async def website_scheduler():
    """
    Mengecek pending_signal.json secara berkala.

    Signal yang sudah mencapai send_at akan dikirim
    ke website.

    Jika website gagal:
        signal TIDAK dihapus
        signal akan dicoba kembali pada pengecekan berikutnya.
    """

    global _website_running

    logger.info(
        "=========================================="
    )

    logger.info(
        "🌐 WEBSITE SCHEDULER ACTIVE"
    )

    logger.info(
        "Website delay: +1 JAM"
    )

    logger.info(
        "Check interval: 30 detik"
    )

    logger.info(
        "=========================================="
    )

    while True:

        # =================================================
        # PREVENT OVERLAPPING
        # =================================================

        if _website_running:

            logger.warning(
                "Website scheduler masih berjalan. "
                "Cycle dilewati."
            )

            await asyncio.sleep(
                5
            )

            continue

        _website_running = True

        try:

            # =============================================
            # GET READY
            # =============================================

            try:

                ready = get_ready_signals()

            except Exception:

                logger.exception(
                    "Gagal membaca pending signals."
                )

                ready = []

            # =============================================
            # NO SIGNAL
            # =============================================

            if not ready:

                logger.debug(
                    "Tidak ada signal website yang siap."
                )

            # =============================================
            # PROCESS
            # =============================================

            else:

                logger.info(
                    "📋 Ada %s signal siap dikirim "
                    "ke website.",
                    len(ready)
                )

                for item in ready:

                    try:

                        await process_ready_signal(
                            item
                        )

                    except Exception:

                        logger.exception(
                            "Error memproses "
                            "pending signal."
                        )

                    # -------------------------------------
                    # Jeda kecil antar signal
                    # -------------------------------------

                    await asyncio.sleep(
                        1
                    )

            # =============================================
            # CLEAN SENT
            # =============================================

            try:

                clean_sent()

            except Exception:

                logger.exception(
                    "Gagal membersihkan signal terkirim."
                )

        except asyncio.CancelledError:

            logger.info(
                "Website scheduler dihentikan."
            )

            raise

        except Exception:

            logger.exception(
                "ERROR WEBSITE SCHEDULER"
            )

        finally:

            _website_running = False

        # =================================================
        # WAIT
        # =================================================

        await asyncio.sleep(
            30
        )

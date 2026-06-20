import asyncio
import logging
from contextlib import suppress

from application import Application

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


async def main() -> None:
    application = Application()
    shutdown_event = asyncio.Event()

    try:
        await application.start()
        logger.info("Server listening on ws://%s:%d", application.host, application.port)
        await shutdown_event.wait()
    except asyncio.CancelledError:
        logger.info("Main task cancelled")
    except Exception:
        logger.exception("Fatal error during server execution")
        raise
    finally:
        logger.info("Beginning shutdown")
        with suppress(Exception):
            await application.stop()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")

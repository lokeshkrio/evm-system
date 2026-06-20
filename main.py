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
    app = Application()

    try:
        await app.start()
        await app.run()
    except asyncio.CancelledError:
        logger.info("Main task cancelled")
    except Exception:
        logger.exception("Fatal error during server execution")
        raise
    finally:
        logger.info("Beginning shutdown")
        with suppress(Exception):
            await app.stop()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")

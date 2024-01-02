import asyncio
from Bioz import Bioz
from webhook.webhook import app
from threading import Thread
from utils.logging_utils import setup_logger
from config import BOT_TOKEN

bot = Bioz()


async def main():
    await bot.start(BOT_TOKEN)

if __name__ == '__main__':
    setup_logger("discord")
    setup_logger("werkzeug")
    logger = setup_logger(__name__)
    try:
        t = Thread(target=app.run, kwargs={
            'host': '0.0.0.0', 'port': 5000, 'debug': False}, daemon=True).start()
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Keyboard Interrupt detected. Exiting...')

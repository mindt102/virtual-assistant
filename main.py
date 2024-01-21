import asyncio
from Bioz import Bioz
from webhook.webhook import app
from threading import Thread
from utils.logging_utils import setup_logger
from config import BOT_TOKEN
from waitress import serve
from paste.translogger import TransLogger

bot = Bioz()


async def main():
    await bot.start(BOT_TOKEN)

if __name__ == '__main__':
    setup_logger("discord")
    setup_logger("werkzeug")
    setup_logger("waitress")
    setup_logger("wsgi")
    logger = setup_logger(__name__)
    try:
        t = Thread(target=serve, args=(TransLogger(app, setup_console_handler=False),),kwargs={
            'host': '0.0.0.0', 'port': 5000}, daemon=True).start()
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Keyboard Interrupt detected. Exiting...')

import asyncio
import aiohttp
from discord.ext import commands, tasks
import discord
from utils import french_utils
from utils.logging_utils import setup_logger
from utils.logging_utils import unexpected_error_handler
from config import BOT_QUEUE, CALLBACK_URL, FEEDBACK_TIMEOUT, EASYFRENCH_PLAYLISTID
import utils.youtube_utils as youtube_utils
from views.youtube.VideoView import VideoView
import datetime


class UtilsCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = setup_logger(__name__)
        self.queue_handlers = {
            "youtube": youtube_utils.queue_handler
        }

    @commands.hybrid_command(
        description="Ping the bot",
        brief="Check whether Bot is working properly"
    )
    async def ping(self, ctx: commands.Context):
        await ctx.send('Pong!', delete_after=15)

    @commands.hybrid_command(
        description="Delete all messages in the channel",
        brief="Delete all messages in the channel"
    )
    async def clear(self, ctx: commands.Context):
        his_len = 1
        while his_len > 0:
            await ctx.send("Deleting messages...", delete_after=FEEDBACK_TIMEOUT)
            await ctx.message.channel.purge()
            await asyncio.sleep(2)
            try:
                his_len = len(await ctx.channel.history().flatten())
            except AttributeError as e:
                his_len = 0

    @ tasks.loop(hours=1)
    async def webhook_check(self):
        channel = discord.utils.get(
            self.bot.get_all_channels(),
            guild__name='Bot',
            name='debug'
        )
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(CALLBACK_URL) as resp:
                    if resp.status != 200:
                        self.logger.critical(
                            f"Webhook callback returned {resp.status}")
                        await channel.send(f"Webhook callback returned {resp.status}")
                    else:
                        self.logger.info("Webhook callback returned 200")
        except aiohttp.client_exceptions.ClientConnectorError as e:
            await channel.send(f"Cannot connect to webhook callback")
            unexpected_error_handler(self.logger, e)
        except Exception as e:
            await channel.send(f"Webhook callback check errored")
            unexpected_error_handler(self.logger, e)

    @ commands.Cog.listener()
    async def on_ready(self):
        self.queue_check.start()
        self.webhook_check.start()

async def setup(bot: commands.Bot):
    await bot.add_cog(UtilsCogs(bot))

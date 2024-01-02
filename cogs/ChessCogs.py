import re
import aiohttp
import discord
from discord.ext import commands, tasks

from utils.logging_utils import setup_logger, unexpected_error_handler


class ChessCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = setup_logger(__name__)

    @commands.hybrid_command(
        description="Check whether chess feature is working properly",
        brief="Ping the chess feature"
    )
    async def chessping(self, ctx: commands.Context):
        await ctx.send("chesspong", delete_after=15)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        channel = discord.utils.get(
            self.bot.get_all_channels(), guild__name='Bot', name='chess')
        if not channel:
            self.logger.critical("Channel not found")
            return
        if message.channel != channel:
            return
        
        self.logger.info("Received message in chess channel")

        if '[Site "Chess.com"]' in message.content:
            # msg = """"""
            try:
                # pgn = re.search(r"^[^\[]+$", message.content,
                #                 re.MULTILINE).group()
                pgn = message.content
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                    async with session.post("https://lichess.org/api/import", headers={"Accept": "application/json"}, data={"pgn": pgn}) as resp:
                        self.logger.info("Sending POST request to Lichess with data: " + pgn)
                        resp_data = await resp.json()
                        self.logger.info("Lichess import returned: " + str(resp))
                        if resp.status != 200:
                            self.logger.critical(
                                f"Lichess import returned {resp_data}, {resp.status}, {resp.reason}")
                            await message.channel.send(f"Analysis failed", delete_after=5, ephemeral=True)
                        else:
                            self.logger.info("Lichess import returned 200")
                            await message.channel.send(f"Analysed game: {resp_data['url']}")
            except Exception as e:
                unexpected_error_handler(
                    self.logger, e, message=message.content, resp=resp)
        else:
            self.logger.info("Message not in PGN format")

async def setup(bot: commands.Bot):
    await bot.add_cog(ChessCogs(bot))

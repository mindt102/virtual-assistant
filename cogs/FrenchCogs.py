import datetime
import discord
from discord.ext import commands, tasks
from config import EASYFRENCH_PLAYLISTID, FEEDBACK_TIMEOUT, RESULT_TIMEOUT
from utils import french_utils, youtube_utils

from utils.logging_utils import setup_logger, unexpected_error_handler
from views.french.FrenchView import FrenchView
from views.french.PlaylistConfirmView import PlaylistConfirmView
from views.french.PlaylistsView import PlaylistsView
from views.youtube.VideoView import VideoView
from queries.french_queries import get_playlists, get_random_playlist, get_video_by_id

class FrenchCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = setup_logger(__name__)
        self.daily_french.start()


    @commands.hybrid_group(
        description="Display help",
        brief="Display help for French commands",
        fallback="help"
    )
    async def french(self, ctx: commands.Context):
        try:
            await ctx.send_help(ctx.command)
        except Exception as e:
            await ctx.send("Server error", delete_after=5, ephemeral=True)
            unexpected_error_handler(self.logger, e)

    @french.command(
        description="Send a random French video from selected playlists",
        brief="Send a random French video"
    )
    async def random(self, ctx: commands.Context = None):
        try:
            await ctx.defer()
            video = await french_utils.random_video()
            if not ctx:
                channel = discord.utils.get(
                    self.bot.get_all_channels(),
                    guild__name='Bot',
                    name='french'
                )
            else:
                channel = ctx

            await channel.send(
                content=f"Daily French ({youtube_utils.duration_to_str(video['duration'])}): {youtube_utils.videoId_to_url(video['_id'])}",
                view=FrenchView(video_id=video["_id"])
            )
        except Exception as e:
            await ctx.send("Server error", delete_after=FEEDBACK_TIMEOUT, ephemeral=True)
            unexpected_error_handler(self.logger, e)

    @french.command(
        name="playlists",
        description="Display all playlists",
        brief="Display all playlists"
    )
    async def playlists(self, ctx: commands.Context):
        try:
            async with ctx.typing(ephemeral=True):
                per_page = 25
                playlists = get_playlists(limit=per_page)
                if len(playlists) == 0:
                    await ctx.send("No playlists found", delete_after=FEEDBACK_TIMEOUT, ephemeral=True)
                else:
                    await ctx.send(
                        content=french_utils.playlistId_to_url(playlists[0]["_id"]),
                        view=PlaylistsView(playlists),
                        delete_after=RESULT_TIMEOUT,
                        ephemeral=True
                    )
        except Exception as e:
            await ctx.send("Server error", delete_after=FEEDBACK_TIMEOUT, ephemeral=True)
            unexpected_error_handler(self.logger, e)


    @french.command(
        name="addplaylist",
        description="Add a playlist",
        brief="Add a playlist"
    )
    async def addplaylist(self, ctx: commands.Context, playlist_id: str):
        try:
            await ctx.send(
                content=f"Add {french_utils.playlistId_to_url(playlist_id)} to playlists",
                view=PlaylistConfirmView(playlist_id),
                delete_after=RESULT_TIMEOUT,
                ephemeral=True
            )
        except Exception as e:
            await ctx.send("Server error", delete_after=FEEDBACK_TIMEOUT, ephemeral=True)
            unexpected_error_handler(self.logger, e)

    @tasks.loop(time=datetime.time(0, 0, 0))
    async def daily_french(self):
        await self.random(None)


async def setup(bot: commands.Bot):
    await bot.add_cog(FrenchCogs(bot))
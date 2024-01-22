from discord.ext import commands, tasks
import discord
import datetime
from config import FEEDBACK_TIMEOUT, RESULT_TIMEOUT
from queries.youtube_queries import get_channels
from utils.logging_utils import setup_logger, unexpected_error_handler
from google_auth_creds import get_googleapi_credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.youtube_utils import channelId_to_url, find_missing_videos, resubscribe, videoId_to_url
from views.youtube.SubConfirmView import SubConfirmView
from views.youtube.VideoView import VideoView
from views.youtube.YoutubeChannelsView import YoutubeChannelsView


class YoutubeCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = setup_logger(__name__)
        self.resub_loop.start()

    @commands.hybrid_group(
        description="Display help",
        brief="Display help for Youtube commands",
        fallback="help"
    )
    async def youtube(self, ctx: commands.Context):
        try:
            await ctx.send_help(ctx.command)
        except Exception as e:
            await ctx.send("Server error", delete_after=5, ephemeral=True)
            unexpected_error_handler(self.logger, e)

    @youtube.command(
        name="channels",
        description="Manage Youtube channels",
        brief="Manage Youtube channels"
    )
    async def list_channels(self, ctx: commands.Context):
        try:
            async with ctx.typing(ephemeral=True):
                per_page = 25
                channels = get_channels(limit=per_page)
                await ctx.send(
                    content=channelId_to_url(channels[0]["_id"]),
                    view=YoutubeChannelsView(
                        channels),
                    delete_after=RESULT_TIMEOUT,
                    ephemeral=True
                )
        except Exception as e:
            await ctx.send("Server error", delete_after=FEEDBACK_TIMEOUT, ephemeral=True)
            unexpected_error_handler(self.logger, e)

    @youtube.command(
        name="subscribe",
        description="Add a channel",
        brief="Subscribe to a Youtube channel"
    )
    async def sub(self, ctx: commands.Context, channel_id: str):
        try:
            await ctx.send(
                content=f"Subscribe to {channelId_to_url(channel_id)}",
                view=SubConfirmView(channel_id),
                delete_after=RESULT_TIMEOUT,
                ephemeral=True
            )
        except Exception as e:
            await ctx.send("Server error", delete_after=FEEDBACK_TIMEOUT, ephemeral=True)
            unexpected_error_handler(self.logger, e)

    @youtube.command(
        description="Search for a channel",
        brief="Search for a Youtube channel"
    )
    async def search(self, ctx: commands.Context, *, query: str):
        self.logger.info(f"Searching for '{query}'...")
        interaction: discord.Interaction = ctx.interaction
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            with build('youtube', 'v3', credentials=get_googleapi_credentials()) as youtube:
                request = youtube.search().list(
                    part="snippet",
                    maxResults=5,
                    q=query,
                    type="channel"
                )
                response = request.execute()
                channels = [{
                    "_id": channel["snippet"]["channelId"],
                    "title": channel["snippet"]["title"]
                } for channel in response["items"]]
                res = await interaction.followup.send(
                    content=channelId_to_url(channels[0]["_id"]),
                    view=YoutubeChannelsView(channels, subscribed=False),
                    ephemeral=True,
                    wait=True
                )
                await res.delete(delay=RESULT_TIMEOUT)
        except discord.errors.HTTPException as e:
            res = await interaction.followup.send("Error searching for channel", wait=True, ephemeral=True)
            unexpected_error_handler(self.logger, e, channels=channels, title_lengths=[
                                     len(channel["title"]) for channel in channels])
            await res.delete(delay=FEEDBACK_TIMEOUT)
        except Exception as e:
            res = await interaction.followup.send("Server error", ephemeral=True, wait=True)
            unexpected_error_handler(self.logger, e)
            await res.delete(delay=FEEDBACK_TIMEOUT)

    @youtube.command(
        description="Find missing videos",
        brief="Find missing videos due to server issues"
    )
    async def missing(self, ctx: commands.Context):
        try:
            self.logger.info("Finding missing videos...")
            await ctx.send("Finding missing videos...", ephemeral=True, delete_after=FEEDBACK_TIMEOUT)
            await find_missing_videos()
            await ctx.send("Finished finding missing videos", ephemeral=True, delete_after=FEEDBACK_TIMEOUT)
        except HttpError as e:
            await ctx.send("Possible quota exceeded", delete_after=FEEDBACK_TIMEOUT, ephemeral=True)
            unexpected_error_handler(self.logger, e)
        except Exception as e:
            await ctx.send("Server error", delete_after=FEEDBACK_TIMEOUT, ephemeral=True)
            unexpected_error_handler(self.logger, e)

    @youtube.command(
        description="Resubscribe",
        brief="Manually unsubscribe and subscribe to all channels"
    )
    async def resub(self, ctx: commands.Context):
        try:
            self.logger.info("Resubbing to Youtube channels...")
            await ctx.send("Resubbing to Youtube channels...", ephemeral=True, delete_after=FEEDBACK_TIMEOUT)
            await resubscribe()
            await ctx.send("Finished resubbing to Youtube channels", ephemeral=True, delete_after=FEEDBACK_TIMEOUT)
        except Exception as e:
            await ctx.send("Server error", delete_after=FEEDBACK_TIMEOUT, ephemeral=True)
            unexpected_error_handler(self.logger, e)

    @ commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author == self.bot.user:
            return
        
        if msg.content.startswith("https://www.youtube.com/watch?v="):
            try:
                video_id = msg.content[len("https://www.youtube.com/watch?v="):]
                await msg.delete()
                channel = msg.channel
                await channel.send(
                    content=f"You shared: {videoId_to_url(video_id)}",
                    view=VideoView(video_id=video_id, no_db_log=True)
                )
            except Exception as e:
                unexpected_error_handler(self.logger, e, msg=msg.content)

        if msg.content.startswith("https://youtu.be/"):
            try:
                video_id = msg.content[len("https://youtu.be/"):]
                await msg.delete()
                channel = msg.channel
                await channel.send(
                    content=f"You shared: {videoId_to_url(video_id)}",
                    view=VideoView(video_id=video_id, no_db_log=True)
                )
            except Exception as e:
                unexpected_error_handler(self.logger, e, msg=msg.content)

    @ tasks.loop(time=datetime.time(hour=0, minute=0, second=0))
    async def resub_loop(self):
        try:
            await resubscribe()
            self.logger.info("Finished auto resub")
        except Exception as e:
            unexpected_error_handler(self.logger, e)


async def setup(bot: commands.Bot):
    await bot.add_cog(YoutubeCogs(bot))

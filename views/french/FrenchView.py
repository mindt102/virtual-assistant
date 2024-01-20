import discord
from discord.ui import view, button
from config import FEEDBACK_TIMEOUT
from utils import french_utils, youtube_utils
from utils.logging_utils import setup_logger, unexpected_error_handler

from queries.youtube_queries import update_watched_at


class FrenchView(view.View):
    def __init__(self, video_id: str, no_db_log: bool = False):
        super().__init__(timeout=None)
        self.video_id = video_id
        self.no_db_log = no_db_log
        self.logger = setup_logger(__name__)

    @button(label="Done", style=discord.ButtonStyle.success)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.edit_message(content="👌", view=None, delete_after=FEEDBACK_TIMEOUT)
            if not self.no_db_log:
                update_watched_at(self.video_id)
        except Exception as e:
            await interaction.response.send_message(f"Server Error", ephemeral=True)
            unexpected_error_handler(self.logger, e)

    @button(label="Next", style=discord.ButtonStyle.primary)
    async def nextvid(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer(thinking=True, ephemeral=True)
            video = await french_utils.random_video()
            await interaction.followup.send(
                content=f"{youtube_utils.videoId_to_url(video['_id'])}",
                view=FrenchView(video_id=video["_id"], no_db_log=True),
                ephemeral=True,
                wait=True
            )
        except Exception as e:
            await interaction.response.send_message(f"Server Error", ephemeral=True)
            unexpected_error_handler(self.logger, e)

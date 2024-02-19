import discord
from discord.ui import view, button, Modal, TextInput
from config import FEEDBACK_TIMEOUT
from utils.logging_utils import setup_logger, unexpected_error_handler

from queries.youtube_queries import update_watched_at

class PauseTimeModal(Modal):
    timestamp = TextInput(
        label="Timestamp", placeholder="Colon seperated timestamp (e.g.: 1:02:03)", style=discord.TextStyle.short)

    def __init__(self, view, **kwargs):
        super().__init__(**kwargs)
        self.view: VideoView = view
        # logger.info(f"View: {id(self.view)}")
        # logger.info(f"Self view: {id(self.view)}")

    async def on_submit(self, interaction: discord.Interaction):
        # Convert timestamp to seconds
        timestamp = self.timestamp.value.split(":")
        if len(timestamp) == 3:
            seconds = int(timestamp[0])*3600 + int(timestamp[1])*60 + int(timestamp[2])
        elif len(timestamp) == 2:
            seconds = int(timestamp[0])*60 + int(timestamp[1])
        elif len(timestamp) == 1:
            seconds = int(timestamp[0])
        else:
            await interaction.response.send_message("Invalid timestamp", ephemeral=True, delete_after=FEEDBACK_TIMEOUT)
            return
        # Extract the duration located inside parentheses from the message
        message = interaction.message.content
        start = message.find("[")
        end = message.find("]")
        duration = "[]"
        if start != -1 and end != -1:
            duration = message[start:end+1]
        await interaction.response.edit_message(content=duration + f"https://www.youtube.com/watch?v={self.view.video_id}&t={seconds}", view=self.view)


class VideoView(view.View):
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

    @button(label="Skip", style=discord.ButtonStyle.primary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.edit_message(content="⏩", view=None, delete_after=FEEDBACK_TIMEOUT)
        except Exception as e:
            await interaction.response.send_message(f"Server Error", ephemeral=True)
            unexpected_error_handler(self.logger, e)

    @button(label="Pause", style=discord.ButtonStyle.secondary)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_modal(PauseTimeModal(title="Timestamp to pause", view=self))
        except Exception as e:
            await interaction.response.send_message(f"Server Error", ephemeral=True)
            unexpected_error_handler(self.logger, e)
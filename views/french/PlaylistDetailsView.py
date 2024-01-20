from typing import Any
import discord
from discord.ui import View, button
from discord.ui.item import Item
from config import FEEDBACK_TIMEOUT
from queries.french_queries import get_playlist_by_id, remove_playlist

from utils.logging_utils import setup_logger, unexpected_error_handler
logger = setup_logger(__name__)

class PlaylistDetailsView(View):
    def __init__(self, playlist_id: str, **kwargs):
        super().__init__(**kwargs)
        self.playlist = get_playlist_by_id(playlist_id)
    
    @button(style=discord.ButtonStyle.success, label="Finish")
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.edit_message(content="👌", view=None, delete_after=FEEDBACK_TIMEOUT)
        except Exception as e:
            await interaction.response.send_message(f"Server Error", ephemeral=True)
            unexpected_error_handler(self.logger, e)

    @button(style=discord.ButtonStyle.blurple, label="Random")
    async def random(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.edit_message(content="🎲", view=None, delete_after=FEEDBACK_TIMEOUT)
        except Exception as e:
            await interaction.response.send_message(f"Server Error", ephemeral=True)
            unexpected_error_handler(self.logger, e)
    
    @button(style=discord.ButtonStyle.danger, label="Remove")
    async def remove(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.edit_message(content=f"Removing playlist: {self.playlist['title']}", view=None, delete_after=FEEDBACK_TIMEOUT)
            result = remove_playlist(playlist_id=self.playlist["_id"])
            if result.deleted_count == 1:
                res = await interaction.followup.send(content=f"Removed playlist: {self.playlist['title']}", ephemeral=True, wait=True)
                logger.info(f"Removed playlist: {self.playlist}")
            else:
                res = await interaction.followup.send(content=f"Failed to remove playlist: {self.playlist['title']}", ephemeral=True, wait=True)
                raise Exception("Failed to remove playlist")
        except Exception as e:
            res = await interaction.followup.send(content=f"Server error", ephemeral=True, wait=True)
            unexpected_error_handler(logger, e, playlist=self.playlist, result=result)
        finally:
            await res.delete(delay=FEEDBACK_TIMEOUT)
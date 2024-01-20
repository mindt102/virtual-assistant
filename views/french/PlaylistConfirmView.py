import discord
from discord.ui import View, Button
from queries.french_queries import add_playlist
from utils.french_utils import request_playlistTitle_by_id
from utils.logging_utils import setup_logger, unexpected_error_handler


class PlaylistConfirmView(View):
    def __init__(self, playlist_id: str):
        super().__init__()
        self.playlist_id = playlist_id
        self.logger = setup_logger(__name__)

    @discord.ui.button(label="Add", style=discord.ButtonStyle.green)
    async def add_handler(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            title = request_playlistTitle_by_id(self.playlist_id)
            if not title:
                res = await interaction.followup.send("Playlist not found", ephemeral=True, wait=True)
            else:
                playlist = {
                    "_id": self.playlist_id,
                    "title": title,
                }
                self.logger.info(f"Adding {playlist}")
                add_playlist(playlist=playlist)
                res = await interaction.followup.send(f"Added {playlist['title']}", ephemeral=True, wait=True)
        except ValueError:
            res = await interaction.followup.send("Already added", ephemeral=True, wait=True)
        except Exception as e:
            res = await interaction.followup.send("Server error", ephemeral=True, wait=True)
            unexpected_error_handler(self.logger, e)
        finally:
            # await interaction.message.delete()
            await res.delete(delay=5)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel_handler(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
        await interaction.response.send_message("Cancelled", ephemeral=True, delete_after=5)
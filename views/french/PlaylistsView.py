import discord
from discord.ui import View, Button, Select
from config import FEEDBACK_TIMEOUT, RESULT_TIMEOUT
from queries.french_queries import add_playlist, get_playlist_by_id, remove_playlist
from utils import french_utils, youtube_utils
from utils.french_utils import playlistId_to_url

from utils.logging_utils import setup_logger, unexpected_error_handler
from views.french.PlaylistDetailsView import PlaylistDetailsView
from views.youtube.VideoView import VideoView

logger = setup_logger(__name__)

class RemoveButton(Button):
    def __init__(self, select, **kwargs):
        self.select = select
        super().__init__(label="Remove", style=discord.ButtonStyle.red, **kwargs)
    async def callback(self, interaction: discord.Interaction):
        try:
            _id, title = self.select.values[0].split("::")
            playlist = {
                    "_id": _id,
                    "title": title
            }
            logger.info(f"Removing playlist: {playlist}")
            await interaction.response.edit_message(content=f"Removing playlist: {playlist['title']}", view=None, delete_after=FEEDBACK_TIMEOUT)
            result = remove_playlist(playlist_id=playlist["_id"])
            if result.deleted_count == 1:
                res = await interaction.followup.send(content=f"Removed playlist: {playlist['title']}", ephemeral=True, wait=True)
                logger.info(f"Removed playlist: {playlist}")
            else:
                res = await interaction.followup.send(content=f"Failed to remove playlist: {playlist['title']}", ephemeral=True, wait=True)
                raise Exception("Failed to remove playlist")
        except Exception as e:
            res = await interaction.followup.send(content=f"Server error", ephemeral=True, wait=True)
            unexpected_error_handler(logger, e, playlist=playlist, result=result)
        finally:
            await res.delete(delay=FEEDBACK_TIMEOUT)

class RandomButton(Button):
    def __init__(self, select, **kwargs):
        self.select = select
        super().__init__(label="Details", style=discord.ButtonStyle.green, **kwargs)
    
    async def callback(self, interaction: discord.Interaction):
        try:
            _id, title = self.select.values[0].split("::")
            logger.info(f"Randoming video from playlist: {title}")
            await interaction.response.defer(thinking=True, ephemeral=True)
            
            video = await french_utils.random_video(playlists=[_id])

            await interaction.followup.send(
                content=f"Random video from {title}: {youtube_utils.videoId_to_url(video['_id'])}",
                view=VideoView(video_id=video["_id"], no_db_log=True),
                ephemeral=True,
                wait=True
            )
        except Exception as e:
            res = await interaction.followup.send(content=f"Server error", ephemeral=True, wait=True)
            unexpected_error_handler(logger, e, _id=_id, title=title)
            await res.delete(delay=FEEDBACK_TIMEOUT)
        
class PlaylistsView(View):
    def __init__(self, playlists: list[dict[str, str]], **kwargs):
        super().__init__(**kwargs)
        
        self.select = Select(
            placeholder="Select a playlist",
            row=0,
        )

        for playlist in playlists:
            label = playlist["title"]
            value = f"{playlist['_id']}::{playlist['title']}"
            self.select.add_option(label=label, value=value)
        
        self.select.callback = self.on_select_option
        self.add_item(self.select)

        self.default_index = 0
        self.set_selected_option(self.default_index)

        self.add_item(RandomButton(self.select))
        self.add_item(RemoveButton(self.select))

    def set_selected_option(self, index: int):
        self.select.options[self.default_index].default = False
        self.select.options[index].default = True
        self.default_index = index
        self.select.values.clear()
        self.select.values.append(self.select.options[index].value)

    async def on_select_option(self, interaction: discord.Interaction):
        try:
            selected_value = self.select.values[0]
            for index, option in enumerate(self.select.options):
                if option.value == selected_value:
                    self.set_selected_option(index)
                    break
            _id, _ = selected_value.split("::")
            await interaction.response.edit_message(
                content=playlistId_to_url(_id),
                view=self
            )
        except Exception as e:
            await interaction.message.delete()
            await interaction.response.send_message(content="Server error", ephemeral=True, delete_after=FEEDBACK_TIMEOUT)
            unexpected_error_handler(logger, e, selected_value=selected_value)
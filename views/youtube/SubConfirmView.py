import discord
from discord.ui import View, Button
from utils.logging_utils import setup_logger, unexpected_error_handler

from utils.youtube_utils import request_channelTitle_by_id, subscribe


class SubConfirmView(View):
    def __init__(self, channel_id: str):
        super().__init__()
        self.channel_id = channel_id
        self.logger = setup_logger(__name__)

    @discord.ui.button(label="Subscribe", style=discord.ButtonStyle.green)
    async def subscribe_handler(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            title = request_channelTitle_by_id(self.channel_id)
            if not title:
                res = await interaction.followup.send("Channel not found", ephemeral=True, wait=True)
            else:
                channel = {
                    "_id": self.channel_id,
                    "title": title
                }
                self.logger.info(f"Subscribing to {channel}")
                await subscribe(channel=channel)
                res = await interaction.followup.send(f"Subscribed to {channel['title']}", ephemeral=True, wait=True)
        except ValueError:
            res = await interaction.followup.send("Already subscribed", ephemeral=True, wait=True)
        except Exception as e:
            res = await interaction.followup.send("Server error", ephemeral=True, wait=True)
            unexpected_error_handler(self.logger, e)
        finally:
            await interaction.message.delete()
            await res.delete(delay=5)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel_handler(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
        await interaction.response.send_message("Cancelled", ephemeral=True, delete_after=5)

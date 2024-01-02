import math
import discord
from discord.ui import Select, View, Button
from config import FEEDBACK_TIMEOUT, RESULT_TIMEOUT
from utils.logging_utils import setup_logger, unexpected_error_handler
from utils.youtube_utils import subscribe
import json
from queries.youtube_queries import get_channels, get_channels_count

from utils.youtube_utils import channelId_to_url, unsubscribe
from views.youtube.ChannelKeywordView import ChannelKeywordView

logger = setup_logger(__name__)


class SubscribeButton(Button):
    def __init__(self, select, **kwargs):
        self.select = select
        super().__init__(label="Subscribe", style=discord.ButtonStyle.green, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        try:
            _id, title = self.select.values[0].split("::")
            channel = {
                "_id": _id,
                "title": title
            }
            logger.info(f"Subscribing to {channel}")
            # await interaction.response.edit_message(content="Subscribing...", view=None, delete_after=FEEDBACK_TIMEOUT)
            await interaction.response.defer(thinking=True, ephemeral=True)
            await subscribe(channel=channel)
            res = await interaction.followup.send(f"Subscribed to {channel['title']}", ephemeral=True, wait=True)
        except ValueError:
            res = await interaction.followup.send("Already subscribed", ephemeral=True, wait=True)
        except Exception as e:
            res = await interaction.followup.send("Server error", ephemeral=True, wait=True)
            unexpected_error_handler(logger, e)
        finally:
            await res.delete(delay=FEEDBACK_TIMEOUT)


class UnsubscribeButton(Button):
    def __init__(self, select, **kwargs):
        self.select = select
        super().__init__(label="Unsubscribe", style=discord.ButtonStyle.red, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        try:
            _id, title = self.select.values[0].split("::")
            channel = {
                "_id": _id,
                "title": title
            }
            logger.info(f"Unsubscribing from {channel}")
            await interaction.response.edit_message(content="Unsubscribing...", view=None, delete_after=FEEDBACK_TIMEOUT)
            await unsubscribe(channel_id=channel["_id"])
            res = await interaction.followup.send(f"Unsubscribed from {channel['title']}", ephemeral=True, wait=True)
        except ValueError:
            res = await interaction.followup.send("Not subscribed", ephemeral=True, wait=True)
        except Exception as e:
            res = await interaction.followup.send("Server error", ephemeral=True, wait=True)
            unexpected_error_handler(logger, e)
        finally:
            await res.delete(delay=FEEDBACK_TIMEOUT)


class DetailsButton(Button):
    def __init__(self, select, **kwargs):
        self.select = select
        super().__init__(label="Details", style=discord.ButtonStyle.green, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        try:
            _id, title = self.select.values[0].split("::")
            logger.info(f"Showing details for {title}")
            await interaction.response.defer(thinking=True, ephemeral=True)
            res = await interaction.followup.send(
                content=f"{channelId_to_url(_id)}",
                view=ChannelKeywordView(channel_id=_id),
                ephemeral=True,
                wait=True,
            )
            await res.delete(delay=RESULT_TIMEOUT)
        except Exception as e:
            res = await interaction.followup.send("Server error", ephemeral=True, wait=True)
            unexpected_error_handler(logger, e)
            await res.delete(delay=FEEDBACK_TIMEOUT)


class NextButton(Button):
    def __init__(self, select, **kwargs):
        self.select = select
        super().__init__(emoji="⏭️", style=discord.ButtonStyle.grey, row=2, ** kwargs)

    async def callback(self, interaction: discord.Interaction):
        # try:
        if True:
            # await interaction.response.edit_message(
            #     content="Loading...", view=None, delete_after=FEEDBACK_TIMEOUT)
            await interaction.response.defer(thinking=True, ephemeral=True)
            select: Select = self.select
            view: YoutubeChannelsView = self.view

            if view.page == 1:
                view.prev_button.disabled = False

            view.page += 1
            view.page_button.update_label()

            end_title = select.options[-1].label

            channels = get_channels(start_title=end_title, limit=view.per_page)

            # self.select.options.clear()
            # for channel in channels:
            #     self.select.options.append(discord.SelectOption(
            #         label=channel["title"],
            #         value=f"{channel['_id']}::{channel['title']}"
            #     ))
            view.init_options(channels)
            view.set_selected_option(0)

            if view.page == view.page_count:
                self.disabled = True

            res = await interaction.followup.send(
                content=channelId_to_url(channels[0]["_id"]),
                view=view,
                ephemeral=True,
                wait=True,
            )
            await res.delete(delay=RESULT_TIMEOUT)
        # except Exception as e:
        #     res = await interaction.followup.send("Server error", ephemeral=True)
        #     unexpected_error_handler(logger, e)
        #     await res.delete(delay=FEEDBACK_TIMEOUT)


class PrevButton(Button):
    def __init__(self, select, **kwargs):
        self.select = select
        super().__init__(emoji="⏮️", style=discord.ButtonStyle.grey, row=2, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.edit_message(
                content="Loading...", view=None, delete_after=FEEDBACK_TIMEOUT)
            select: Select = self.select
            view: YoutubeChannelsView = self.view

            if view.page == view.page_count:
                view.next_button.disabled = False

            view.page -= 1
            view.page_button.update_label()

            start_title = select.options[0].label

            channels = get_channels(
                start_title=start_title, limit=view.per_page, reverse=True)

            view.init_options(reversed(channels))
            view.set_selected_option(0)

            if view.page == 1:
                self.disabled = True

            res = await interaction.followup.send(
                content=channelId_to_url(channels[-1]["_id"]),
                view=view,
                ephemeral=True,
                wait=True,
            )
            await res.delete(delay=RESULT_TIMEOUT)
        except Exception as e:
            res = await interaction.followup.send("Server error", ephemeral=True)
            unexpected_error_handler(logger, e)
            await res.delete(delay=FEEDBACK_TIMEOUT)


class PageButton(Button):
    def __init__(self, page_count, **kwargs):
        super().__init__(
            label=f"1/{page_count}", style=discord.ButtonStyle.blurple, row=2, **kwargs)
        self.disabled = True

    def update_label(self):
        self.label = f"{self.view.page}/{self.view.page_count}"


class YoutubeChannelsView(View):
    def __init__(self, channels: list[dict[str, str]], subscribed: bool = True):
        super().__init__()

        self.select = Select(
            placeholder="Select a channel",
            row=0
        )
        self.init_options(channels)
        self.select.callback = self.on_select_option
        self.add_item(self.select)

        self.default_index = 0
        self.set_selected_option(self.default_index)

        if not subscribed:
            self.add_item(SubscribeButton(select=self.select))
        else:
            self.per_page = len(channels)
            self.page_count = math.ceil(get_channels_count() / self.per_page)
            self.page = 1

            self.prev_button = PrevButton(select=self.select)
            self.prev_button.disabled = True
            self.add_item(self.prev_button)

            self.page_button = PageButton(page_count=self.page_count)
            self.add_item(self.page_button)

            self.add_item(DetailsButton(select=self.select))
            self.add_item(UnsubscribeButton(select=self.select))

            self.next_button = NextButton(select=self.select)
            self.add_item(self.next_button)

    def set_selected_option(self, index: int):
        self.select.options[self.default_index].default = False
        self.select.options[index].default = True
        self.default_index = index
        # if len(self.select.values) == 0:
        self.select.values.clear()
        self.select.values.append(self.select.options[index].value)
        # logger.info(f"Select values: {self.select.values}")

    async def on_select_option(self, interaction: discord.Interaction):
        try:
            selected_value = self.select.values[0]
            for index, option in enumerate(self.select.options):
                if option.value == selected_value:
                    self.set_selected_option(index)
                    break
            _id, _ = selected_value.split("::")
            await interaction.response.edit_message(
                content=channelId_to_url(_id),
                view=self
            )
        except Exception as e:
            await interaction.message.delete()
            await interaction.response.send_message("Server error", ephemeral=True, delete_after=5)
            unexpected_error_handler(logger, e)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item):
        unexpected_error_handler(logger, error)
        res = await interaction.followup.send(content="Server error", ephemeral=True, wait=True)
        await res.delete(delay=FEEDBACK_TIMEOUT)

    def init_options(self, channels: list[dict[str, str]]):
        self.select.options.clear()
        for channel in channels:
            label = channel["title"]
            if "keywords" in channel and channel["keywords"]:
                label += " | " + ", ".join(channel["keywords"])

            value = f"{channel['_id']}::{channel['title']}"

            self.select.options.append(discord.SelectOption(
                label=label,
                value=value
            ))

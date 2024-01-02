from discord.ui import Button, Modal, View, TextInput
import discord
from config import FEEDBACK_TIMEOUT, RESULT_TIMEOUT
from queries.youtube_queries import get_channel_by_id, update_channel_by_id
from utils.logging_utils import setup_logger, unexpected_error_handler
from utils.youtube_utils import channelId_to_url, check_keywords, request_videos_by_channelId


logger = setup_logger(__name__)


class AddButton(Button):
    def __init__(self, **kwargs):
        super().__init__(label="Add keywords", style=discord.ButtonStyle.green, row=1, **kwargs)

    async def callback(self, interaction):
        await self.view.on_add(interaction)


class DeleteButton(Button):
    def __init__(self, **kwargs):
        super().__init__(label="Delete keywords",
                         style=discord.ButtonStyle.red, row=1, **kwargs)

    async def callback(self, interaction):
        await self.view.on_delete(interaction)


class TestButton(Button):
    def __init__(self, **kwargs):
        super().__init__(label="Test keywords",
                         style=discord.ButtonStyle.blurple, row=1, **kwargs)

    async def callback(self, interaction):
        await self.view.on_test(interaction)


class PromptKeywordsModal(Modal):
    keywords = TextInput(
        label="Keywords", placeholder="Comma separated keywords", style=discord.TextStyle.short)

    def __init__(self, view, **kwargs):
        super().__init__(**kwargs)
        self.view: ChannelKeywordView = view
        logger.info(f"View: {id(self.view)}")
        logger.info(f"Self view: {id(self.view)}")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="Adding...", view=None, delete_after=FEEDBACK_TIMEOUT)
        keywords = list(map(str.strip, self.keywords.value.split(",")))
        self.view.add_keywords(keywords)
        logger.info(
            f"Added keywords {keywords} to channel {self.view.channel['title']}")
        res = await interaction.followup.send(content=f"{channelId_to_url(self.view.channel['_id'])}", view=self.view, ephemeral=True, wait=True)
        await res.delete(delay=RESULT_TIMEOUT)


class ChannelKeywordView(View):
    def __init__(self, channel_id):
        super().__init__(timeout=RESULT_TIMEOUT)
        self.channel: dict[str, str] = get_channel_by_id(channel_id)
        if not self.channel:
            logger.critical(f"Channel {channel_id} not found")
            raise Exception(f"Channel {channel_id} not found")

        self.add_item(AddButton())

        if "keywords" in self.channel and len(self.channel["keywords"]) > 0:
            self.init_select()
        else:
            self.select = None

    async def on_add(self, interaction: discord.Interaction):
        # try:
        await interaction.response.send_modal(PromptKeywordsModal(title="Add keywords", view=self))
        # except Exception as e:
        #     unexpected_error_handler(logger, e)
        #     await interaction.response.send_message(content="Server error", view=None, ephemeral=True, delete_after=FEEDBACK_TIMEOUT)

    async def on_delete(self, interaction: discord.Interaction):
        # try:
        await interaction.response.edit_message(content="Deleting...", view=None, delete_after=FEEDBACK_TIMEOUT)
        logger.info(
            f"Deleting {self.select.values} from {self.channel['title']}")
        self.remove_keywords(self.select.values)

        res = await interaction.followup.send(content=f"{channelId_to_url(self.channel['_id'])}", view=self, ephemeral=True, wait=True)
        await res.delete(delay=RESULT_TIMEOUT)
        # except Exception as e:
        #     unexpected_error_handler(logger, e)
        #     res = await interaction.followup.send(content="Server error", view=None, ephemeral=True, wait=True)
        #     await res.delete(delay=FEEDBACK_TIMEOUT)

    async def on_test(self, interaction: discord.Interaction):
        keywords = self.select.values or self.channel["keywords"]

        await interaction.response.defer(thinking=True, ephemeral=True)
        logger.info(
            f"Testing {keywords} from {self.channel['title']}")

        videos = request_videos_by_channelId(self.channel["_id"])

        description = ""
        for item in videos:
            title = item["snippet"]["title"]
            icon = "✅" if check_keywords(title, keywords) else "🔳"
            description += f"{icon} {title}\n"

        embed = discord.Embed(
            title=f"Keywords: {', '.join(keywords)}",
            description=description,
            color=discord.Color.blurple()
        )

        res = await interaction.followup.send(embed=embed, ephemeral=True, wait=True)
        await res.delete(delay=RESULT_TIMEOUT)

    async def on_select_option(self, interaction: discord.Interaction):
        # try:
        await interaction.response.defer()
        logger.info(f"Selected {interaction.data['values']}")
        # except Exception as e:
        #     unexpected_error_handler(logger, e)
        #     await interaction.response.send_message(content="Server error", view=None, ephemeral=True, delete_after=FEEDBACK_TIMEOUT)

    async def on_error(self, interaction: discord.Interaction[discord.Client], error: Exception, item):
        unexpected_error_handler(logger, error)
        res = await interaction.followup.send(content="Server error", ephemeral=True, wait=True)
        await res.delete(delay=FEEDBACK_TIMEOUT)

    def add_keywords(self, keywords: list[str]):
        if "keywords" not in self.channel:
            self.channel["keywords"] = keywords
        else:
            self.channel["keywords"] = list(
                set(self.channel["keywords"] + keywords))

        update_channel_by_id(self.channel["_id"], self.channel)
        self.update_view()

    def remove_keywords(self, keywords: list[str]):
        if "keywords" not in self.channel:
            logger.critical(
                f"Channel {self.channel['_id']} has no keywords to delete")
            return
        self.channel["keywords"] = list(
            set(self.channel["keywords"]) - set(keywords))

        update_channel_by_id(self.channel["_id"], self.channel)
        self.update_view()

    def update_view(self):
        if not self.select:
            self.init_select()
            return

        if len(self.channel["keywords"]) == 0:
            self.remove_item(self.select)
            self.remove_item(self.delete_button)
            self.remove_item(self.test_button)

            del self.select, self.delete_button, self.test_button
            return

        self.select.options.clear()
        self.select.values.clear()

        for keyword in self.channel["keywords"]:
            self.select.options.append(discord.SelectOption(
                label=keyword, value=keyword))
        self.select.max_values = len(self.channel["keywords"])

    def init_select(self):
        self.select = discord.ui.Select(
            placeholder="Keywords to filter titles",
            options=[discord.SelectOption(
                label=keyword, value=keyword) for keyword in self.channel["keywords"]],
            min_values=1,
            max_values=len(self.channel["keywords"]),
            row=0
        )
        self.select.callback = self.on_select_option
        self.add_item(self.select)

        self.test_button = TestButton()
        self.add_item(self.test_button)

        self.delete_button = DeleteButton()
        self.add_item(self.delete_button)

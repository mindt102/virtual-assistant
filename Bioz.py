import discord
from discord.ext import commands
from utils.logging_utils import setup_logger
from utils.logging_utils import unexpected_error_handler

extensions = ["cogs.UtilsCogs", "cogs.YoutubeCogs", "cogs.ChessCogs", "cogs.FrenchCogs"]


class Bioz(commands.Bot):
    def __init__(self, *args, **kwargs):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='?', intents=intents)
        self.logger = setup_logger(__name__)

    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user}")
        channel = discord.utils.get(
            self.get_all_channels(), guild__name='Bot', name='debug')
        await channel.send("I'm ready!", delete_after=5)

    async def setup_hook(self) -> None:
        try:
            for extension in extensions:
                await self.load_extension(extension)
                self.logger.info(f"Loaded {extension}")
            await self.tree.sync()
        except Exception as e:
            unexpected_error_handler(self.logger, e, extension=extension)

    async def on_error(self, event_method: str, /, *args, **kwargs):
        # return await super().on_error(event_method, *args, **kwargs)
        unexpected_error_handler(
            self.logger, event_method, event_method=event_method, args=args, kwargs=kwargs)

    async def on_command_error(self, context: commands.Context, exception: Exception):
        if isinstance(exception, commands.CommandNotFound):
            self.logger.info(f"Command not found: {context.message.content}")
            await context.send("Command not found", delete_after=5, ephemeral=True)
        elif isinstance(exception, commands.MissingRequiredArgument):
            self.logger.info(
                f"Missing required argument: {context.message.content}")
            await context.send_help(context.command, delete_after=5, ephemeral=True)
        else:
            unexpected_error_handler(self.logger, exception)
            await context.send("Server error", delete_after=5, ephemeral=True)
        # return await super().on_command_error(context, exception)

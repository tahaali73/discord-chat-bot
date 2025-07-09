# main.py
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from utils.database import setup_db # Import the setup_db function

# Load environment variables
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Set up logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
logging.basicConfig(level=logging.INFO, handlers=[handler], format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

# Set up Discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Ensure this is enabled in your bot's Discord Developer Portal

# Initialize bot
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")
    print("Bot is online and connected to Discord!")
    logging.info(f"Bot is online and connected as {bot.user.name}")
    await setup_db() # Ensure the database is set up when the bot starts

    # Dynamically load all cogs from the 'cogs' folder
    # This loop will go through each .py file in the 'cogs' directory
    # and attempt to load it as a cog.
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logging.info(f"Successfully loaded cog: {filename[:-3]}")
                print(f"Loaded cog: {filename[:-3]}")
            except Exception as e:
                logging.error(f"Failed to load cog {filename[:-3]}: {e}", exc_info=True)
                print(f"Failed to load cog {filename[:-3]}: {e}")

    # You can also manually load cogs if you prefer
    # await bot.load_extension('cogs.general')
    # await bot.load_extension('cogs.moderation')
    # await bot.load_extension('cogs.ai_features')

@bot.event
async def on_command_error(ctx, error):
    # This is a global error handler for commands not handled by specific cog error handlers
    if isinstance(error, commands.CommandNotFound):
        # await ctx.send("Sorry, I don't know that command.", delete_after=5) # Optional: uncomment if you want to respond to unknown commands
        logging.warning(f"Command not found: {ctx.message.content} by {ctx.author}")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing arguments. Usage: `{ctx.command.usage}`" if ctx.command.usage else f"Missing arguments. Please check `!help {ctx.command.name}`.")
        logging.warning(f"Missing arguments for {ctx.command.name} by {ctx.author}")
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.author.send("This command cannot be used in private messages.")
    elif isinstance(error, commands.DisabledCommand):
        await ctx.send("This command is disabled.")
    else:
        logging.error(f"Unhandled command error in {ctx.command.name} by {ctx.author}: {error}", exc_info=True)
        await ctx.send("An unexpected error occurred while running this command.")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
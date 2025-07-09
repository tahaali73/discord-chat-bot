# cogs/general.py
import discord
from discord.ext import commands
import logging

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.secret_role = "Gamer" # Define here or pass from main if dynamic

    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(
            title=f"🦧 Welcome to OrangutanX Labs, {member.name}!",
            description="Thanks for joining the jungle!",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="About Us",
            value="""🎮 Utilities for NFT Holders
            Daily Free Spins (SpinLoot)
            Weekly Jackpots
            Earn SPL tokens by holding, chatting, spinning, and raiding
            Leaderboard & raffle rewards
            More features coming soon!""",
            inline=False
        )
        embed.add_field(
            name="Collections",
            value="""💎 OrangutanX OG – Free mint (333 supply)
            XOXO – Paid mint via GOTM Labs (333 supply)""",
            inline=False
        )
        embed.add_field(
            name="Explore",
            value="""🌐 Website: https://orangutanx.com
            Buy NFTs: https://magiceden.io/marketplace/orangutanx""",
            inline=False
        )
        embed.add_field(
            name="Get Started",
            value="Type !help anytime to learn more about utilities, rewards, or how to get started.",
            inline=False
        )
        embed.set_footer(text="🎯 Let the spins begin — good luck! 🍀")
        try:
            await member.send(embed=embed)
            logging.info(f"Sent welcome DM to {member.name}")
        except discord.Forbidden:
            logging.warning(f"Could not send welcome DM to {member.name} (DMs probably disabled).")

    @commands.command()
    async def hello(self, ctx):
        await ctx.send(f"Hello {ctx.author.mention}!")
        logging.info(f"{ctx.author} used !hello command.")

    @commands.command()
    async def assign(self, ctx):
        role = discord.utils.get(ctx.guild.roles, name=self.secret_role)
        if role:
            try:
                await ctx.author.add_roles(role)
                await ctx.send(f"{ctx.author.mention} is now assigned to {self.secret_role}")
                logging.info(f"{ctx.author} assigned to role {self.secret_role}")
            except discord.Forbidden:
                await ctx.send("I don't have permission to assign roles.")
                logging.error(f"Bot lacks permissions to assign role {self.secret_role}")
            except Exception as e:
                await ctx.send(f"Error assigning role: {e}")
                logging.error(f"Error assigning role for {ctx.author}: {e}", exc_info=True)
        else:
            await ctx.send("Role doesn't exist.")
            logging.warning(f"Attempted to assign non-existent role: {self.secret_role}")

    @commands.command()
    async def remove(self, ctx):
        role = discord.utils.get(ctx.guild.roles, name=self.secret_role)
        if role:
            try:
                await ctx.author.remove_roles(role)
                await ctx.send(f"{ctx.author.mention} has had the {self.secret_role} removed")
                logging.info(f"{ctx.author} removed from role {self.secret_role}")
            except discord.Forbidden:
                await ctx.send("I don't have permission to remove roles.")
                logging.error(f"Bot lacks permissions to remove role {self.secret_role}")
            except Exception as e:
                await ctx.send(f"Error removing role: {e}")
                logging.error(f"Error removing role for {ctx.author}: {e}", exc_info=True)
        else:
            await ctx.send("Role doesn't exist.")
            logging.warning(f"Attempted to remove non-existent role: {self.secret_role}")

    @commands.command()
    async def dm(self, ctx, *, msg):
        try:
            await ctx.author.send(f"You said: {msg}")
            await ctx.send("DM sent!")
            logging.info(f"Sent DM to {ctx.author}: {msg}")
        except discord.Forbidden:
            await ctx.send(f"Could not DM {ctx.author.mention}. They might have DMs disabled.")
            logging.warning(f"Could not send DM to {ctx.author} (DMs probably disabled).")
        except Exception as e:
            await ctx.send(f"Error sending DM: {e}")
            logging.error(f"Error sending DM to {ctx.author}: {e}", exc_info=True)

    @commands.command()
    async def reply(self, ctx):
        await ctx.reply("This is a reply to your message!")
        logging.info(f"{ctx.author} used !reply command.")

    @commands.command()
    async def poll(self, ctx, *, question):
        embed = discord.Embed(title="New Poll", description=question, color=discord.Color.blue())
        try:
            poll_message = await ctx.send(embed=embed)
            await poll_message.add_reaction("👍")
            await poll_message.add_reaction("👎")
            logging.info(f"Poll created by {ctx.author}: {question}")
        except Exception as e:
            await ctx.send(f"Error creating poll: {e}")
            logging.error(f"Error creating poll for {ctx.author}: {e}", exc_info=True)

    @commands.command()
    @commands.has_role("Gamer") # Use the actual role name here
    async def secret(self, ctx):
        await ctx.send("Welcome to the club!")
        logging.info(f"{ctx.author} accessed secret command.")

    @secret.error
    async def secret_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send(f"{ctx.author.mention}, you do not have permission to do that! You need the '{self.secret_role}' role.")
            logging.warning(f"{ctx.author} tried to use secret command without role.")
        else:
            logging.error(f"Error in secret command for {ctx.author}: {error}", exc_info=True)
            await ctx.send(f"An error occurred with the secret command: {error}")

async def setup(bot):
    await bot.add_cog(General(bot))
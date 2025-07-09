# cogs/moderation.py
import discord
from discord.ext import commands
import logging
import datetime
from utils.database import get_user_violations, update_user_violations, reset_user_violations # Import DB functions

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ALLOWED_ROLES_FOR_LINKS = ["Trusted Member", "Moderator", "Server Staff"]
        self.FORBIDDEN_WORDS = ["shit"] # You can expand this list

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from the bot itself
        if message.author == self.bot.user:
            return

        # --- Link & Forbidden Word Moderation Logic (Guild Channels Only) ---
        if not isinstance(message.channel, discord.DMChannel):
            content_lower = message.content.lower()

            # Check for forbidden words
            for word in self.FORBIDDEN_WORDS:
                if word in content_lower:
                    try:
                        await message.delete()
                        await message.channel.send(f"{message.author.mention} - Don't use that word!", delete_after=5)
                        logging.info(f"Deleted forbidden word '{word}' from {message.author} in {message.channel}: {message.content}")
                        return # Stop processing if message deleted
                    except discord.Forbidden:
                        logging.error(f"Bot lacks permissions to delete message from {message.author} in {message.channel}")
                        # Optionally, alert an admin or log to a specific channel
                    except Exception as e:
                        logging.error(f"Error deleting message with forbidden word: {e}", exc_info=True)
                    return # Stop processing if message was deleted

            # Check for links
            has_link = "http://" in content_lower or "https://" in content_lower or "www." in content_lower

            if has_link:
                is_admin = message.author.guild_permissions.administrator
                has_allowed_role = False
                if message.author.roles:
                    for role in message.author.roles:
                        if role.name in self.ALLOWED_ROLES_FOR_LINKS:
                            has_allowed_role = True
                            break

                if not is_admin and not has_allowed_role:
                    try:
                        await message.delete()
                        logging.info(f"Deleted disallowed link from {message.author} in {message.channel}: {message.content}")

                        user_id = message.author.id
                        user_data = await get_user_violations(user_id)
                        current_violations = user_data["violations"] if user_data else 0

                        if current_violations == 0:
                            await message.channel.send(
                                f"{message.author.mention}, links are not allowed in this channel. "
                                f"This is your first warning. Further attempts will result in a timeout.",
                                delete_after=10
                            )
                            await update_user_violations(user_id, 1, discord.utils.utcnow().isoformat())
                            logging.info(f"Issued first warning to {message.author} for disallowed link.")
                        else:
                            timeout_end = discord.utils.utcnow() + datetime.timedelta(days=1)
                            if isinstance(message.author, discord.Member):
                                await message.author.timeout(timeout_end, reason="Sent disallowed link after warning")
                                await message.channel.send(
                                    f"{message.author.mention}, links are still not allowed. "
                                    f"You have been timed out for 24 hours due to repeated violations. "
                                    f"Please review the server rules or contact staff if you believe this is an error.",
                                    delete_after=20
                                )
                                await reset_user_violations(user_id)
                                logging.info(f"Timed out {message.author} for 24 hours (violation #{current_violations + 1}) in {message.channel}: {message.content}")
                            else:
                                await message.channel.send(
                                    f"{message.author.mention}, links are not allowed in this channel. "
                                    f"A timeout would have been applied, but there was an issue. Please contact staff.",
                                    delete_after=15
                                )
                                logging.warning(f"Could not timeout {message.author} (not a discord.Member object) after repeated link violations.")

                        return # Stop processing if it was a disallowed link
                    except discord.Forbidden:
                        logging.error(f"Bot lacks permissions to delete message or timeout user ({message.author}) in {message.channel}. "
                                      f"Ensure bot has 'Manage Messages' and 'Moderate Members' permissions and higher role position.")
                        await message.channel.send(
                            f"I tried to enforce link rules for {message.author.mention}, "
                            f"but I don't have the necessary permissions. Please ensure I have 'Manage Messages' and 'Moderate Members'.",
                            delete_after=20
                        )
                    except Exception as e:
                        logging.error(f"Error handling link violation for {message.author}: {e}", exc_info=True)
                        await message.channel.send(
                            f"An unexpected error occurred while trying to enforce rules for {message.author.mention}.",
                            delete_after=10
                        )
                    return # Stop processing if deletion/timeout was attempted
        
        # Don't forget to allow other on_message listeners/commands to process
        # For cogs, you typically don't call bot.process_commands(message) here
        # unless you specifically want to prevent normal command processing after your on_message logic.
        # Since your AI features will be in another Cog's on_message, let the bot handle it.
        await self.bot.process_commands(message)

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member):
        """Removes a timeout from a specified user.
        Usage: !untimeout @username
        """
        try:
            if member.timed_out_until is None:
                await ctx.send(f"{member.mention} is not currently timed out.")
                return

            await member.timeout(None, reason=f"Timeout removed by {ctx.author.name}")
            await ctx.send(f"Timeout removed for {member.mention}.")
            logging.info(f"Timeout removed for {member.name} by {ctx.author.name}")
            
            # Reset their violation count in your database as they've been manually un-timed out
            await reset_user_violations(member.id)
            logging.info(f"Violation count for {member.name} reset due to manual untimeout.")

        except discord.Forbidden:
            await ctx.send(f"I don't have permission to remove timeouts for {member.mention}. "
                           f"Please ensure my role is above theirs and I have the 'Moderate Members' permission.")
            logging.error(f"Bot lacks permissions to untimeout {member.name} for {ctx.author.name}")
        except discord.HTTPException as e:
            await ctx.send(f"An error occurred while trying to untimeout {member.mention}: {e}")
            logging.error(f"HTTPException when untimeouting {member.name}: {e}", exc_info=True)
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")
            logging.error(f"Unexpected error when untimeouting {member.name}: {e}", exc_info=True)

    @untimeout.error
    async def untimeout_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(f"{ctx.author.mention}, you don't have permission to use this command. "
                           f"You need the 'Moderate Members' permission.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a user to untimeout, e.g., `!untimeout @username`")
        else:
            logging.error(f"Error in untimeout command for {ctx.author}: {error}", exc_info=True)
            await ctx.send(f"An error occurred: {error}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
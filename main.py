import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from huggingface_hub import InferenceClient
from vector_store import add_knowledge, list_all_knowledge, query_knowledge
import uuid

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
HF_TOKEN = os.getenv("HF_TOKEN")


llm_client = InferenceClient(
    model="meta-llama/Llama-3.1-8B-Instruct",
    token=HF_TOKEN,
)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

secret_role = "Gamer"

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")
    print("Bot is online and connected to Discord!")

@bot.event
async def on_member_join(member):
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
    await member.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Check if the message is a DM
    if isinstance(message.channel, discord.DMChannel):
        print(f"Received DM from {message.author}: {message.content}")
        # Handle DM logic here
        await message.channel.typing()
        # Query knowledge base with metadata filtering
        context_docs = query_knowledge(
            message.content,
            n_results=5,
            where={"type": {"$in": ["rule", "faq", "about", "mission", "vision", "future_plan", "nft", "ecosystem", "utility", "governance", "community", "gameplay", "info"]}}
        )
        print(f"Retrieved context_docs from vector store: {context_docs}")
        if not context_docs:
            context_str = "No relevant information was found in the server knowledge base."
            print("No relevant context found in KB.")
        else:
            context_str = "\n".join([f"- {doc.strip()}" for doc in context_docs])
            print(f"Constructed context_str for LLM:\n{context_str}")
        # Prompt structured with SYSTEM + CONTEXT + USER
        messages_for_llm = [
            {
                "role": "system",
                "content": "You are a Discord bot assistant for the OrangutanX community. Your primary goal is to provide helpful and accurate information based solely on the provided 'Server Knowledge'. If the 'Server Knowledge' does not contain the answer, you must state 'I don't have enough information from the server knowledge to answer that.' Do not use external knowledge."
            },
            {
                "role": "system",
                "content": f"Server Knowledge:\n{context_str}"
            },
            {
                "role": "user",
                "content": message.content
            }
        ]
        print(f"Messages sent to LLM: {messages_for_llm}")
        try:
            response = llm_client.chat.completions.create(
                messages=messages_for_llm
            )
            reply_text = response.choices[0].message.content
            print(f"LLM Reply: {reply_text}")
            await message.channel.send(reply_text)
        except Exception as e:
            print(f"Error calling LLM: {e}")
            await message.channel.send("I encountered an error trying to process that. Please try again later.")
    else:
        # Handle guild channel logic here
        if "shit" in message.content.lower():
            await message.delete()
            await message.channel.send(f"{message.author.mention} - Don't use that word!")
            return
        # Use LLaMA if bot is mentioned
        if bot.user.mentioned_in(message):
            print(f"Bot mentioned in message from {message.author}: {message.content}")
            await message.channel.typing()
            # Get the message content without mentions
            cleaned_query = message.clean_content
            # Remove the bot's own name if it's at the beginning (e.g., "@Wompti XOXO nft" becomes "XOXO nft")
            cleaned_query = cleaned_query.replace(f"@{bot.user.name}", "").strip()
            print(f"Cleaned query for vector store: '{cleaned_query}'")
            # Query knowledge base with metadata filtering
            context_docs = query_knowledge(
                cleaned_query,
                n_results=5,
                where={"type": {"$in": ["rule", "faq", "about", "mission", "vision", "future_plan", "nft", "ecosystem", "utility", "governance", "community", "gameplay", "info"]}}
            )
            print(f"Retrieved context_docs from vector store: {context_docs}")
            if not context_docs:
                context_str = "No relevant information was found in the server knowledge base."
                print("No relevant context found in KB.")
            else:
                context_str = "\n".join([f"- {doc.strip()}" for doc in context_docs])
                print(f"Constructed context_str for LLM:\n{context_str}")
            # Prompt structured with SYSTEM + CONTEXT + USER
            messages_for_llm = [
                {
                    "role": "system",
                    "content": "You are a Discord bot assistant for the OrangutanX community. Your primary goal is to provide helpful and accurate information based solely on the provided 'Server Knowledge'. If the 'Server Knowledge' does not contain the answer, you must state 'I don't have enough information from the server knowledge to answer that.' Do not use external knowledge."
                },
                {
                    "role": "system",
                    "content": f"Server Knowledge:\n{context_str}"
                },
                {
                    "role": "user",
                    "content": cleaned_query
                }
            ]
            print(f"Messages sent to LLM: {messages_for_llm}")
            try:
                response = llm_client.chat.completions.create(messages=messages_for_llm)
                reply_text = response.choices[0].message.content
                print(f"LLM Reply: {reply_text}")
                await message.channel.send(f"{message.author.mention} {reply_text}")
            except Exception as e:
                print(f"Error calling LLM: {e}")
                await message.channel.send(f"{message.author.mention} I encountered an error trying to process that. Please try again later.")
    
    # This line should be outside the if/else block for on_message,
    # and typically at the very end of the on_message function
    # to ensure commands are processed even if the message isn't a DM or a bot mention.
    # If it's intended to only process commands for specific message types, keep it nested.
    await bot.process_commands(message)

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")
    
@bot.command()
async def teach(ctx, *, fact):
    doc_id = str(uuid.uuid4())[:8]
    metadata = {
        "type": "user_teach",
        "taught_by": ctx.author.name,
        "source": "discord"
    }
    try:
        add_knowledge(doc_id, fact, metadata)
        await ctx.send(f"Thanks {ctx.author.mention}, I’ve learned something new!")
    except Exception as e:
        await ctx.send(f"Error saving: {e}")


@bot.command()
async def assign(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} is now assigned to {secret_role}")
    else:
        await ctx.send("Role doesn't exist")

@bot.command()
async def remove(ctx):
    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.remove_roles(role)
        await ctx.send(f"{ctx.author.mention} has had the {secret_role} removed")
    else:
        await ctx.send("Role doesn't exist")

@bot.command()
async def dm(ctx, *, msg):
    await ctx.author.send(f"You said {msg}")

@bot.command()
async def reply(ctx):
    await ctx.reply("This is a reply to your message!")

@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title="New Poll", description=question)
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")

@bot.command()
@commands.has_role(secret_role)
async def secret(ctx):
    await ctx.send("Welcome to the club!")

@secret.error
async def secret_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("You do not have permission to do that!")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
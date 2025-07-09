# cogs/ai_features.py
import discord
from discord.ext import commands
import logging
from huggingface_hub import InferenceClient
from vector_store import add_knowledge, query_knowledge # Assuming these are correctly implemented
import os
import uuid

class AIFeatures(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.llm_client = InferenceClient(
            model="meta-llama/Llama-3.1-8B-Instruct",
            token=os.getenv("HF_TOKEN"), # Access HF_TOKEN from environment variables
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        # DM Logic
        if isinstance(message.channel, discord.DMChannel):
            logging.info(f"Received DM from {message.author}: {message.content}")
            await message.channel.typing()
            
            context_docs = query_knowledge(
                message.content,
                n_results=5,
                where={"type": {"$in": ["rule", "faq", "about", "mission", "vision", "future_plan", "nft", "ecosystem", "utility", "governance", "community", "gameplay", "info"]}}
            )
            logging.info(f"Retrieved context_docs from vector store: {context_docs}")
            
            context_str = "\n".join([f"- {doc.strip()}" for doc in context_docs]) if context_docs else "No relevant information was found in the server knowledge base."
            logging.info(f"Constructed context_str for LLM:\n{context_str}")

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
            logging.info(f"Messages sent to LLM: {messages_for_llm}")
            
            try:
                response = self.llm_client.chat.completions.create(
                    messages=messages_for_llm,
                    max_new_tokens=500,
                    stop_sequences=["\n\n", "User:", "Bot:"]
                )
                reply_text = response.choices[0].message.content
                logging.info(f"LLM Reply: {reply_text}")
                await message.channel.send(reply_text)
            except Exception as e:
                logging.error(f"Error calling LLM for DM: {e}", exc_info=True)
                await message.channel.send("I encountered an error trying to process that. Please try again later.")
                
        # Bot Mention Logic
        elif self.bot.user.mentioned_in(message):
            logging.info(f"Bot mentioned in message from {message.author}: {message.content}")
            await message.channel.typing()
            
            cleaned_query = message.clean_content.replace(f"@{self.bot.user.name}", "").strip()
            logging.info(f"Cleaned query for vector store: '{cleaned_query}'")

            context_docs = query_knowledge(
                cleaned_query,
                n_results=5,
                where={"type": {"$in": ["rule", "faq", "about", "mission", "vision", "future_plan", "nft", "ecosystem", "utility", "governance", "community", "gameplay", "info"]}}
            )
            logging.info(f"Retrieved context_docs from vector store: {context_docs}")
            
            context_str = "\n".join([f"- {doc.strip()}" for doc in context_docs]) if context_docs else "No relevant information was found in the server knowledge base."
            logging.info(f"Constructed context_str for LLM:\n{context_str}")

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
            logging.info(f"Messages sent to LLM: {messages_for_llm}")
            
            try:
                response = self.llm_client.chat.completions.create(messages=messages_for_llm)
                reply_text = response.choices[0].message.content
                logging.info(f"LLM Reply: {reply_text}")
                await message.channel.send(f"{message.author.mention} {reply_text}")
            except Exception as e:
                logging.error(f"Error calling LLM for mention: {e}", exc_info=True)
                await message.channel.send(f"{message.author.mention} I encountered an error trying to process that. Please try again later.")
        
        # Important: Don't call await self.bot.process_commands(message) here
        # as it will be called by the main bot loop after all on_message listeners.

    @commands.command()
    async def teach(self, ctx, *, fact):
        doc_id = str(uuid.uuid4())[:8]
        metadata = {
            "type": "user_teach",
            "taught_by": ctx.author.name,
            "source": "discord"
        }
        try:
            add_knowledge(doc_id, fact, metadata)
            await ctx.send(f"Thanks {ctx.author.mention}, I’ve learned something new!")
            logging.info(f"Knowledge added by {ctx.author}: {fact}")
        except Exception as e:
            await ctx.send(f"Error saving: {e}")
            logging.error(f"Error adding knowledge by {ctx.author}: {e}", exc_info=True)

async def setup(bot):
    await bot.add_cog(AIFeatures(bot))
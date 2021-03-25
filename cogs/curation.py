import os
import datetime

import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv

load_dotenv()

sugg_vote_channel_id = int(os.getenv('SUGGESTION_VOTE_ID'))
greenlit_sugg_channel_id = int(os.getenv('GREENLIT_SUGGESTION_ID'))

upvote_emoji_id = int(os.getenv('UPVOTE_EMOJI_ID'))
downvote_emoji_id = int(os.getenv('DOWNVOTE_EMOJI_ID'))
greenlit_emoji_id = int(os.getenv('GREENLIT_EMOJI_ID'))
outdated_emoji_id = '\N{SKULL}'

vote_threshold = int(os.getenv('VOTE_THRESHOLD'))
positive_ratio = float(os.getenv('POSITIVE_RATIO'))
outdated_time = int(os.getenv('OUTDATED_AFTER_X_DAYS'))


class Curation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sorting_suggestions.start()

    @commands.Cog.listener("on_message")
    async def add_votes(self, message):
        if message.channel.id != sugg_vote_channel_id:
            return

        if message.author == self.bot.user:
            return
        
        upvote = await message.guild.fetch_emoji(upvote_emoji_id)
        downvote = await message.guild.fetch_emoji(downvote_emoji_id)
        await message.add_reaction(upvote)
        await message.add_reaction(downvote)

    async def work(self, ctx=None):
        sugg_channel = self.bot.get_channel(sugg_vote_channel_id)
        greenlit_channel = self.bot.get_channel(greenlit_sugg_channel_id)
        
        async for message in sugg_channel.history():
            
            upvote_emoji = await message.guild.fetch_emoji(upvote_emoji_id)
            downvote_emoji = await message.guild.fetch_emoji(downvote_emoji_id)
            greenlit_emoji = await message.guild.fetch_emoji(greenlit_emoji_id)
        
            creation_date = message.created_at
            now = datetime.datetime.now()
            difference = now - creation_date
            seconds_passed_since_posted = int(difference.total_seconds())
             
            if len(message.reactions) < 2:
              continue
              
            greenlit = False
            for reaction in message.reactions:
              if type(reaction.emoji) is str:
                continue
              if reaction.emoji.id == greenlit_emoji_id:
                greenlit = True
                
            if greenlit:
              continue
            elif (seconds_passed_since_posted >= (outdated_time + 1) * 86400):
              return
            elif (seconds_passed_since_posted >= outdated_time * 86400):
              await message.add_reaction(outdated_emoji_id)
              continue
            else:
              status = evaluate_ratio(message.reactions[0].count, message.reactions[1].count)

              if ((message.reactions[0].count + message.reactions[1].count) >= vote_threshold) and status == 'positive':
                await message.add_reaction(greenlit_emoji)
                await greenlit_channel.send(
                            'Suggestion by {0} ({2}{3}/{4}{5}).\nLink: {6}'.format(
                                message.author.mention, int(positive_ratio * 100), upvote_emoji, message.reactions[0].count, downvote_emoji, message.reactions[1].count, message.jump_url))
                suggestion_shared = await greenlit_channel.send('> ' + message.content)
                await suggestion_shared.add_reaction(upvote_emoji)
                await suggestion_shared.add_reaction(downvote_emoji)

    @commands.command()
    @commands.has_any_role(610250148525637633, 747283070931042345, 610271966183817236, 824508548640931863)
    async def curate(self, ctx):
        try:
            print("Manual curation requested!")
            await ctx.channel.send("Curation requested, I will evaluate the current suggestions and potentially greenlight some.")
            await self.work(ctx)
        except Exception as e:
            print(str(e))

    @tasks.loop(seconds=1800)
    async def sorting_suggestions(self):
        try:
            now = datetime.datetime.now()
            print(now.hour)
            if now.hour == 6:
              print("It is midnight in EST so I will curate the suggestion channel.")
              await self.work()
        except Exception as e:
            print(str(e))

    @sorting_suggestions.before_loop
    async def bot_startup_stagger(self):
        await self.bot.wait_until_ready()


def evaluate_ratio(a, b):
    if a / (a + b) >= positive_ratio:
        return "positive"
    else:
        return "undecided"


def setup(bot):
    bot.add_cog(Curation(bot))
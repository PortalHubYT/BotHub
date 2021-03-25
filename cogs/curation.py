import os
import datetime

import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv

# This loads the .env values from a separate file
load_dotenv()

# And put these values in python variables
sugg_vote_channel_id = int(os.getenv('SUGGESTION_VOTE_ID'))
greenlit_sugg_channel_id = int(os.getenv('GREENLIT_SUGGESTION_ID'))

upvote_emoji_id = int(os.getenv('UPVOTE_EMOJI_ID'))
downvote_emoji_id = int(os.getenv('DOWNVOTE_EMOJI_ID'))
greenlit_emoji_id = int(os.getenv('GREENLIT_EMOJI_ID'))
outdated_emoji_id = '\N{SKULL}'

vote_threshold = int(os.getenv('VOTE_THRESHOLD'))
positive_ratio = float(os.getenv('POSITIVE_RATIO'))
outdated_time = int(os.getenv('OUTDATED_AFTER_X_DAYS'))


# This class represents the curation process of the bot, it contains the different curation methods that the bot has
class Curation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sorting_suggestions.start()

    # This decorator triger the add_vote function whenever a message is being sent
    @commands.Cog.listener("on_message")
    async def add_votes(self, message):
    
        # It checks that the suggestion is being sent in the right channel (here, the Suggestion channel)
        if message.channel.id != sugg_vote_channel_id:
            return
        
        # And makes sure it wasn't sent by the bot itself
        if message.author == self.bot.user:
            return
        
        # Loads the upvote and downvote emoji on the go, and add them to the message newly sent in Suggestion channel
        upvote = await message.guild.fetch_emoji(upvote_emoji_id)
        downvote = await message.guild.fetch_emoji(downvote_emoji_id)
        await message.add_reaction(upvote)
        await message.add_reaction(downvote)
    
    # This function 'work' is triggered by a loop below in the code, or when the '!curate' command is sent
    async def work(self, ctx=None):
    
        # The bot is loading the two relevant channels it need access to (Suggestion, and Greenlit suggestions) into variables
        # to be used later in the function easily
        sugg_channel = self.bot.get_channel(sugg_vote_channel_id)
        greenlit_channel = self.bot.get_channel(greenlit_sugg_channel_id)
        
        # It then starts iterating on each of the message in "Suggestion" channel, from most recent to oldest
        async for message in sugg_channel.history():
            
            # Loads the emoji it might need to use later in the loop (I reckon this could be placed elsewhere for efficiency sakes)
            upvote_emoji = await message.guild.fetch_emoji(upvote_emoji_id)
            downvote_emoji = await message.guild.fetch_emoji(downvote_emoji_id)
            greenlit_emoji = await message.guild.fetch_emoji(greenlit_emoji_id)
            
            # It's evaluating the time passed since the message was sent
            creation_date = message.created_at
            now = datetime.datetime.now()
            
            difference = now - creation_date
            seconds_passed_since_posted = int(difference.total_seconds())
             
            # Safeguard: if the message has less than two reactions (shouldnt happen) then the bot skips the message
            if len(message.reactions) < 2:
              continue
            
            # Here it checks that he bot has not already greenlit the message or considered it oudated
            # If the message is marked as outdated, it skips to the next message
            greenlit = False
            for reaction in message.reactions:
              if type(reaction.emoji) is str:
                continue
              if reaction.emoji.id == greenlit_emoji_id:
                greenlit = True
             
            # Here is the main process of curation.
            # First it checks if it's already greenlit, if so, it skips the message
            # Then it checks if the message is more than X + 1 days old, in which case it stops the function completely (and won't evaluate more messages)
            # Then it checks if the message is more than X days old, in which case it marks it as "outdated" and skip to the next message
            # Otherwise, it's evaluating the ratio of positive votes, and checks that it has more than VOTE_THRESHOLD votes, if so
            # the bot add a "greenlit" emoji to the message, pass it to the greenlit channel and adds new votes buttons for the nerds
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
    
    # This decorator listen for the command which is stated in the function name (here, "!curate") and makes sure that the person sending it has the approriate role
    @commands.command()
    @commands.has_any_role(610250148525637633, 747283070931042345, 610271966183817236, 824508548640931863)
    async def curate(self, ctx):
        try:
            # If the person sending the command has the approriate role, then it will start the "work" function above, emulating a curation.
            print("Manual curation requested!")
            await ctx.channel.send("Curation requested, I will evaluate the current suggestions and potentially greenlight some.")
            await self.work(ctx)
        except Exception as e:
            print(str(e))
    
    # This decorator is a loop happening every 30 minutes
    @tasks.loop(seconds=1800)
    async def sorting_suggestions(self):
        try:
            # It checks if the the current hour is 6am (which is midnight EST) and if so, it starts the curation process by starting the "work" function
            now = datetime.datetime.now()
            print(now.hour)
            if now.hour == 6:
              print("It is midnight in EST so I will curate the suggestion channel.")
              await self.work()
        except Exception as e:
            print(str(e))
      
    # This is a decorator that executes the decorated function below before the loop above is started, it waits until the bot is ready
    @sorting_suggestions.before_loop
    async def bot_startup_stagger(self):
        await self.bot.wait_until_ready()


# This is the function that is being used the class above that evaluate the ratio of positive votes for a given message
def evaluate_ratio(a, b):
    if a / (a + b) >= positive_ratio:
        return "positive"
    else:
        return "undecided"

# And this is the function that starts the curation 'cog' (= a functionnality of the bot wrapped in a class)
def setup(bot):
    bot.add_cog(Curation(bot))
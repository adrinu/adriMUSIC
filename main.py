from classes.MusicBot import MusicBot
from discord.ext import commands
import os

if __name__ == "__main__":
    bot = commands.Bot(command_prefix="!")
    bot.add_cog(MusicBot(bot))
    bot.run(os.getenv("TOKEN"))
   
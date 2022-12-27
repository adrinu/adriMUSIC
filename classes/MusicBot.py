
import discord
import youtube_dl
from collections import deque
from discord.ext import commands
from settings import YDL_OPTIONS, FFMPEG_OPTIONS
from Track import Track
from Lyrics import Lyrics

class MusicBot(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.q = deque()
        self.current_track = None
    
    @commands.before_invoke
    async def isAuthorConnected(ctx):
        if not ctx.author.voice:
            raise commands.CommandError("🚫 **You must be in a voice channel before running this command!**")

    @commands.command(aliases=['p'])
    async def play(self, ctx, *query):
        query = " ".join(query)
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()
        
        await ctx.send("🔎 __**Looking for the song**__")
        track = Track(query)

        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(track.youtubeURL, download=False)
            url2 = info["formats"][0]["url"]
            track.source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
        
        self.q.append(track)
        if ctx.voice_client.is_playing():
            await ctx.send("☑️ **Added *{}* to the queue!**".format(track.title))
        else: 
            self.current_track = self.q.popleft()
            ctx.voice_client.play(self.current_track.source, after=lambda e: self.play_next(ctx))
            await ctx.send("▶️ **Now playing *{}* **\n{}".format(self.current_track.title, self.current_track.youtubeURL))
    
    def play_next(self, ctx):
        if self.q:
            self.current_track = self.q.popleft()
            ctx.voice_client.play(self.current_track.source, after=lambda e: self.play_next(ctx))
        else:
            self.current_track = None
      
    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        if self.q:
            await ctx.send("__**Queue**__")
            for number, track in enumerate(self.q):
                await ctx.send(">>> {} {} - {}".format(self.convertIntToEmoji(number+1), track.artist, track.title))
        else:
            await ctx.send("**There are no songs queued up!**")

    @commands.command()
    async def remove(self, ctx, number):
        if 0 <= int(number)-1 < len(self.q):
            title = self.q[int(number)-1].title
            self.q.remove(self.q[int(number)-1])
            await ctx.send("**⏏️ Removed the song *{}* from the queue!**".format(title))
        else:
            await ctx.send("{} **in the queue does not exist!**".format(self.convertIntToEmoji(number)))
        
    @commands.command()
    async def disconnect(self, ctx):
        if ctx.voice_client:
            await ctx.send("👋 **Disconnected from voice channel!**")
            await ctx.voice_client.disconnect()
        else:
            await ctx.send("⁉️ Play a song!")
    
    @commands.command()
    async def connect(self, ctx):
        if not ctx.voice_client:
            await ctx.send("👋 **Connected to voice channel!**")
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("🔌 **I'm already connected!**")
    @commands.command()
    async def move(self, ctx, song_to_be_moved, where_to_move):
        self.q.insert(song_to_be_moved, self.q[where_to_move])
        self.q.remove[self.q[where_to_move]]
        await ctx.send("🗳️ **Moved the song!**")
    
    @commands.command()
    async def clear(self, ctx):
        await ctx.send("⏳ **Clearing the queue**")
        while self.q:
            self.q.popleft()
        await ctx.send("⌛ **Queue is cleared!**")
    
    # --------------------------- Current Song Actions --------------------------- #
    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client.is_paused():
            await ctx.send("**The song is already paused!**")
        else:
            ctx.voice_client.pause()
            await ctx.send("⏸ **Song currently paused!**")
    
    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client.is_playing():
            await ctx.send("**The song is already playing!**")
        else:
            ctx.voice_client.resume()
            await ctx.send("▶️ **Resuming song!**")
    
    @commands.command()
    async def lyrics(self, ctx):
        if self.current_track:
            await ctx.send("🏃 **Grabbing the lyrics for the song {}**".format(self.current_track.title))
            lyrics = Lyrics(self.current_track.artist, self.current_track.title).lyric_messages()
            for line in lyrics:
                await ctx.send(">>> {}".format(line))
        else:
            await ctx.send("🚫 **No song is playing!**")

    @commands.command()
    async def stats(self, ctx):
        if self.current_track:
            await ctx.send("__**Song stats**__")
            await ctx.send(">>> 📝 **Title** - {}\n⬆️ **Uploader** - {}\n📅 **Date** - {}\n👀 **Views** - {}\n👍 **Likes** - {}".format(self.current_track.title, self.current_track.channel,self.current_track.publishDate, self.current_track.stats.views, self.current_track.stats.likes))
        else:
            await ctx.send("🚫 **No song is playing!**")
    
    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
        await ctx.send("⏭ **Skipping song**")
        self.play_next(ctx)
    
    @commands.command()
    async def skipto(self, ctx, num):    
        q_num = int(num) - 1
        await ctx.send("⏩ **Skipping to** {}".format(self.q[q_num].title))
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
        while self.q and q_num != 0:
            self.q.popleft()
            q_num -= 1
        self.play_next(ctx)
      
    @commands.command(aliases=["np"])
    async def nowplaying(self, ctx):
        if self.current_track:
            await ctx.send("__**Now Playing**__")
            await ctx.send(">>> **Title**\t{}".format(self.current_track.title))
            await ctx.send(">>> **Artist**\t{}".format(self.current_track.artist))
            await ctx.send(">>> **Features**\t {}".format(", ".join(self.current_track.features)))
        else:
            await ctx.send("**No song is currently playing**")
        
    # ------------------------------- Miscellaneous Commands ------------------------------- #
    
    @commands.command()
    async def sourcecode(self, ctx):
        await ctx.send("{}".format("https://github.com/adrinu/adriMUSIC"))
        
    # ----------------------------- Helper Functions ----------------------------- #
    def convertIntToEmoji(self, num):
        num_to_emojis = {
            "0": "0️⃣",
            "1": "1️⃣",
            "2": "2️⃣",
            "3": "3️⃣",
            "4": "4️⃣",
            "5": "5️⃣",
            "6": "6️⃣",
            "7": "7️⃣",
            "8": "8️⃣",
            "9": "9️⃣",
            "10": "🔟",
        }

        return "".join([num_to_emojis[char] for char in str(num)]) if str(num) != "10" else num_to_emojis["10"]
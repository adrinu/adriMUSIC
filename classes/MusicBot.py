
import discord
import youtube_dl
from collections import deque
from discord.ext import commands
from settings import YDL_OPTIONS, FFMPEG_OPTIONS
from Track import Track
from Lyrics import Lyrics
import random

class MusicBot(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.q = deque()
        self.is_connected = False
        self.current_track = None
        
        self.skips = 0
        self.requested_songs = 0
        self.removed = 0

    @commands.command(aliases=['p'])
    async def play(self, ctx, *query):
        self.requested_songs += 1
        query = " ".join(query)
        if ctx.author.voice:
            if not self.is_connected:
                await ctx.author.voice.channel.connect()
                self.is_connected = True
            if "https://youtube.com" in query:
                await ctx.send("🔎 Seaching for {} on YouTube".format(query))
            else:
                await ctx.send("🔎 Fetching the song")
            
            track = Track(query)

            with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(track.youtubeURL, download=False)
                url2 = info["formats"][0]["url"]
                track.source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
            
            self.q.append(track)
            if ctx.voice_client.is_playing():
                await ctx.send("✔ Added the {}  to the queue!".format(track.title))
            else:
                self.current_track = self.q.popleft()
                ctx.voice_client.play(self.current_track.source, after=lambda e: self.play_next(ctx))
                await ctx.send("Now playing {} by {}\n {}".format(self.current_track.title, self.current_track.artist, self.current_track.youtubeURL))
        else:
            await ctx.send("You need to be in a voice channel to use this command!")
    
    def play_next(self, ctx):
        if len(self.q) > 0:
            self.current_track = self.q.popleft()
            ctx.voice_client.play(self.current_track.source, after=lambda e: self.play_next(ctx))
        else:
            self.current_track = None
      
    @commands.command()
    async def queue(self, ctx):
        if self.current_track:
            await ctx.send("**Currently Playing**: {} by {}".format(self.current_track.title, self.current_track.artist))
        if len(self.q) == 0:
            await ctx.send(">>>**There are no songs queued up ...**")
        else:
            for number, track in enumerate(self.q):
                await ctx.send(">>> **{})** {} - {}".format(number+1, track.artist, track.title))

    @commands.command()
    async def remove(self, ctx, number):
        self.removed += 1
        try:
            title = self.q[int(number)-1].title
            self.q.remove(self.q[int(number)-1])
            await ctx.send("**❌ Removed the song *{}* from the queue!**".format(title))
        except IndexError:
            await ctx.send("#{} in the Queue does not exist!".format(int(number)))
        
    @commands.command()
    async def disconnect(self, ctx):
        try:
            await ctx.voice_client.disconnect()
            await ctx.send("https://tenor.com/view/ight-imma-head-out-spongebob-imma-head-out-ima-head-out-gif-14902967")
        except AttributeError:
            await ctx.send("adriMUSIC has disconnected from the voice channel! Play a song!")
    
    @commands.command()
    async def connect(self, ctx):
        try:
            await ctx.author.voice.channel.connect()
            await ctx.send("https://media2.giphy.com/media/ORjfgiG9ZtxcQQwZzv/giphy.gif")
        except:
            await ctx.send("im already connected")
    @commands.command()
    async def move(self, ctx, q1, q2):
        if (0 < int(q1) < len(q1)) and (0 < int(q2) < len(q1)):
            await ctx.send("Oh oh! One of the songs is out of position in the queue. Try again!")
        else:
            await ctx.send("**Swapping #{} with #{} in the queue!**".format(q1, q2))
            self.q[int(q1)-1], self.q[int(q2)-1] = self.q[int(q2)-1], self.q[int(q1)-1]
    
    @commands.command()
    async def botstats(self, ctx):
        await ctx.send("**__adriMUSIC Bot Stats__**")
        await ctx.send("**Removed Songs** - {}\n**Songs Requested** - {}\n**Songs Skip** - {}".format(self.removed, self.requested_songs, self.skips))
    
    @commands.command()
    async def clear(self, ctx):
        await ctx.send("🚮 **Clearing the queue**")
        while len(self.q) != 0:
            self.q.popleft()
        await ctx.send("**Queue is cleared!")
    
    # --------------------------- Current Song Actions --------------------------- #
    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client.is_paused():
            await ctx.send("The song is already paused!")
        else:
            ctx.voice_client.pause()
            await ctx.send("⏸ Song currently paused!")
    
    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client.is_playing():
            await ctx.send("The song is already playing!")
        else:
            ctx.voice_client.resume()
            await ctx.send("▶ Resuming song!")
    
    @commands.command()
    async def lyrics(self, ctx):
        await ctx.send("🐶 **Fetching the lyrics for the song {}**".format(self.current_track.title))
        if self.current_track:
            lyrics = Lyrics(self.current_track.artist, self.current_track.title)
            for i in lyrics.lyric_messages():
                await ctx.send(">>> {}".format(i))

    @commands.command()
    async def stats(self, ctx):
        if self.current_track:
            await ctx.send("__**Song stats**__")
            await ctx.send(">>> 📝 **Title** - {}\n⬆ **Uploader** - {}\n📅 **Date** - {}\n👀 **Views** - {}\n👍 **Likes** - {}".format(self.current_track.title, self.current_track.channel,self.current_track.publishDate, self.current_track.stats.views, self.current_track.stats.likes))
        else:
            await ctx.send("No song is playing!")
    
    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
        self.skips += 1
        await ctx.send("⏭ **Skipping song**")
        self.play_next(ctx)
    
    @commands.command()
    async def skipto(self, ctx, num):
        q_num = int(num) - 1
        await ctx.send("⏩ **Skipping to** {}".format(self.q[q_num].title))
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
        while len(self.q) != 0 and q_num != 0:
            self.skips += 1
            self.q.popleft()
            q_num -= 1
        self.play_next(ctx)
      
    @commands.command(aliases=["np"])
    async def nowplaying(self, ctx):
        if self.current_track:
         
            await ctx.send("Now Playing")
            await ctx.send("------------------------")
            await ctx.send(">>> **Title** {}".format(self.current_track.title))
            await ctx.send(">>> **Artist** {}".format(self.current_track.artist))
            await ctx.send(">>> **Features** {}".format(", ".join(self.current_track.features)))
        
        else:
            await ctx.send("**No song is currently playing")
        
    # ------------------------------- Fun Commands ------------------------------- #
    @commands.command()
    async def ayo(self, ctx):
        ayos = ["https://tenor.com/view/ayo-ay-yo-gif-24007574", "https://tenor.com/view/angryfan-pause-hold-up-wait-gif-13284505", "https://tenor.com/view/sidetalk-ayo-ayoo-ayooo-glizzy-gif-23903684"]
        await ctx.send(random.choice(ayos))
    
    @commands.command()
    async def sourcecode(self, ctx):
        await ctx.send("Here is the link to code ... {}".format("https://github.com/adrinu/adriMUSIC"))
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import youtube_dl
from collections import deque
from playwright.async_api import async_playwright
import lyricsgenius as lg
import random

load_dotenv()

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
    }
YDL_OPTIONS = {
    "format": "bestaudio"
    }

class Track:
    def __init__(self, artist = "", title = "") -> None:
        # Stats
        self.artist = artist
        self.title = title
        self.uploader = ""
        self.views = ""
        self.likes = ""
        self.upload_date = ""
        
        # Track info
        self.youtube_url = ""
        self.lyrics = ""
        self.source = None
     
    @staticmethod   
    def clean_data(uploader ,full_title):
        unwanted = ["(Official Video)", "(Official Music Video)", "(Official Audio)", 
                    "(OFFICIAL VIDEO)", "(Video Oficial)", "(Audio)", "(Lyrics)", 
                    "(Clean Verison)", "(Clean)", "(Dirty Version)", "[Official Audio]"]
        for i in unwanted:
            full_title = full_title.replace(i, "")
        try:
            full_title = full_title[:full_title.index("ft.")].strip()
        except ValueError:
            pass
        try:
            artist, title = full_title.split("-", 1)
            return (artist.strip(), title.strip())
        except:
            return (uploader.strip(), full_title.strip()) 
        
    async def search_track(self, query):
        if "https://www.youtube.com/" in query:
            self.youtube_url = query
        else:
            youtube_search_url = "https://www.youtube.com/results?search_query={}".format("+".join(query.strip().split()))
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(youtube_search_url)
                await page.wait_for_load_state()
                await page.click('id=video-title')
                self.youtube_url = page.url
                await page.close()
        await self.get_stats()
    
    async def get_stats(self):
         async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(self.youtube_url)
            await page.wait_for_load_state()
            
            # View
            self.views = await page.inner_text('id=count >> css=[class="view-count style-scope ytd-video-view-count-renderer"]')
            # Likes
            self.likes = await page.inner_text('css=[class="yt-simple-endpoint style-scope ytd-toggle-button-renderer"] >> id=text')
            
            title = await page.inner_text('css=[class="title style-scope ytd-video-primary-info-renderer"]')
            uploader = await page.inner_text('css=[class="style-scope ytd-channel-name"]')
            self.uploader = uploader
            
            self.artist, self.title = self.clean_data(uploader, title)
            
            upload_date = await page.inner_text('id=info-strings')
            self.upload_date = upload_date.removeprefix("•").replace("Premiered", "").strip()
           
            await page.close()
    
    def get_lyrics(self):
        if self.lyrics == "":
            genius =  lg.Genius(access_token=os.getenv("GENIUS_TOKEN"),skip_non_songs=True, excluded_terms=["(Remix)", "(Live)"], remove_section_headers=True)
            try:
                lyrics = genius.search_song(title=self.title, artist=self.artist).lyrics.replace("217EmbedShare URLCopyEmbedCopy", "")
                self.lyrics = self.lyric_message(lyrics)
            except:
                raise Exception()
        else:
            pass
    
    def lyric_message(self,lyrics):
        temp = lyrics.split("\n")
        total_chars = 0
        messages = []
        message = ""
        for i in temp:
            total_chars += len(i) 
            if total_chars > 1995:
                messages.append(message)
                message = ""
                total_chars = 0
            else:
                message += i + "\n"
                total_chars += 1
        messages.append(message.replace("EmbedShare", "").replace("URLCopyEmbedCopy", ""))
        return messages
                
            
class MusicBot(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.q = deque()
        self.is_connected = False
        self.current_track = None

    @commands.command(aliases=['p'])
    async def play(self, ctx, *query):
        query = " ".join(query)
        if ctx.author.voice:
            if not self.is_connected:
                await ctx.author.voice.channel.connect()
                self.is_connected = True
            if "https://youtube.com" in query:
                await ctx.send("🔎 Seaching for {} on YouTube".format(query))
            else:
                await ctx.send("🔎 Fetching the song")
            track = Track()
            await track.search_track(query)
            
            with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(track.youtube_url, download=False)
                url2 = info["formats"][0]["url"]
                track.source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
            
            self.q.append(track)
            if ctx.voice_client.is_playing():
                await ctx.send("✔ Added the {}  to the queue!".format(track.title))
            else:
                self.current_track = self.q.popleft()
                ctx.voice_client.play(self.current_track.source, after=lambda e: self.play_next(ctx))
                await ctx.send("Now playing {} by {}\n {}".format(self.current_track.title, self.current_track.artist, self.current_track.youtube_url))
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
                print(number, track.artist)
                await ctx.send(">>> **{})** {} - {}".format(number+1, track.artist, track.title))

    @commands.command()
    async def remove(self, ctx, number):
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
            try:
                self.current_track.get_lyrics()
            except:
                await ctx.send("Could not find lyrics to {} !".format(self.current_track.title))
            else:
                for i in self.current_track.lyrics:
                    await ctx.send(">>> {}".format(i))
        else:
            await ctx.send("There is no song playing!")
           
    @commands.command()
    async def stats(self, ctx):
        if self.current_track:
            await ctx.send("__**Song stats**__")
            await ctx.send(">>> 📝 **Title** - {}\n⬆ **Uploader** - {}\n📅 **Date** - {}\n👀 **Views** - {}\n👍 **Likes** - {}".format(self.current_track.title, self.current_track.uploader,self.current_track.upload_date, self.current_track.views.split()[0], self.current_track.likes.split()[0]))
        else:
            await ctx.send("No song is playing!")
    
    
    # ------------------------------- Fun Commands ------------------------------- #
    @commands.command()
    async def ayo(self, ctx):
        ayos = ["https://tenor.com/view/ayo-ay-yo-gif-24007574", "https://tenor.com/view/angryfan-pause-hold-up-wait-gif-13284505", "https://tenor.com/view/sidetalk-ayo-ayoo-ayooo-glizzy-gif-23903684"]
        await ctx.send(random.choice(ayos))
        
        
if __name__ == "__main__":
    bot = commands.Bot(command_prefix="!")
    bot.add_cog(MusicBot(bot))
    bot.run(os.getenv("TOKEN"))
    
      
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
        self.artist = artist
        self.title = title
        self.uploader = ""
        self.views = ""
        self.likes = ""
        self.youtube_url = ""
        self.lyrics = ""
        self.priority = 0
        self.upload_date = ""
        
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
                await page.click('css=[class="style-scope ytd-video-renderer"]')
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
            
            self.uploader = await page.inner_text('css=[class="style-scope ytd-channel-name"]')
            upload_date = await page.inner_text('id=info-strings')
            self.upload_date = upload_date.removeprefix("•").replace("Premiered", "").strip()
            try:
                title = title.split("-")
                print(title[1])
                self.title = title[1].removesuffix("(Official Video)").removesuffix("(Official Music Video)").removesuffix("(Official Audio)").strip()
                self.artist = title[0].strip()
            except IndexError:
                self.title = title.strip().replace("'","").replace("[","").replace("]","").replace("(Official Video)", "")
                self.artist = self.uploader.strip()
           
            await page.close()
    
    def get_lyrics(self):
        genius =  lg.Genius(access_token=os.getenv("GENIUS_TOKEN"),skip_non_songs=True, excluded_terms=["(Remix)", "(Live)"], remove_section_headers=True)
        lyrics = genius.search_song(title=self.title, artist=self.artist).lyrics.replace("217EmbedShare URLCopyEmbedCopy", "")
        self.lyrics = self.lyric_message(lyrics)
    
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
        self.track = Track()

    @commands.command()
    async def play(self, ctx, *query):
        query = " ".join(query)
        if ctx.author.voice:
            if not self.is_connected:
                await ctx.author.voice.channel.connect()
                self.is_connected = True
            await ctx.send("🔎 Seaching for {} on YouTube".format(query))
            await self.track.search_track(query)
            with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(self.track.youtube_url, download=False)
                url2 = info["formats"][0]["url"]
                source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
                await ctx.send("Now playing {} by {}\n {}".format(self.track.title, self.track.artist, self.track.youtube_url))
                ctx.voice_client.play(source)
        else:
            await ctx.send("You need to be in a voice channel to use this command!")
    
    @commands.command()
    async def disconnect(self, ctx):
        await ctx.voice_client.disconnect()
        await ctx.send("https://tenor.com/view/ight-imma-head-out-spongebob-imma-head-out-ima-head-out-gif-14902967")
        
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
        self.track.get_lyrics()
        await ctx.send("Display lyrics for the song {}".format(self.track.title))
        for i in self.track.lyrics:
            await ctx.send(">>> {}".format(i))
   
    @commands.command()
    async def stats(self, ctx):
        await ctx.send("__**Song stats**__")
        await ctx.send(">>> 📝 **Title** - {}\n⬆ **Uploader** - {}\n📅 **Date** - {}\n👀 **Views** - {}\n👍 **Likes** - {}".format(self.track.title, self.track.uploader,self.track.upload_date, self.track.views.split()[0], self.track.likes.split()[0]))
        
    @commands.command()
    async def ayo(self, ctx):
        ayos = ["https://tenor.com/view/ayo-ay-yo-gif-24007574", "https://tenor.com/view/angryfan-pause-hold-up-wait-gif-13284505", "https://tenor.com/view/sidetalk-ayo-ayoo-ayooo-glizzy-gif-23903684"]
        await ctx.send(random.choice(ayos))
        
        

if __name__ == "__main__":
    bot = commands.Bot(command_prefix="!")
    bot.add_cog(MusicBot(bot))
    bot.run(os.getenv("TOKEN"))
    
      
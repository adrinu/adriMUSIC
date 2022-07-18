from googleapiclient.discovery import build
from dotenv import load_dotenv
from os import getenv, path
import sys
import lyricsgenius
import pathlib

load_dotenv()

# Video download options
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
    }

YDL_OPTIONS = {
    "format": "bestaudio"
    }

# YouTube API
YOUTUBE = build('youtube', 'v3', developerKey=getenv("API_KEY"))

# GENIUS API
GENIUS = lyricsgenius.Genius(access_token=getenv("GENIUS_TOKEN"),skip_non_songs=True, excluded_terms=["(Remix)", "(Live)"], remove_section_headers=True)

# PATH
#sys.path.append(path.join(pathlib.Path("classes").resolve()))
sys.path.insert(0, path.join(pathlib.Path("classes").resolve()))
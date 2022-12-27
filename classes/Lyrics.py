from settings import GENIUS as genius

class Lyrics:
    def __init__(self, artist, song_name) -> None:
        try:
            self.lyrics = genius.search_song(title=song_name, artist=artist).lyrics
        except:
            try:
                self.lyrics = genius.search_song(title=song_name).lyrics
            except:
                self.lyrics = "Could not get the lyrics for {} by {}".format(song_name, artist)      
    
    def lyric_messages(self):
        temp = self.lyrics.split("\n")
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
        messages.append(message)
        return messages
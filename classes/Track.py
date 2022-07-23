
from settings import YOUTUBE as yt
from Stats import Stat
from Lyrics import Lyrics

class Track:
    def __init__(self, query = "") -> None:
        req = yt.search().list(
            part="snippet",
            q = query
        )
        response = req.execute()
        
        self.id = response["items"][0]["id"]["videoId"]
        self.channel = response["items"][0]["snippet"]["channelTitle"]
        self.publishDate = response["items"][0]["snippet"]["publishTime"].split("T")[0]
        self.youtubeURL = "https://www.youtube.com/watch?v={}".format(self.id)
        
        self.stats = Stat(self.id)
        self.artist, self.title, self.features = self.cleanUpTitle(response["items"][0]["snippet"]["title"])
        self.source = None
    
    @staticmethod
    def cleanUpTitle(title):
        unwanted = ("ft.", "FT.", "feat.", "FEAT.", "Feat.")
        try:
            features = []

            a, t = title.split("-")

            # Gets the main artist and featuring MCs before song name
            artists = a.split(",")
            artist = artists[0]
            if len(artists) > 1:
                features.extend([featured.strip() for featured in artists[1:]])
                
            # Some songs use ' x ' for features
            if " x " in a:
                artists = a.split(" x ")
                artist = artists[0]
                features.extend([featured.strip() for featured in artists[1:]])
            
            # Removes anything in [] & ()
            found = False
            temp = list(t)
            for i in range(len(temp)):
                if temp[i] in ("[", "("):
                    found = True
                    
                if found:
                    # sometimes features are in () []
                    try:
                        end = temp.index(")", i) if temp[i] == "(" else temp.index("]", i)
                        substring = "".join(temp[i+1:end])
                        
                        for ft in unwanted :
                            if ft in substring:
                                substring = substring.replace(ft, "")
                                features.extend([f.strip() for f in substring.split(",")])
                    except:
                        pass
                    
                    if temp[i] in ("]", ")"):
                        found = False
                    temp[i] = ""
            
            temp = "".join(temp)
        
            # Gets featuring MCs in feats.
            for ft in unwanted:
                found = temp.find(ft)
                if found > 0:
                    feats = temp[found:].split(ft)
                    for featured in feats[1].split(","):
                        features.append(featured.strip())
                    temp = temp.replace(ft, "").replace(featured, "")
                    
                if ft in artist:
                    tempp = artist.split(ft)
                    artist = tempp[0]
                    features.extend([f.strip() for f in tempp[1:]])
                    
            return (artist.strip(), "".join(temp).strip(), features)
        except:
            return ("", title.strip(), [])
            
            
        
        
        
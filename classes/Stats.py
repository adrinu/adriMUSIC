from settings import YOUTUBE as yt

class Stat():
    def __init__(self, id) -> None:
        req = yt.videos().list(
            part="statistics", 
            id=id
        )
        response = req.execute()
        
        if response["items"][0]["id"] == id:
            self.views = response["items"][0]["statistics"]["viewCount"]
            self.likes = response["items"][0]["statistics"]["likeCount"]
        else:
            self.views = ""
            self.likes = ""
    

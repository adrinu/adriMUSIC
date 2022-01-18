
# music bot

A music bot for Discord Servers


## Features

- Play songs in your discord server
- Get the lyrics without going on a web explorer



## Commands

| Command | Paramemeter | Description                       |
| :-------- | :------- | :-------------------------------- |
| `!play`   | `youtube_link or query` | Directly plays from youtube link or search up a song|
| `!lyrics` |  | Displays current song lyrics|
| `!pause` |  | Pauses the song|
| `!resume` |  | Resume the song|
| `!stats` |  | Displays stats of youtube video (Likes, Views, etc)|
| `!disconnect` |  | Disconnects bot from the voice channel |


## Roadmap

- Queue system
- Edge cases for commands
- Optimize code, make it run faster
- Parse YouTube Titles better
- Search on other websites like soundcloud.com
- Seperate classes, functions, etc into files

## Run Locally

Clone the project

```bash
  git clone https://github.com/adrinu/adriMUSIC.git
```

Go to the project directory

```bash
  cd my-project
```

Create a .env file, add Discord Bot Token and Genius Token.
```
TOKEN=discord_token
GENIUS_TOKEN=genius token
```

Run main.py (python3.10)

```bash
  python main.py
```


Make sure you invite the bot to your server! With that being said, go to your discord server and try it out!



## Contributing

Contributions are always welcome! Make a pull request! 

# Sbotify

This project is a python bot that scrapes reddit comments for song and artist names and then adds that song to a playlist dedicated to that thread. The intention with this project was to cater to threads with large collections of songs, for example: "What are your best workout songs?" could be found on /r/fitness, "Post your favorite Count Basie song" could be found on /r/jazz, etc. 

## Usage 
You can summon Sbotify by using the following format at the end of your comment: **!Sbotify song: {song name} artist: {artist name}**

After adding the song, Sbotify will reply to the summoning comment with a message telling the user their song was added to the playlist. It will also provide a link to the playlist, a link to a 30sec preview (which can be played without logging into Spotify), and a link to message me in case of an issue. The reply also includes a link for the summoner to delete the bot's comment and remove the song from the playlist (used especially if the bot gets their song wrong).

![img](https://i.imgur.com/7GdvGDr.png)

## Requirements

If you plan on running your own version of Sbotify, make sure you:
* Have a Spotify account
* Have a reddit account
* Configure ```config.py``` with *your own API ids and information*. Make sure to put your own username in your reddit useragent
* Create an empty ```comment_ids.txt``` and ```link_ids.txt``` to keep track of what comments your bot has seen
* Install the libraries mentioned below

## Libraries

* [spotipy](https://github.com/plamere/spotipy) for Spotify API interaction
* [PRAW](https://github.com/praw-dev/praw) for interaction with reddit

## Next Steps
* Improve summon detection with regex
* Get summons from inbox instead of comment search
* Multiple songs in one comment
* ~~Playlist descriptions with subreddit, author, and full title~~
* ~~Better error handling~~
* ~~Allow summoner to delete the reply comment and requested song (if the bot gets the wrong song, etc.)~~

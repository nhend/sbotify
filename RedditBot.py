import Sbotify as sbot
import praw
import config

client_id = config.reddit_id
client_secret = config.reddit_secret
username = config.reddit_username
password = config.reddit_password
user_agent = config.user_agent
hot_word = config.hot_word

#FORMAT: !Sbotify song:94 Dreaming artist:ATO
#IMPLEMENT:
#    Allowing for multiple songs in one comment
#    Allowing hotword in middle of comment
#    Ignoring already added comments
#    Allowing for just a band name (pick 1 popular song)
#    Allowing for just a song name ???

#FIX:
#    Convert print statements to errors or error response (incorrect format etc.)
#    Title generation (set playlist description as full thread title)


reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     password=password,
                     user_agent=user_agent,
                     username=username)

def parse_comment(comment):
    
    comment_body = comment.body
    comment_body = comment_body[comment_body.find('!Sbotify'):] #shorten comment_body to content after the hotword call
    
    track_index = comment_body.find('song:')
    artist_index = comment_body.find('artist:')
    
    #if begins with space, add 1
    
    track_offset = 5 #need characters after 'song:', so exclude 'song:'
    artist_offset = 7 #could've used len()+1 but that'd only be necessary if I changed the format
    
    if track_index == -1 or artist_index == -1:
        print('Incorrect format')
        
    track_index += track_offset
    artist_index += artist_offset
    
    track = comment_body[track_index:artist_index-artist_offset]
    artist = comment_body[artist_index:]
    
    return [track, artist]
    
def gen_title(comment):
    #playlist title format is: [POST ID] POST TITLE
    #ex. [t3_827zrc] Favorite Count Basie songs?
      
    title = '[' + comment.link_id + '] ' + comment.link_title
    #Spotify only allows 50 character titles, so limit
    title = (title[:50]) if len(title) > 50 else title
    
    return title

def gen_desc(comment):
    #description format is: POST TITLE by USER in SUBREDDIT
    
    desc = '\"' + comment.link_title + '\" by ' + comment.link_author + ' in ' + comment.subreddit_name_prefixed
    #Spotify only allows 300 character descriptions, so limit
    desc = (desc[:300]) if len(desc) > 300 else desc
    
    return desc

def add_song(comment):
    #if comment.thread_id in link_ids.txt, add song to playlist of that id
    with open('link_ids.txt', 'a+') as link_ids:
            link_ids.seek(0)
            
            while True:
                if comment.link_id in link_ids.read(): #if we've seen this thread before, just add the song to that id playlist
                    #add song
                    track_titles = parse_comment(comment)
                    track_id = sbot.search_track(track_titles[0], track_titles[1])
                    
                    playlist_id = sbot.get_playlist_id(comment.link_id)
                    
                    sbot.add_track(track_id, playlist_id)
                    break
                
                else: #else, create a playlist and add the song
                    link_ids.write('\n' + comment.link_id)
                    #create playlist                   
                    sbot.create_playlist(gen_title(comment), gen_desc(comment))
                    
                    #add song
                    track_titles = parse_comment(comment)
                    track_id = sbot.search_track(track_titles[0], track_titles[1])
                    
                    playlist_id = sbot.get_playlist_id(comment.link_id)
                    
                    sbot.add_track(track_id, playlist_id)
                    
                    break
    
def search():

    subreddit = reddit.subreddit('Sbotify')
    
    #while True
    
    for comment in subreddit.comments():
        if hot_word in comment.body: 
            #check duplicates against file of replied IDs
            with open('comment_ids.txt', 'a+') as comment_ids:
                comment_ids.seek(0)
                
                while True:
                    if comment.id in comment_ids.read(): #if repeat comment, ignore
                        break
                    else: #else, add song to thread's playlist
                        
                        comment_ids.write('\n' + comment.id)
                        add_song(comment)
                        break
                         
            #parse_comment(comment.body)
            #find_comment(parse_comment(comment.body)) maybe???
            
search()
import Sbotify as sbot
import praw
import config
from spotipy import SpotifyException
import time

client_id = config.reddit_id
client_secret = config.reddit_secret
username = config.reddit_username
password = config.reddit_password
user_agent = config.user_agent
hot_word = config.hot_word
subreddit_list = config.subreddits

#FORMAT: !Sbotify song:94 Dreaming artist:ATO
#IMPLEMENT:
#    Allowing for multiple songs in one comment
#    Allowing hotword in middle of comment
#    Allowing for just a band name (pick 1 popular song)
#    Allowing for just a song name ???

#FIX:
#    Delete comments with bad score (<= -2 ?)
#    Convert errors to error response (incorrect format etc.)

reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     password=password,
                     user_agent=user_agent,
                     username=username)

subreddits = reddit.subreddit('+'.join(subreddit_list))


def parse_comment(comment):
    
    comment_body = comment.body
    comment_body = comment_body[comment_body.find(hot_word):]  # Shorten comment_body to content after the hotword call
    comment_body = comment_body.lower()

    track_index = comment_body.find('song: ')
    artist_index = comment_body.find('artist: ')
    
    #if begins with space, add 1
    
    track_offset = 6   # Need characters after 'song:', so exclude 'song:'
    artist_offset = 8  # Could've used len()+1 but that'd only be necessary if I changed the format
    
    if track_index == -1 or artist_index == -1:
        comment.reply("Hi! Looks like you've used the wrong format, in case you've forgotten it's" + \
                      "\n\n!Sbotify song: {song title} artist: {artist name}" + \
                      "\n\n*** \n\n ^^I'm ^^a ^^bot ^^in ^^development ^^by ^^/u/CarpetStore. [^^Message ^^him](https://www.reddit.com/message/compose/?to=CarpetStore) ^^with ^^comments ^^or ^^complaints.")
        
        print('Posted error reply to ' + comment.id)
        
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
    
    return [track_id, playlist_id]
 
def post_comment(comment, track_ids):
    
    track_names = sbot.get_track_names(track_ids[0])
    
    reply = "I've added your song, ***'" + track_names[0] + "'*** by **" + track_names[1] + "** " \
        + " to this thread's playlist: ['" + sbot.get_playlist_name(comment.link_id) + "'](" + sbot.get_playlist_link(comment.link_id) + ")"   
    
    if sbot.get_track_preview(track_ids[0]) != None:
        reply += "\n\n [Sample of this song](" + sbot.get_track_preview(track_ids[0]) + ")" \
        + "\n\n*** \n\n ^^I'm ^^a ^^bot ^^in ^^development ^^by ^^/u/CarpetStore. [^^Message ^^him](https://www.reddit.com/message/compose/?to=CarpetStore) ^^with ^^comments ^^or ^^complaints."
    else:
        reply += "\n\n This song doesn't have a sample available. [Here's a link to the full song](" + sbot.get_track_link(track_ids[0]) + ")" \
        + "\n\n*** \n\n ^^I'm ^^a ^^bot ^^in ^^development ^^by ^^/u/CarpetStore. [^^Message ^^him](https://www.reddit.com/message/compose/?to=CarpetStore) ^^with ^^comments ^^or ^^complaints."
    
    posted_comment = comment.reply(reply)
    
    delete_link = " ^^Did ^^I ^^get ^^it ^^wrong? [^^Click ^^here ^^to ^^delete ^^this ^^comment ^^and ^^remove ^^your ^^song.](https://www.reddit.com/message/compose/?to=Sbotify&subject=delete&message=" \
    + posted_comment.id + ")"
    
    time.sleep(1)
    posted_comment.edit(posted_comment.body + delete_link)
    
    print('Posted reply to ' + comment.id)
    
def check_delete():
    
    for message in reddit.inbox.messages(limit=25): 
        #using python short circuit evaluation to make sure the message is new, about deletion, about an actual comment, and sent by the author of the relevant comment
        if message.new and message.subject.lower() == 'delete':
            print('Found delete message')
            
            my_comment = reddit.comment(id=message.body)
            
            parent_comment = reddit.comment(id=my_comment.parent_id[3:]) #parent_id includes prefix 't1_', but comment object doesn't take fullname, just id (stuff after prefix)
            
            if parent_comment.id in open('comment_ids.txt').read(): 
                if message.author.name == parent_comment.author:
            
                    track_titles = parse_comment(parent_comment)
                    track_id = sbot.search_track(track_titles[0], track_titles[1])
                    
                    playlist_id = sbot.get_playlist_id(parent_comment.link_id)
                    
                    sbot.remove_track(track_id, playlist_id)
                    
                    my_comment.delete()               
                    message.mark_read()
                    
                    print('Deleted ' + my_comment.id + ' on: ' + parent_comment.id)   
        #else break

def main():
    
    for comment in subreddits.comments():
        if hot_word in comment.body: 
            #check duplicates against file of replied IDs
            with open('comment_ids.txt', 'a+') as comment_ids:
                comment_ids.seek(0)
                
                while True:
                    if comment.id in comment_ids.read(): #if repeat comment, ignore
                        break
                    else: #else, add song to thread's playlist
                        comment_ids.write('\n' + comment.id)
                        sbot.refresh() #refresh spotify API
                        
                        track_ids = add_song(comment)
                        post_comment(comment, track_ids)
                        break
    
    check_delete()
    #refresh()
                
if __name__ == '__main__':
    while True:
        try:
            main()
        
        except SpotifyException:
            sbot.refresh()
            print('Refreshed token')
        
        except KeyboardInterrupt:
            print('Goodbye!')
            break
        
        except Exception as e:
            print('Exception occurred:')
            reddit.redditor('CarpetStore').message('Sbotify Error occurred', e)
            print(e)
        

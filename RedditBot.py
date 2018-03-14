import Sbotify as sbot
from spotipy import SpotifyException
import praw
from praw.models import Comment
import config
import time
import re

client_id = config.reddit_id
client_secret = config.reddit_secret
username = config.reddit_username
password = config.reddit_password
user_agent = config.user_agent
hot_word = config.hot_word
subreddit_list = config.subreddits

#FORMAT: !Sbotify song:94 Dreaming artist:ATO
#IMPLEMENT:
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
    
    '''
    if #can't find song or artist#
        comment.reply("Hi! Looks like you've used the wrong format, in case you've forgotten it's" + \
                      "\n\n!Sbotify song: {song title} artist: {artist name}" + \
                      "\n\n*** \n\n ^^I'm ^^a ^^bot ^^in ^^development ^^by ^^/u/CarpetStore. [^^Message ^^him](https://www.reddit.com/message/compose/?to=CarpetStore) ^^with ^^comments ^^or ^^complaints.")
        
        print('Posted error reply to ' + comment.id)
    '''
    titles_list = re.findall(r'\*\*(.*?)\*\*:\*(.*?)\*',comment.body)

    '''
    for pair in titles_list:
        print(pair[0] + ' ' + pair[1])
    '''
    
    #  titles_list looks like [(Sex and Drugs, Abhi the Nomad), (Pusher, Alt-J)]
    return titles_list
    
def gen_title(comment):
    
    #playlist title format is: [POST ID] POST TITLE
    #ex. [t3_827zrc] Favorite Count Basie songs?
      
    title = '[' + get_link_id(comment) + '] ' + comment.link_title
    #Spotify only allows 50 character titles, so limit
    title = (title[:50]) if len(title) > 50 else title
    
    return title

def gen_desc(comment):
    
    #description format is: POST TITLE by USER in SUBREDDIT
    
    desc = '\"' + comment.link_title + '" in ' + comment.subreddit_name_prefixed
    #Spotify only allows 300 character descriptions, so limit
    desc = (desc[:300]) if len(desc) > 300 else desc
    
    return desc

def get_link_id(comment):
    #print(comment)
    
    vars_dict = vars(comment)
    if 'context' in vars_dict:
        location = 'context'
    elif 'permalink' in vars_dict:
        location = 'permalink'
    else:
        print('Err: No context or permalink!')
        print(vars_dict)
        
    title = re.findall(r'/comments/(.*?)/',vars_dict[location])

    return title[0]  # findall() returns an array so just take the first one

def add_song(comment):
    
    track_ids = []
    #if comment.thread_id in link_ids.txt, add song to playlist of that id
    with open('link_ids.txt', 'a+') as link_ids:
            link_ids.seek(0)
            
            while True:
                if get_link_id(comment) in link_ids.read(): #if we've seen this thread before, just add the song to that id playlist
                    #add song
                    name_pairs = parse_comment(comment)

                    for pair in name_pairs:
                        track_id = sbot.search_track(pair[0], pair[1])
                        playlist_id = sbot.get_playlist_id(get_link_id(comment))
                    
                        sbot.add_track(track_id, playlist_id)
                        track_ids.append(track_id)
                    break
                
                else: #else, create a playlist and add the song
                    link_ids.write('\n' + get_link_id(comment))
                    #create playlist                   
                    sbot.create_playlist(gen_title(comment), gen_desc(comment))
                    
                    #add song
                    name_pairs = parse_comment(comment)

                    for pair in name_pairs:
                        track_id = sbot.search_track(pair[0], pair[1])
                        playlist_id = sbot.get_playlist_id(get_link_id(comment))
                    
                        sbot.add_track(track_id, playlist_id)
                        track_ids.append(track_id)                      
                    break
    
    return [track_ids, playlist_id]
 
def post_comment(comment, track_ids):
    
    #track_ids looks like [['2384thk3j4thh938h', 'i732rhwr7befw23r'], '39485y934gfwkdfg29']
    #so, songs are track_ids[0][i] and playlist is track_ids[1][0]
    
    reply = "I've added your songs to this thread's playlist: ['" + sbot.get_playlist_name(get_link_id(comment)) + "'](" + sbot.get_playlist_link(get_link_id(comment)) + ")"   
    
    counter = 0
    
    for track_id in track_ids[0]:    
        if sbot.get_track_preview(track_ids[0][counter]) != None:
            reply += "\n\n [Sample of **" + sbot.get_track_names(track_ids[0][counter])[0] + "** by *" + sbot.get_track_names(track_ids[0][counter])[1] + "*](" + sbot.get_track_preview(track_ids[0][counter]) + ")"
        else:
            reply += "\n\n **" + sbot.get_track_names(track_ids[0][counter])[0] + "** by *" + sbot.get_track_names(track_ids[0][counter])[1] + "* doesn't have a sample available. [Link to the full song](" + sbot.get_track_link(track_ids[0][counter]) + ")"
        
        counter += 1
    
    reply += "\n\n*** \n\n ^^I'm ^^a ^^bot ^^in ^^development ^^by ^^/u/CarpetStore. [^^Message ^^him](https://www.reddit.com/message/compose/?to=CarpetStore) ^^with ^^comments ^^or ^^complaints." 
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
                    playlist_id = sbot.get_playlist_id(get_link_id(parent_comment))
                    
                    for track_title in track_titles:
                        track_id = sbot.search_track(track_title[0], track_title[1])
                        sbot.remove_track(track_id, playlist_id)
                    
                    my_comment.delete()               
                    message.mark_read()
                    
                    print('Deleted ' + my_comment.id + ' on: ' + parent_comment.id)   
        #else break

def main():
    
    for comment in reddit.inbox.unread():
        if isinstance(comment, Comment) and bool(re.search('\*\*(.*?)\*\*:\*(.*?)\*', comment.body)):
            #check duplicates against file of replied IDs
            with open('comment_ids.txt', 'a+') as comment_ids:
                comment_ids.seek(0)
                
                while True:
                    if comment.id in comment_ids.read(): #if repeat comment, ignore
                        break
                    else: #else, add song to thread's playlist
                        comment_ids.write('\n' + comment.id)
                        sbot.refresh() #checks if new API token is needed, refreshes if so
                        
                        comment.mark_read()
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
        

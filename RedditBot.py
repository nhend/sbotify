import Sbotify as sbot
from spotipy import SpotifyException
import praw
from praw.models import Comment, Message
import config
import time
import re

client_id = config.reddit_id
client_secret = config.reddit_secret
username = config.reddit_username
password = config.reddit_password
user_agent = config.user_agent

#FORMAT: /u/Sbotify **94 Dreaming**:*ATO* **Somebody to Love**:*Abhi the Nomad*
#IMPLEMENT:
#    Delete comments with bad score (<= -2 ?)

#FIX:
#    Duplicates
#    Non-songs being 'added'

reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     password=password,
                     user_agent=user_agent,
                     username=username)

def parse_comment(comment):
    
    # Uses regex to separate data found in comment to song-artist pairs
    titles_list = re.findall(r'\*\*(.*?)\*\*(?: ?):(?: ?)\*(.*?)\*',comment.body)
    
    # titles_list looks like [(Sex and Drugs, Abhi the Nomad), (Pusher, Alt-J)]
    return titles_list
    
def gen_title(comment):
    
    # Playlist title format is: [POST ID] POST TITLE
    # ex. [t3_827zrc] Favorite Count Basie songs?
      
    title = '[' + get_link_id(comment) + '] ' + comment.link_title
    # Spotify only allows 50 character titles, so limit to 50 if necessary
    title = (title[:50]) if len(title) > 50 else title
    
    return title

def gen_desc(comment):
    
    # Playlist description format is: "POST TITLE" in r/SUBREDDIT
    
    desc = '\"' + comment.link_title + '" in ' + comment.subreddit_name_prefixed
    # Spotify only allows 300 character descriptions, so limit
    desc = (desc[:300]) if len(desc) > 300 else desc
    
    return desc

def get_link_id(comment):
    '''Gets the id of the thread from a comment
    
    Since we're getting summons from the inbox instead of a subreddit comment stream,
    we can't use parent_id or link_id (if a comment was a child of another comment,
    parent_id would return the id of its parent comment, not the thread id)
    
    Instead, we get the link from either the 'context' (if comment object is a parent
    comment) or the 'permalink' (if comment object is a child comment) vars, and then
    extract the link id from the link using regex

    This function wouldn't be necessary if the Comment object vars were more consistent.
    
    Returns: 
        A string
        
        Example:
        84ar17
    '''
    
    vars_dict = vars(comment)
    if 'context' in vars_dict:
        location = 'context'
    elif 'permalink' in vars_dict:
        location = 'permalink'
    else:
        print('Err: No context or permalink!')
        print(vars_dict)
        
    title = re.findall(r'/comments/(.*?)/',vars_dict[location])

    return title[0]  # findall() returns an array, we just need the first element

def add_song(comment):
    '''Adds a song to an existing or new playlist
    
    Uses a list of link ids (link_ids.txt) to keep track of which threads
    have already had a summon in them. In other words, which threads have
    an existing playlist.
    
    If the thread's id is not found in the list, we record the link id in 
    the list, create a playlist, and add the user's songs. If the id is 
    found, just add the user's songs. 
    
    Returns:
        A list - track_ids
        
        track_ids[0] is a list of the ids of the requested tracks
        track_ids[1] is the playlist id we're adding the tracks to
        
        Example:
        [['0ZAbupc7jAQpG9IxojQ3s3', '6ZljnCVxgY8UKsqs1urMMc'], '4O8Fn7JHyhnpL1jVNrw2GK']
    '''
    track_ids = []
    
    with open('link_ids.txt', 'a+') as link_ids:
            link_ids.seek(0)
            
            while True:
                # If we've seen this thread before, just add the song to this thread's playlist
                if get_link_id(comment) in link_ids.read(): 
                    
                    name_pairs = parse_comment(comment)

                    for pair in name_pairs:
                        # Use Spotify's search function to get id of the requested song
                        track_id = sbot.search_track(pair[0], pair[1])
                        
                        # Make sure the song exists
                        if track_id != None:
                            playlist_id = sbot.get_playlist_id(get_link_id(comment))
                        
                            # Add the song and record 
                            sbot.add_track(track_id, playlist_id)
                            track_ids.append(track_id)
                        
                        # Ignore 'tracks' that don't exist     
                        else:
                            continue
                            
                    break
                
                else: # If we haven't, create a playlist and add the song
                    # Add thread's id to link_ids.txt
                    link_ids.write('\n' + get_link_id(comment))
                    # Create playlist with gen_title() and gen_desc()                
                    sbot.create_playlist(gen_title(comment), gen_desc(comment))
                    
                    name_pairs = parse_comment(comment)

                    for pair in name_pairs:
                        # Use Spotify's search function to get id of the requested song
                        track_id = sbot.search_track(pair[0], pair[1])
                        
                        # Make sure the song exists
                        if track_id != None:
                            playlist_id = sbot.get_playlist_id(get_link_id(comment))
                        
                            # Add the song and record 
                            sbot.add_track(track_id, playlist_id)
                            track_ids.append(track_id)
                        
                        # Ignore 'tracks' that don't exist   
                        else:
                            continue
                            
                    break
    
    return [track_ids, playlist_id]
 
def post_comment(comment, track_ids):
    '''Reply to summoner with their songs and other info
    
    Supplies the summoner with the name of the thread's playlist, a link 
    to the thread's playlist, the name and artist name of each requested 
    song, a sample of each song (or a link, if no sample is available), 
    a link to the bot's FAQ, a link to message me, and a link to delete 
    this comment and remove their songs from the thread's playlist.
    
    In order to supply a delete link, we need the id of the comment we're 
    posting with this call. So we post the comment, get the id of the 
    comment, and immediately edit it to include the deletion link.
    '''
    
    reply = "I've added your songs to this thread's playlist: ['" + sbot.get_playlist_name(get_link_id(comment)) \
        + "'](" + sbot.get_playlist_link(get_link_id(comment)) + ")"   
    
    # Track_ids looks like [['0ZAbupc7jAQpG9IxojQ3s3', '6ZljnCVxgY8UKsqs1urMMc'], 
    #    '4O8Fn7JHyhnpL1jVNrw2GK']
    # So, a song id is track_ids[0][i] and playlist is track_ids[1][0]
    
    for track_id in track_ids[0]:   
        
        # If the song has a preview, add it to the reply 
        if sbot.get_track_preview(track_id) != None:
            reply += "\n\n [Sample of **" + sbot.get_track_names(track_id)[0] + "** by *" \
                 + sbot.get_track_names(track_id)[1] + "*](" \
                 + sbot.get_track_preview(track_id) + ")"
                 
        # If it doesn't, add the link of the full song
        else:
            reply += "\n\n **" + sbot.get_track_names(track_id)[0] + "** by *" \
                + sbot.get_track_names(track_id)[1] \
                + "* doesn't have a sample available. [Link to the full song](" \
                + sbot.get_track_link(track_id) + ")"
    
    reply += "\n\n*** \n\n[^\[FAQ\]](https://www.reddit.com/r/Sbotify/comments/84ic13/sbotify_info/)" \
        + " ^- [^Message ^my ^developer](https://www.reddit.com/message/compose/?to=CarpetStore) ^-" 
    
    # Post comment before the deletion link edit
    posted_comment = comment.reply(reply)
     
    delete_link = " [^Delete ^this ^comment ^and ^remove ^your ^songs]" \
        + "(https://www.reddit.com/message/compose/?to=Sbotify&subject=delete&message=" + posted_comment.id + ")"
    
    # Since the edit requires a second API request immediately after, give the API some time to breathe
    time.sleep(1)
    
    # Edit the comment with deletion link
    posted_comment.edit(posted_comment.body + delete_link)
    
    print('Posted reply to ' + comment.id)
    
def delete_comment(message):
    '''Allows the user to delete a comment by sending a PM
    
    When the user clicks the deletion link to remove Sbotify's reply and
    their requested songs from the thread's playlist, a PM is generated
    containing the comment id of Sbotify's reply. 
    
    Before deleting, we need to make sure that the id actually belongs 
    to one of our comments and that the person sending the PM is the 
    owner of the comment we replied to. 
    '''
    
    my_comment = reddit.comment(id=message.body)
    
    # Parent_id includes prefix 't1_', but comment object doesn't take fullname, just id (stuff after prefix)
    parent_comment = reddit.comment(id=my_comment.parent_id[3:])
    
    # Check that the id is actually a comment we've posted, that the PM sender owns the parent comment
    if parent_comment.id in open('comment_ids.txt').read() and \
        message.author.name == parent_comment.author:
            
            # To remove a song, we need the track id and the playlist id. To get the track id we 
            # need the track names, and to get the playlist id we need the link id. Both of these 
            # can be found with a Comment object.
            track_titles = parse_comment(parent_comment)
            playlist_id = sbot.get_playlist_id(get_link_id(parent_comment))
            
            # Iterate over the user's requested tracks and remove each one from the playlist
            # Uses track_title[0] = song name and track_title[1] = artist name
            for track_title in track_titles:
                track_id = sbot.search_track(track_title[0], track_title[1])
                sbot.remove_track(track_id, playlist_id)
            
            # Delete comment and remove the message from the unread queue
            my_comment.delete()               
            message.mark_read()
        
            print('Deleted ' + my_comment.id + ' on: ' + parent_comment.id)          

def main():
    
    for item in reddit.inbox.unread():
        # Since Messages or Comments can show up in the inbox, we need to filter for each. Also, users
        # can mention the bot without needing a song, so filter those out by looking for our format
        if isinstance(item, Comment) and bool(re.search('\*\*(.*?)\*\*(?: ?):(?: ?)\*(.*?)\*', item.body)):
            comment = item  # Rename for clarity
            
            # Check duplicates against file of ids we've already replied to/seen
            with open('comment_ids.txt', 'a+') as comment_ids:
                comment_ids.seek(0)
                
                while True:
                    if comment.id in comment_ids.read(): # If repeat comment, ignore
                        break
                    else: # Else, record id and add requested songs to thread's playlist
                        comment_ids.write('\n' + comment.id)
                        
                        # refresh() actually checks if the Spotify API token is expired,
                        # we should still only call it when a Spotify action is needed
                        # (i.e. when we find a comment with a song request)
                        sbot.refresh() 
                        
                        comment.mark_read() # Not actually necessary but makes the inbox cleaner
                        track_ids = add_song(comment)
                        post_comment(comment, track_ids)
                        
                        break
        
        # Not all messages will be deletion messages so we need to filter for those            
        if isinstance(item, Message) and item.subject.lower() == 'delete':
            sbot.refresh()
            delete_comment(item)
                
if __name__ == '__main__':
    while True:
        try:
            main()
        
        # Most issues are caught before Spotify is involved, so usually the problem
        # is the API token being expired
        except SpotifyException:
            sbot.refresh()
            print('Refreshed token')
        
        except KeyboardInterrupt:
            print('Goodbye!')
            break
        
        # It's lazy but necessary to keep the bot running 24/7
        except Exception as e:
            print('Exception occurred:')
            print(e)
        

import spotipy
from spotipy import util
import config

#add ability to call band name and add their most popular song
#remove ' and " from query

### SCOPES AND CREDENTIALS ###
username = config.spotify_username
scopes = config.scopes
client_id = config.spotify_client_id
client_secret = config.spotify_client_secret
redirect_uri = config.redirect_uri

token = util.prompt_for_user_token(username,scope=scopes,client_id=client_id,client_secret=client_secret, redirect_uri=redirect_uri)
sp = spotipy.Spotify(auth=token)
sp.trace = False

def check_repeat_title(playlist_title):
    
    playlists = sp.user_playlists(username)

    for item in playlists['items']:
        if(item['name'] == playlist_title):
            return True
        
    return False
        
def create_playlist(playlist_title, playlist_desc):
    
    sp.user_playlist_create(username, playlist_title)

def search_track(track_title, artist_title):
    
    results = sp.search(q=track_title + ' ' + 'artist:' + artist_title,type='track',limit=1)
    
    try: 
        return results['tracks']['items'][0]['id']
    
    except IndexError:
        print('Track not found')

def get_playlist_id(link_id):
    
    playlists = sp.user_playlists(username)
    
    for playlist in playlists['items']:
        if (playlist['owner']['id'] == username) and (link_id.lower() in playlist['name'].lower()):
            return playlist['id']
       
    return None

def add_track(track_id, playlist_id):

    track_ids = [track_id] #for some reason, Spotipy only takes an array for track ids
    sp.user_playlist_add_tracks(username, playlist_id=playlist_id, tracks=track_ids)

#title = 'Test 3'   
# if not repeat_title(title):
#     print('hello')
#     create_playlist(title)
import spotipy
from spotipy import oauth2 
import config

### SCOPES AND CREDENTIALS ###
username = config.spotify_username
scopes = config.scopes
client_id = config.spotify_client_id
client_secret = config.spotify_client_secret
redirect_uri = config.redirect_uri

sp_oauth = oauth2.SpotifyOAuth(client_id=client_id,client_secret=client_secret,redirect_uri=redirect_uri,scope=scopes)
token_info = sp_oauth.get_cached_token() 
if not token_info:
    auth_url = sp_oauth.get_authorize_url(show_dialog=True)
    print(auth_url)
    response = input('Paste the above link into your browser, then paste the redirect url here: ')
    
    code = sp_oauth.parse_response_code(response)
    token_info = sp_oauth.get_access_token(code)
    
    token = token_info['access_token']
    
sp = spotipy.Spotify(auth=token)

def refresh():
    
    global token_info, sp
    
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        token = token_info['access_token']
        sp = spotipy.Spotify(auth=token)
    
def create_playlist(playlist_title, playlist_desc):
    
    sp.user_playlist_create(username, playlist_title, public=True, description=playlist_desc)
    
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

    tracks = [track_id] #for some reason, Spotipy only takes an array for track ids
    sp.user_playlist_add_tracks(username, playlist_id=playlist_id, tracks=tracks)
    
def remove_track(track_id, playlist_id):
    
    tracks = [track_id]
    sp.user_playlist_remove_all_occurrences_of_tracks(username, playlist_id=playlist_id, tracks=tracks)

#BELOW FUNCTIONS ARE FOR POSTING BOT REPLY
    
def get_track_names(track_id):
    
    track_name = sp.track(track_id)['name']
    artist_name = sp.track(track_id)['artists'][0]['name']
    
    return [track_name, artist_name]

def get_track_preview(track_id):
    
    return sp.track(track_id)['preview_url']

def get_track_link(track_id):
    
    return sp.track(track_id)['external_urls']['spotify']

def get_playlist_name(link_id):
    
    playlists = sp.user_playlists(username)
    
    for playlist in playlists['items']:
        if (playlist['owner']['id'] == username) and (link_id.lower() in playlist['name'].lower()):
            return playlist['name']
       
    return None

def get_playlist_link(link_id):
    
    playlists = sp.user_playlists(username)
    
    for playlist in playlists['items']:
        if (playlist['owner']['id'] == username) and (link_id.lower() in playlist['name'].lower()):
            return playlist['external_urls']['spotify']
       
    return None

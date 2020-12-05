# IMPORTS
import os
import re
import sys
import time
import pickle
from datetime import timedelta
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

def load_credentials():
    '''This function returns an OAuth 2.0 credentials object. It will first check to see if there is a token.pickle file to read.
    If there is, it will load the credentials from the file. If needed, this function will refresh the access token.
    Only if the function does not find a token.pickle file will it open the webserver and obtain the tokens. It will save these tokens to a token.pickle file.
    
    Returns:
        OAuth 2.0 Credentials: a credentials object
    '''
    if os.path.exists('token.pickle'):
        # get tokens from pickle
        with open('token.pickle', 'rb') as fp:
            print('Attempting to Load Credentials...')
            credentials = pickle.load(fp)

        # make sure tokens are valid
        if not credentials.valid:
            print('Refreshing Credentials...')
            credentials.refresh(Request())
    else:
        # create webserver and obtain credentials
        print('Fetching New Tokens...')
        flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', scopes=['https://www.googleapis.com/auth/youtubepartner'])
        flow.run_local_server(port=8080, prompt='consent')
        credentials = flow.credentials

        # pickle credentials for future use
        with open('token.pickle', 'wb') as fp:
            print('Storing Credentials for Future Use...')
            pickle.dump(credentials, fp)

    return credentials

        
def playlist_duration(build_obj, pid):
    '''This function calculates the duration of a playlist and returns it in seconds.
    
    Args:
        build_obj (googleapiclient.build object): an OAuth 2.0 authorized object able to get details of unlisted content
        pid (string): the playlist id of which to find the duration
    
    Returns:
        int: the length of the playlist in seconds
    '''
    # get playlist videos
    pl_request = build_obj.playlistItems().list(
        part='contentDetails',
        playlistId=pid,
        maxResults=50                                   # never going to have more than 50
    )
    pl_response = pl_request.execute()

    # create vid id's list
    vids = []
    for item in pl_response['items']:
        vids.append(item['contentDetails']['videoId'])

    # get video details
    vid_request = build_obj.videos().list(
        part='contentDetails',
        id=','.join(vids)
    )
    vid_response = vid_request.execute()

    # get durations
    total_seconds = 0
    hours_pattern = re.compile(r'(\d+)H')
    minutes_pattern = re.compile(r'(\d+)M')
    seconds_pattern = re.compile(r'(\d+)S')
    for item in vid_response['items']:
        # get duration field
        duration = item['contentDetails']['duration']
        # search and parse
        hours = hours_pattern.search(duration)
        minutes = minutes_pattern.search(duration)
        seconds = seconds_pattern.search(duration)
        hours = int(hours.group(1) if hours else 0)
        minutes = int(minutes.group(1) if minutes else 0)
        seconds = int(seconds.group(1) if seconds else 0)
        
        # convert to seconds and add to total
        vid_seconds = timedelta(
            hours=hours,
            minutes=minutes,
            seconds=seconds
        ).total_seconds()
        total_seconds += vid_seconds

    return total_seconds

def main():
    # load credentials
    credentials = load_credentials()
    # get list of playlists
    youtube = build('youtube', 'v3', credentials=credentials)
    get_all_request = youtube.playlists().list(part='snippet', mine=True)
    get_all_result = get_all_request.execute()
    # find the aaa playlist
    for item in get_all_result['items']:
        if item['snippet']['localized']['title'] == 'asdf':
            # get duration of playlist and store playlist id
            playlist_id = item.get('id')
            duration = playlist_duration(youtube, playlist_id)
            break
    # add five fudge seconds
    duration /= int(sys.argv[1])
    duration += 5
    # wait
    print(f'Waiting for {duration} Seconds...')
    time.sleep(duration)
    # delete playlist
    delete_request = youtube.playlists().delete(id=playlist_id)
    delete_request.execute()


if __name__ == '__main__':
    main()
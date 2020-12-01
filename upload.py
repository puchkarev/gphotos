# Utility for uploading a file to google photos.
# Author: Victor Puchkarev (ittechnician@gmail.com)
# Copyright: 2020
# License: I'm NOT allowing you to use this code for any purpose personal
# or commercial.
#
# Usage:
#   > ./upload.py [path to image or video file] [optional album title]
# Example:
#   > ./upload.py /home/pi/Videos/myvideo.mp4 MyAlbum
#
# Installation:
#
# Dependencies:
# 1) python3 (sudo apt-get install python3)
# 2) google-api-python-client (sudo pip3 install google-api-python-client)
# 3) google-auth-oauthlib (sudo pip3 install google-auth-oauthlib)
# 4) Place this script in a folder (that folder will contain a few additional
#    files.
#
# The folder where the script resides must contain client_secret.json of type
# OAuth 2.0 Client IDs of type Desktop. These credentials identify the
# application itself and are not really secret, they don't give any
# permissions to the application itself, they just identify the project to
# google and allow user authentication.
# To configure this properly do the following:
# 1) Go to https://console.developers.google.com/
# 2) Create a new project there (top left corner under project drop down)
# 3) Create new OAuth 2.0 Client ID by going to:
#    APIs & Services -> Credentials -> Create Credentials -> OAuth client ID
#    Select type Dekstop app, Give it a name, Click Create, then OK, then
#    Click the download button for the client_secret.json and put it in the
#    same folder as this script.
#
# Next is we need to get credentials for the actual user. To do this run
# the script with no arguments. It will open a browser and ask you to login
# and give permissions to this project (the OAuth project we created above).
# It should just ask for permissions to append/write to Google Photos.
# Unless you already authorized the project (unlikely) it will give you
# warnings about safety of the project. The credentials will be stored in
# token.pickle file in the same folder. This script will attempt to reuse
# and refresh credentials as much as possible, but if they expire it will
# open the browser and ask you to login again.
#
# config.pickle contains the information about the albums that were created
# it is necessary since the script does not have read permissions from
# google photos, and is only allowed to add to albums that were created
# using the client_secret.json on the user account associated with
# token.pickle
#
# If you want to use this script for a different user, then delete the
# token.pickle and config.pickle

import os
import sys
import pickle
import json
import requests

import google.oauth2.credentials

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
import google_auth_httplib2

# Obtain Credentials (or retrieve and refresh as necessary).
# Returns credentials.
def obtain_credentials():
  CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'client_secret.json')
  USER_TOKEN_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'token.pickle')
  # Scopes: https://developers.google.com/photos/library/guides/authorization
  SCOPES = ['https://www.googleapis.com/auth/photoslibrary.appendonly']
  creds = None
  if (os.path.exists(USER_TOKEN_FILE)):
    with open(USER_TOKEN_FILE, 'rb') as tokenFile:
      print('Retrieving stored credentials')
      creds = pickle.load(tokenFile)
  if not creds or not creds.valid:
    if (creds and creds.expired and creds.refresh_token):
      print('Refreshing credentials')
      creds.refresh(Request())
    else:
      print('Obtaining credentials')
      flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
      creds = flow.run_local_server(port = 0)
    print('Storing credentials')
    with open(USER_TOKEN_FILE, 'wb') as tokenFile:
      pickle.dump(creds, tokenFile)
  return creds

# Uploads the media file (image or video to google photos using credentials
# If album id is specified the media will be placed in the given album.
# Returns a create response.
def upload_media(file_path, album_id, creds):
  # Step 1: Upload Media
  # https://developers.google.com/photos/library/guides/upload-media
  UPLOAD_URL = 'https://photoslibrary.googleapis.com/v1/uploads'
  upload_response = requests.post(UPLOAD_URL, data = open(file_path, 'rb').read(),
    headers = {
      'Authorization': 'Bearer ' + creds.token,
      'Content-type': 'application/octet-stream',
      'X-Goog-Upload-Protocol': 'raw',
      'X-Goog-Upload-File-Name': os.path.basename(file_path)
    })

  # Step 2: Create Media
  # https://developers.google.com/photos/library/reference/rest/v1/mediaItems/batchCreate
  create_body={
    'newMediaItems': [{
      'simpleMediaItem': {
        'uploadToken': upload_response.content.decode('utf-8')
      }
    }]
  }
  # if we specified an album id, then add it to the request.
  if album_id:
    create_body['albumId'] = album_id

  service = build('photoslibrary', 'v1', credentials = creds)
  create_response = service.mediaItems().batchCreate(body=create_body).execute()
  return create_response

# Create Album in google photos with a given title using credentials specified.
def create_album(album_title, creds):
  # https://developers.google.com/photos/library/reference/rest/v1/albums/create
  service = build('photoslibrary', 'v1', credentials = creds)
  create_response = service.albums().create(
    body={
      'album': {
         'title': album_title
       }
     }).execute()
  return create_response

# Gets the id of the album with a given title, if one does not exist in the config
# then creates one. This script has no google photos read permissions so it has to
# keep this info in the config.
def get_album_id(album_title, creds):
  CONFIG_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.pickle')
  config = None

  if (os.path.exists(CONFIG_FILE)):
    with open(CONFIG_FILE, 'rb') as configFile:
      config = pickle.load(configFile)
  if not config:
    config = {}
  if 'albums' not in config:
    config['albums'] = {}
  if album_title not in config['albums']:
    album_id = create_album(album_title, creds)['id']
    config['albums'][album_title] = album_id

    print('Storing new album id {0}'.format(album_id))
    with open(CONFIG_FILE, 'wb') as configFile:
      pickle.dump(config, configFile)

  return config['albums'][album_title]

# Get the credentials
creds = obtain_credentials()

# Get the file path to upload
if len(sys.argv) < 2:
  sys.exit('Need filename to upload')
file_path = sys.argv[1]

# Get the optional album title
album_title = None
album_id = None
if len(sys.argv) > 2:
  album_title = sys.argv[2]
  print('Uploading to {0}'.format(album_title))
  album_id = get_album_id(album_title, creds)

# Upload the file.
print('Uploading {0}'.format(file_path))
create_response = upload_media(file_path, album_id, creds)
print('Response: {0}'.format(create_response['newMediaItemResults'][0]['status']['message']))

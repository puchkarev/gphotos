# Utility for uploading a file to google photos.
# Author: Victor Puchkarev (ittechnician@gmail.com)
# Copyright: 2020

import os
import sys
import pickle
import json
import requests

import google.oauth2.credentials

from pathlib import Path
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
import google_auth_httplib2

CONFIG_FOLDER=os.path.join(str(Path.home()), '.gphotos')

# Obtain Credentials (or retrieve and refresh as necessary).
# Returns credentials.
def obtain_credentials():
  CLIENT_SECRETS_FILE = os.path.join(CONFIG_FOLDER, 'client_secret.json')
  USER_TOKEN_FILE = os.path.join(CONFIG_FOLDER, 'token.pickle')
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
  CONFIG_FILE = os.path.join(CONFIG_FOLDER, 'config.pickle')
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

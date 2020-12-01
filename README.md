# gphotos
This project deals with interfacing to google photos using the official google photos API v1.

# Installation

## python3

```sudo apt-get install python3```

## google-api-python-client

```sudo pip3 install google-api-python-client```

## google-auth-oauthlib

```sudo pip3 install google-auth-oauthlib```

## gphotos

```git clone https://github.com/puchkarev/gphotos```

## client_secret.json

Get OAuth 2.0 Client ID for your program from google.
These credentials identify the application itself and are not really secret,
they don't give any permissions to the application itself, they just identify
the project to google and allow user authentication.
To configure this properly do the following:
1. Go to https://console.developers.google.com/
2. Create a new project there (top left corner under project drop down)
3. Create new OAuth 2.0 Client ID by going to:
   APIs & Services -> Credentials -> Create Credentials -> OAuth client ID
   Select type Dekstop app, Give it a name, Click Create, then OK, then
   Click the download button for the client_secret.json and put it in the
   config folder ~/.gphotos/

## Get User Credentials

Next is we need to get credentials for the actual user. To do this run
the script with no arguments. It will open a browser and ask you to login
and give permissions to this project (the OAuth project we created above).
It should just ask for permissions to append/write to Google Photos.
Unless you already authorized the project (unlikely) it will give you
warnings about safety of the project. The credentials will be stored in
token.pickle file in the config folder. This script will attempt to reuse
and refresh credentials as much as possible, but if they expire it will
open the browser and ask you to login again.

# Usage

## Uploading media to google photos

```./upload.py [path to image or video file] [optional album title]```

Example:

```./upload.py /home/pi/Videos/myvideo.mp4 MyAlbum```

Note that the with the given scope the only albums google allows to add
media to is the albums created by this script, and in addition this script
does not have read permissions, so it cannot get a list of albums. So it
stores the list of albums it creates and their associated ids in the config
folder.

# License

I'm NOT allowing you to use this code for any purpose personal or commercial.


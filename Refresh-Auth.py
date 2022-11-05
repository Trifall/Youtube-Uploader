#!/usr/bin/python

# You must create a client ID and client secret for your application. You can
# do this at https://console.developers.google.com
# Populate the client_secrets.json file with the respective values.
# If you haven't been audited by Google, you can only upload videos with a private visibility status.

# Example command to run this script:
# python Vod-Uploader.py --file="video_file_name.mp4" --description="description here" --category="22" --privacyStatus="unlisted" --keywords="keyword1,keyword2,keyword3" --title="Title here"

import argparse
import http.client
import httplib2
import os
import random
import sys
import time

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
                        http.client.IncompleteRead, http.client.ImproperConnectionState,
                        http.client.CannotSendRequest, http.client.CannotSendHeader,
                        http.client.ResponseNotReady, http.client.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google API Console at
# https://console.developers.google.com/.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secrets.json"

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_PLAYLIST_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the API Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))


def get_authenticated_service(args, _scope):
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
                                   scope=_scope,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    # if(_scope == YOUTUBE_PLAYLIST_SCOPE):
    storage = Storage("Vod-Uploader.py-oauth2-general.json")
    # else:

    credentials = run_flow(flow, storage, args)

    # try to build, except the exception if the token is invalid or expired
    try:
        return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                     http=credentials.authorize(httplib2.Http()))
    except:
        try:
            print("[Auth] Error: Invalid or expired token, attempting to refresh...")
            # refresh the token
            credentials.refresh(httplib2.Http())
            print("[Auth] Token refreshed.")
            return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                         http=credentials.authorize(httplib2.Http()))
        except:
            credentials = run_flow(flow, storage, args)
            return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                         http=credentials.authorize(httplib2.Http()))


if __name__ == '__main__':

    args = argparser.parse_args()
    args.noauth_local_webserver = True

    youtube_playlist_client = get_authenticated_service(
        args, YOUTUBE_PLAYLIST_SCOPE)

    print("Auth process complete.")

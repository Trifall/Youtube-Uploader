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

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
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

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

UPLOADED_VIDEO_ID = ""


def get_authenticated_service(args, _scope):
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
                                   scope=_scope,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    # if(_scope == YOUTUBE_PLAYLIST_SCOPE):
    storage = Storage("%s-oauth2-general.json" % sys.argv[0])
    # else:
    #     storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
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

# Replace the dashes before the first space in the string with forward slashes


def replaceDashesBeforeFirstSpace(string):
    index = string.find(" ")
    if(index == -1):
        return string
    return string[:index].replace("-", "/") + string[index:]


def extractFileNameFromPath(path):
    delimiter = "/"
    if(path.find("/") == -1):
        delimiter = "\\"
    if(path.find(delimiter) == -1):
        return path
    return path[path.rfind(delimiter) + 1:][:-4]


def initialize_upload(youtube, options):
    tags = None
    if options.keywords:
        tags = options.keywords.split(",")

    # if options.title is equal to "Test Title", then set the title equal options.file
    if options.title == "Untitled Video":
        options.title = extractFileNameFromPath(options.file)

    options.title = replaceDashesBeforeFirstSpace(options.title)

    body = dict(
        snippet=dict(
            title=options.title,
            description=options.description,
            tags=tags,
            categoryId=options.category
        ),
        status=dict(
            privacyStatus=options.privacyStatus
        )
    )

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=",".join(list(body.keys())),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        #
        # Setting "chunksize" equal to -1 in the code below means that the entire
        # file will be uploaded in a single HTTP request. (If the upload fails,
        # it will still be retried where it left off.) This is usually a best
        # practice, but if you're using Python older than 2.6 or if you're
        # running on App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
    )

    # call `resumable_upload(insert_request)` method to upload the video, catch if there is an error, and sleep for 60 seconds, then try again
    try:
        resumable_upload(insert_request)
        break
    except:
        print("[Upload] Error: Upload failed, retrying in 30 seconds...")
        return False


# This method implements an exponential backoff strategy to resume a
# failed upload.


def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print("Uploading file...")
            status, response = insert_request.next_chunk()
            if response is not None:
                if 'id' in response:
                    print("Video id '%s' was successfully uploaded." %
                          response['id'])
                    global UPLOADED_VIDEO_ID
                    UPLOADED_VIDEO_ID = response['id']
                else:
                    exit("The upload failed with an unexpected response: %s" % response)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                                     e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = "A retriable error occurred: %s" % e

        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                exit("No longer attempting to retry.")

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)


def add_video_to_playlist(youtube, videoID, playlistID):
    add_video_request = youtube.playlistItems().insert(
        part="snippet",
        body={
            'snippet': {
                'playlistId': playlistID,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': videoID
                },
                'position': 0
            }
        }
    ).execute()

    # log the response in the format of "Added video to playlist, ID: %s" % add_video_request['id']
    print("Added video to playlist - Request ID: %s" % add_video_request['id'])


if __name__ == '__main__':
    argparser.add_argument("--file", required=True,
                           help="Video file to upload")
    argparser.add_argument("--title", help="Video title",
                           default="Untitled Video")
    argparser.add_argument("--description", help="Video description",
                           default="")
    argparser.add_argument("--category", default="22",
                           help="Numeric video category. " +
                           "See https://developers.google.com/youtube/v3/docs/videoCategories/list")
    argparser.add_argument("--keywords", help="Video keywords, comma separated",
                           default="")
    argparser.add_argument("--privacyStatus", choices=VALID_PRIVACY_STATUSES,
                           default="private", help="Video privacy status.")
    argparser.add_argument("--playlistID", default="",
                           help="Playlist ID to add video to")
    argparser.add_argument(
        '--skip-upload', action=argparse.BooleanOptionalAction, default=False, help='Skip the upload step and just add the video to a playlist')
    argparser.add_argument("--videoID", default="",
                           help="Used for skipping the upload and adding the video to a playlist manually")
    argparser.add_argument(
        "--testing", action=argparse.BooleanOptionalAction, default=False, help='skips all')

    # implement an index flag to add the video to a specific index in the playlist
    args = argparser.parse_args()
    args.noauth_local_webserver = True

    if args.testing:
        print("Testing mode enabled")
        args.skip_upload = True
        # print the args
        print(args)
        exit("Testing printed args. Exiting...")

    if(args.skip_upload):
        print("Skipping upload...")
    else:
        if not os.path.exists(args.file):
            exit("Please specify a valid file using the --file= parameter.")
        youtube_upload_client = get_authenticated_service(
            args, YOUTUBE_UPLOAD_SCOPE)
        try:
            initialize_upload(youtube_upload_client, args)
        except HttpError as e:
            print("An HTTP error %d occurred:\n%s" %
                  (e.resp.status, e.content))

            error_msg = e._get_reason()

            # if the error message contained "title", then the title has an error, so retry with the title "Untitled Video"
            if "title" in error_msg.lower():
                print(
                    "\nTitle Error Detected: Retrying with new title: \"Untitled Video - manual override\"")
                args.title = "Untitled Video - manual override"
                initialize_upload(youtube_upload_client, args)
            else:
                exit("Exiting...")

    if(args.videoID == "" and UPLOADED_VIDEO_ID == ""):
        print("No video ID found, skipping playlist update...")
    else:
        if(UPLOADED_VIDEO_ID == ""):
            UPLOADED_VIDEO_ID = args.videoID
        if (args.playlistID != ""):
            youtube_playlist_client = get_authenticated_service(
                args, YOUTUBE_PLAYLIST_SCOPE)
            print("Adding video to playlist...")
            try:
                add_video_to_playlist(youtube_playlist_client,
                                      UPLOADED_VIDEO_ID, args.playlistID)
            except HttpError as e:
                print("An HTTP error %d occurred:\n%s" %
                      (e.resp.status, e.content))
    print("YouTube process finished")

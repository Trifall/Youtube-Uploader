# Youtube-Uploader

#### A modified version of Google's upload script.

- You must create a client ID and client secret for your application. You can
  do this at https://console.developers.google.com
- Populate client_secrets_example.json and rename it to client_secrets.json.
- If you haven't been audited by Google, you can only upload videos with a private visibility status.

<hr />

#### Flags

    - --file - required, takes path to video file as a string. Can leave blank if --skip-upload is passed.
    - --title - optional, takes title of video as a string. Defaults to "Test Title"
    - --description - optional, description of video as a string. Defaults to "Test Description"
    - --category - optional, takes category of video as a string. Defaults to "22" (Blogs or whatever)
    - --keywords - optional, takes keywords for video as a string. Defaults to ""
    - --privacyStatus - optional, takes privacy status of video as a string. Defaults to "private", requires audit to use "public" or "unlisted"
    - --playlistID - optional, takes playlist ID to add video to as a string. Skips if no value is passed.
    - --skip-upload - optional, binary flag (no input value), skips the upload step and just adds the video to a playlist.
    - --videoID - optional, takes video ID as a string. Skips the upload step and adds the video to a playlist manually. If using --skip-upload, this is required for the script to work.
    - --testing - optional, binary flag. just prints the args that were passed into the script and exits.

<hr />

### Example command to run this script:

```
python Vod-Uploader.py --file="video_file_name.mp4" --description="description here" --category="22" --privacyStatus="unlisted" --keywords="keyword1,keyword2,keyword3" --title="Title here"
```

### Example command for uploading and adding to a playlist:

```
python Vod-Uploader.py --file="video_file_name.mp4" --description="description here" --category="22" --privacyStatus="unlisted" --keywords="keyword1,keyword2,keyword3" --title="Title here" --playlistID="playlist id here"
```

### Example command for strictly adding to a playlist manually:

```
python Vod-Uploader.py --file="" --playlistID="playlist id here" --skip-upload --videoID="video id here"
```

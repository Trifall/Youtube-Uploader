# Youtube-Uploader

#### A modified version of Google's upload script.

 - You must create a client ID and client secret for your application. You can
 do this at https://console.developers.google.com
 - Populate client_secrets_example.json and rename it to client_secrets.json.
 - If you haven't been audited by Google, you can only upload videos with a private visibility status.

<hr />

 ### Example command to run this script: 

python Vod-Uploader.py --file="video_file_name.mp4" --description="description here" --category="22" --privacyStatus="unlisted" --keywords="keyword1,keyword2,keyword3" --title="Title here"

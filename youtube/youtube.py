import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
from utils import description_to_list
from constants import YOUTUBE_DESCRIPTION
from pathlib import Path

# The scopes required to upload videos
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def upload_video(video_file, title, description, tags, srt_file_path, category_id="1"):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "client_secrets.json"

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, SCOPES
    )
    credentials = flow.run_local_server(port=0)
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials
    )

    with open("youtube_description.txt", "r") as f:
        description = f.read()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": "draft",  # "private",  # options: public, private, unlisted
            "selfDeclaredMadeForKids": False,
        },
    }

    # Call the API's videos.insert method to create and upload the video
    insert_request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(video_file, chunksize=-1, resumable=True),
    )

    print(f"Uploading file: {video_file}...")
    response = None
    while response is None:
        status, response = insert_request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"Upload Complete! Video ID: {video_id}")

    # Now upload the captions using the same 'youtube' client
    srt_file = srt_file_path
    if os.path.exists(srt_file):
        upload_caption(youtube, video_id, srt_file)
    else:
        print("SRT file not found, skipping caption upload.")


def upload_caption(youtube, video_id, srt_file_path):
    """
    Uploads an SRT file as a caption track for the specified video.
    """
    print(f"Uploading captions for video ID: {video_id}...")

    body = {
        "snippet": {
            "videoId": video_id,
            "language": "en",  # The language of the captions
            "name": "English",  # Label in the CC menu
            "isDefault": True,  # Auto-display for viewers
        }
    }

    # 'sync=True' is used if the SRT timestamps perfectly match the video audio
    insert_request = youtube.captions().insert(
        part="snippet",
        body=body,
        media_body=MediaFileUpload(srt_file_path, mimetype="application/octet-stream"),
        sync=True,
    )

    response = insert_request.execute()
    print(f"Captions uploaded! Status: {response['snippet']['status']}")


if __name__ == "__main__":
    path = Path("No Other Choice Review (2026-01-04).md")
    description_parts = description_to_list(path)
    
    title = description_parts[0]
    description = YOUTUBE_DESCRIPTION.format(synopsis=description_parts[1], thoughts=description_parts[2], hashtags=description_parts[3])
    
    print(title)
    print(description)
    
    # upload_video(
    #     video_file="Is This Thing On.mov",
    #     title="Automated Upload Test with sub minute #shorts",
    #     description="This video was uploaded using a Python script.",
    #     tags=["python", "automation", "api"],
    #     srt_file_path="No Other Choice.srt",
    # )

    # with open("youtube_description.txt", "r") as f:
    #     description = f.read()
    #     print(description)

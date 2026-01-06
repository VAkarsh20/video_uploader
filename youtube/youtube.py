import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so top-level packages (like `utils`) are importable
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
from utils.description_to_list import description_to_list
from constants import YOUTUBE_DESCRIPTION
from utils.video_asset_utils import get_video_asset_paths
from logger import Logger
import time

# The scopes required to upload videos
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def create_youtube_client():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "client_secrets.json"

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, SCOPES
    )
    credentials = flow.run_local_server(port=0)
    Logger.info("YouTube client created via OAuth flow.")
    return googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials
    )


def upload_video(video_file, title, description, tags, srt_file_path, category_id="1"):
    Logger.phase("YouTube Upload")
    Logger.info(f"Preparing to upload: {video_file}")
    youtube = create_youtube_client()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
            # # --- LANGUAGE SETTINGS ---
            "defaultLanguage": "en-US",  # Title & Description Language: English (United States)
            "defaultAudioLanguage": "en-US",  # Video Language: English (United States)
        },
        "status": {
            # --- VISIBILITY ---
            "privacyStatus": "private",  # "private",  # options: public, private, unlisted
            # --- MADE FOR KIDS ---
            "selfDeclaredMadeForKids": False,
            "madeForKids": False,
            # --- ALLOW EMBEDDING ---
            "embeddable": True,  # Allow embedding
            # --- LICENSE ---
            "license": "youtube",  # "youtube" (Standard)
            # --- SHOW LIKES ---
            # Corresponds to "Show how many viewers like this video"
            "publicStatsViewable": True,
            # --- ALTERED CONTENT ---
            "containsSyntheticMedia": False,  # No AI/Synthetic Media
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
    Logger.success(f"Upload Complete! Video ID: {video_id}")

    # Now upload the captions using the same 'youtube' client
    srt_file = srt_file_path
    if os.path.exists(srt_file):
        upload_caption(youtube, video_id, srt_file)

        # Give YouTube a moment to register the new entry
        time.sleep(2)

        # New verification step
        verify_caption_status(youtube, video_id)
    else:
        Logger.warning("SRT file not found, skipping caption upload.")


def upload_caption(youtube, video_id, srt_file_path):
    """
    Uploads an SRT file as a caption track for the specified video.
    """
    Logger.info(f"Uploading captions for video ID: {video_id}...")

    body = {
        "snippet": {
            "videoId": video_id,
            "language": "en-US",  # The language of the captions
            "isDefault": True,  # Auto-display for viewers
        }
    }

    insert_request = youtube.captions().insert(
        part="snippet",
        body=body,
        media_body=MediaFileUpload(srt_file_path, mimetype="application/octet-stream"),
        sync=False,  # False to preserve your SRT timings exactly
    )

    response = insert_request.execute()
    Logger.success(f"Captions uploaded! Status: {response['snippet']['status']}")


def verify_caption_status(youtube, video_id):
    """
    Fetches the list of captions for a video and prints their current status.
    """
    try:
        request = youtube.captions().list(part="snippet", videoId=video_id)
        response = request.execute()
        Logger.info(f"Checking caption registry for Video ID: {video_id}...")

        items = response.get("items", [])
        if not items:
            Logger.warning("No caption tracks found in the registry yet.")
            return

        for item in items:
            name = item["snippet"]["name"]
            lang = item["snippet"]["language"]
            status = item["snippet"]["status"]
            track_kind = item["snippet"].get("trackKind", "standard")

            # Using your Logger for consistent styling
            Logger.success(f"Track Found: '{name}' [{lang}]")
            print(f"      └─ Status: {status} | Type: {track_kind}")

    except Exception as e:
        Logger.error(f"Could not verify captions: {e}", exc_info=True)


if __name__ == "__main__":
    # 1. Get the validated asset paths from the user
    # This replaces the hardcoded .mov and .srt strings
    video_file, cover_file, srt_file_path = get_video_asset_paths()

    # If the user chose to quit ('q'), exit the script gracefully
    if not video_file:
        sys.exit(0)

    Logger(log_file_path="automation.log")

    Logger.phase("Youtube Upload")

    print(
        f"\n{Logger.BOLD}{Logger.INFO}[INPUT]{Logger.ENDC} Enter the path to the description file (or 'q' to quit): ",
        end="",
    )
    user_input = input().strip().strip("'").strip('"')
    if user_input.lower() in ["q", "quit"]:
        Logger.info("Exiting workflow.")
        sys.exit(0)

    path = Path(user_input)
    description_parts = description_to_list(path)

    title = description_parts[0]
    description = YOUTUBE_DESCRIPTION.format(
        synopsis=description_parts[1],
        thoughts=description_parts[2],
        hashtags=description_parts[3],
    )

    upload_video(
        video_file=video_file,
        title=title,
        description=description,
        tags=["python", "automation", "api"],
        srt_file_path=srt_file_path,
    )

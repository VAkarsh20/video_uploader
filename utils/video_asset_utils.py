import sys
from pathlib import Path
from logger import Logger

# Assuming your Logger class is in a file named logger_file.py
# from logger_file import Logger


def retrieve_video_asset_paths(folder_path):
    """
    Scans a folder for specific video, image, and transcript extensions and sends their paths
    """
    base_dir = Path(folder_path)

    if not base_dir.is_dir():
        raise ValueError(f"Path is not a directory: {folder_path}")

    video = None
    cover = None
    transcript = None

    # Iterate through files in the directory
    for file in base_dir.iterdir():
        if file.is_file():
            ext = file.suffix.lower()
            if ext == ".mov":
                video = str(file)
            elif ext == ".jpg":
                cover = str(file)
            elif ext == ".srt":
                transcript = str(file)

    # Validate that we found all three required components
    if not all([video, cover, transcript]):
        missing = []
        if not video:
            missing.append(".mov")
        if not cover:
            missing.append(".jpg")
        if not transcript:
            missing.append(".srt")
        raise FileNotFoundError(f"Missing assets: {', '.join(missing)}")

    return video, cover, transcript


def get_video_asset_paths():
    """
    Interactively prompts the user for a directory path and validates video assets.

    This function runs a loop that captures user input, cleans potential formatting
    artifacts (like quotes from drag-and-drop), and calls `retrieve_video_assets`
    to verify the existence of a .mov, .jpg, and .srt file.

    It uses the custom Logger class to provide colored terminal feedback and
    persistent logging to 'automation.log'.
    """
    # 1. Initialize your custom logger
    Logger(log_file_path="automation.log")

    Logger.phase("Video Asset Discovery")

    while True:
        try:
            # Get user input with your class's color formatting
            print(
                f"\n{Logger.BOLD}{Logger.INFO}[INPUT]{Logger.ENDC} Enter video folder path to upload (or 'q' to quit): ",
                end="",
            )
            user_input = input().strip().strip("'").strip('"')

            if user_input.lower() in ["q", "quit"]:
                Logger.info("Exiting workflow.")
                break

            Logger.info(f"Scanning directory: {user_input}")

            # Attempt to retrieve paths
            video, cover, transcript = retrieve_video_asset_paths(user_input)

            # Log successes using your class methods
            Logger.info(f"Video Path: {video}")
            Logger.info(f"Cover Path: {cover}")
            Logger.info(f"Transcript Path: {transcript}")
            Logger.success("All required assets located successfully.")

            return video, cover, transcript

        except ValueError as ve:
            Logger.error(f"Invalid Path: {ve}")
        except FileNotFoundError as fnf:
            Logger.error(fnf)
        except KeyboardInterrupt:
            print()  # Clean newline after ^C
            Logger.warning("Process interrupted by user.")
            break
        except Exception as e:
            Logger.error(f"Unexpected error: {e}", exc_info=True)


if __name__ == "__main__":
    get_video_asset_paths()

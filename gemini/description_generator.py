import os
import re
from datetime import datetime
from typing import Any, List

from logger import Logger
from .gemini_prompts import GEMINI_GENERATE_DESCRIPTION_PROMPT
from .gemini_prompts import GEMINI_PROOFREAD_DESCRIPTION_PROMPT
from .chat import call_gemini


class DescriptionGenerator:
    """Encapsulates prompt construction, sending, filename management, and saving.

    Intended to replace the previous module-level helper functions.
    """

    def __init__(self, client: Any = None, chat: Any = None, examples_dir: str = "shorts_descriptions"):
        """Create a DescriptionGenerator.

        Args:
            client: Optional Gemini/GenAI client instance used for any direct client
                interactions (not required for chat-based flows).
            chat: Optional chat session object. If provided, `send_prompt` will use it.
            examples_dir: Path to a directory containing example caption files used
                for few-shot prompt construction.
        """
        self.client = client
        self.chat = chat
        self.examples_dir = examples_dir

    def get_most_recent_files(self, directory: str, n: int = 3) -> List[str]:
        """Return the most recently modified files in `directory`.

        Args:
            directory: Path to scan for files.
            n: Number of recent files to return (default 3).

        Returns:
            List of absolute file paths (may be shorter than `n` if not enough files).
        """
        # If the directory doesn't exist, warn and return an empty list
        if not os.path.exists(directory):
            Logger.warning(f"Directory '{directory}' does not exist.")
            return []

        # Filter out directories and hidden/system files (like .DS_Store)
        files = [
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f)) and not f.startswith(".")
        ]

        # Sort by modification time (most recent first) and return the top `n`
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return files[:n]

    def generate_prompt(self, topic: str, srt_file_path: str) -> str | None:
        """Build the final Gemini prompt using the transcript and example captions.

        Args:
            topic: The video/topic name used in the prompt.
            srt_file_path: Path to the SRT transcript file to include.

        Returns:
            The rendered prompt string ready to send to Gemini, or None on error.
        """
        Logger.phase("Prompt Generation")

        # 1. Read the video transcript from the provided SRT file
        try:
            Logger.info(f"Reading transcript from: {srt_file_path}")
            with open(srt_file_path, "r") as f:
                transcript = f.read()
        except FileNotFoundError:
            Logger.error(f"Transcript file not found: {srt_file_path}")
            return None

        # 2. Retrieve the 3 most recent captions to use as style references
        Logger.info("Fetching recent caption examples for style matching...")
        caption_files = self.get_most_recent_files("shorts_descriptions")
        captions = []
        titles = []  # New list for titles

        # Regex to match " (YYYY-MM-DD)" at the end of the string
        # \s* matches optional whitespace
        # \(\d{4}-\d{2}-\d{2}\) matches (four digits-two digits-two digits)
        date_pattern = r"\s*\(\d{4}-\d{2}-\d{2}\)$"

        for i, caption_file in enumerate(caption_files):
            try:
                with open(caption_file, "r") as f:
                    captions.append(f.read())
                    # Extract filename without extension
                    base_filename = os.path.basename(caption_file)
                    title = os.path.splitext(base_filename)[0]

                    # Clean the title using the date regex
                    title = re.sub(date_pattern, "", title).strip()
                    titles.append(title)
                    Logger.info(f"Loaded example {i+1}: {title}")
            except Exception as e:
                Logger.warning(f"Could not read {caption_file}: {e}")

        # Ensure we have 3 slots filled (even if empty) to avoid .format() errors
        if len(captions) < 3:
            Logger.warning(f"Only {len(captions)} examples found. Padding remaining slots.")
            captions.extend(["[No example provided]"] * (3 - len(captions)))
            titles.extend(["[No Title Provided]"] * (3 - len(titles)))  # Pad titles as well

        # 3. Inject variables into the master prompt template
        try:
            final_prompt = GEMINI_GENERATE_DESCRIPTION_PROMPT.format(
                topic=topic,
                transcript=transcript,
                caption1=captions[0],
                caption2=captions[1],
                caption3=captions[2],
                title1=titles[0],
                title2=titles[1],
                title3=titles[2],
            )
            Logger.success("Gemini prompt generated successfully.")
            return final_prompt
        except KeyError as e:
            Logger.error(f"Formatting error: Missing key in prompt template: {e}")
            return None

    def generate_description(self, prompt: str, phase: str) -> str | None:
        """Send `prompt` to Gemini using the configured chat session to generate a description.

        Args:
            prompt: Fully rendered prompt text.
            phase: Short label used for logging (e.g., 'Calling Gemini for Ideas').

        Returns:
            The textual response from Gemini or None on error.
        """
        Logger.phase(phase)
        try:
            Logger.info("Sending prompt to Gemini...")
            # Use the chat object so Gemini retains conversation state between calls
            response = call_gemini(prompt, self.chat)
            Logger.success("Received response from Gemini.")
            return response.text
        except Exception as e:
            Logger.error(f"An error occurred with the Gemini API: {e}")
            return None

    def get_filename(self, topic: str) -> str:
        """Generate a safe filename for the topic with today's date.

        Args:
            topic: The user-visible topic/title for the file.

        Returns:
            A filename like 'Topic Name (YYYY-MM-DD).md'. Illegal filename characters
            are stripped.
        """
        # Generates a filename: 'Topic Name (YYYY-MM-DD).md'.
        # Cleans illegal characters while preserving spaces.
        date_str = datetime.now().strftime("%Y-%m-%d")
        # Remove chars that are illegal in Windows/macOS filenames
        safe_topic = re.sub(r'[\\/*?:"<>|]', "", topic).strip()
        return f"{safe_topic} ({date_str}).md"

    def save_output(self, filename: str, description: str) -> None:
        """Append Gemini `description` to `filename`.

        The method uses append mode so multiple phases (ideas, proofreading) can be
        saved to the same file.

        Args:
            filename: Destination markdown filename.
            description: Text to append to the file.
        """
        try:
            # Appends the Gemini output to the Markdown file. Using 'a' (append)
            # to preserve the 'Ideas' and 'Proofreading' phases in one file.
            with open(filename, "a", encoding="utf-8") as md_file:
                md_file.write(f"\n\n---\n\n{description}")
            Logger.success(f"File updated: {filename}")
        except Exception as e:
            Logger.error(f"Could not save file: {e}")

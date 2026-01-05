import os
import argparse
from logger import Logger
from gemini import (
    GEMINI_GENERATE_DESCRIPTION_PROMPT,
    GEMINI_PROOFREAD_DESCRIPTION_PROMPT,
)
import re
from datetime import datetime
from getkey import getkey, keys
from gemini import create_gemini_client, create_gemini_chat, call_gemini, DescriptionGenerator


def main():
    # Setup persistent logging
    log_file = "automation_debug.log"
    Logger(log_file_path=log_file)

    # CLI Argument Parsing
    parser = argparse.ArgumentParser(
        description="Generate a Gemini prompt for video descriptions."
    )
    parser.add_argument("topic", help="The topic of the video.")
    parser.add_argument("srt_file", help="The path to the SRT file for the transcript.")
    args = parser.parse_args()

    topic, srt_file = args.topic, args.srt_file

    # Initialize the AI Session and generator
    client = create_gemini_client()
    chat = create_gemini_chat(client)
    generator = DescriptionGenerator(client=client, chat=chat)

    # Prep data
    prompt = generator.generate_prompt(topic, srt_file)
    filename = generator.get_filename(topic)

    # PHASE 1: Generate initial ideas
    if prompt:
        description = generator.generate_description(prompt, "Calling Gemini for Ideas")
        if description:
            generator.save_output(filename, description)
        else:
            return
    else:
        return

    # INTERACTIVE STEP: Pause for user review before proofreading
    print(
        f"{Logger.WARNING}[INPUT]{Logger.ENDC} Create Description. Hit any key to send to Gemini or ESC to end... "
    )
    key = getkey()
    if key == keys.ESC:
        Logger.info("ESC detected. Ending flow.")
        return

    # PHASE 2: Proofreading
    # Because we use the 'chat' object, Gemini already knows the previous 'description'
    proofread_prompt = GEMINI_PROOFREAD_DESCRIPTION_PROMPT
    if proofread_prompt:
        proofread_description = generator.generate_description(
            proofread_prompt, "Calling Gemini for Proofreading"
        )

        if proofread_description:
            generator.save_output(filename, proofread_description)
        else:
            Logger.error("Failed to get proofread description from Gemini.")


if __name__ == "__main__":
    main()

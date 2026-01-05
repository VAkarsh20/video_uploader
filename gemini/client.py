import yaml
import google.genai as genai
from logger import Logger


def create_gemini_client(api_keys_path="api_keys.yml"):
    """Reads API key from YAML and initializes the Google GenAI client."""
    try:
        with open(api_keys_path, "r", encoding="utf-8") as f:
            yml = yaml.safe_load(f)
    except Exception as e:
        Logger.error(f"Could not read {api_keys_path}: {e}")
        return None

    api_key = yml.get("gemini", {}).get("api_key")
    if not api_key:
        Logger.error("Gemini API Key not found.")
        return None

    return genai.Client(api_key=api_key)
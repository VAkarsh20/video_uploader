from typing import Any


def create_gemini_chat(client: Any, model: str = "gemini-3-flash-preview"):
    """Starts a stateful chat session to maintain context between multiple calls."""
    return client.chats.create(model=model)


def call_gemini(prompt: str, chat: Any):
    """Sends a message through the chat object (maintains history)."""
    return chat.send_message(prompt)

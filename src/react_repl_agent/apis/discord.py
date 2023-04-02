"""
Discord API Wrappers.

More info:
- https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks
"""
from pathlib import Path
from typing import Optional

import discord
from discord import SyncWebhook

from .image import Image


def _get_webhook() -> str:
    DISCORD_WEB_HOOK_FILE = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "secrets"
        / "discord_webhook.key"
    )
    assert (
        DISCORD_WEB_HOOK_FILE.exists()
    ), f"Discord webhook file does not exist! Make sure to provide a valid key file at '{DISCORD_WEB_HOOK_FILE}'!"
    with DISCORD_WEB_HOOK_FILE.open("r") as f:
        webhook_url = f.read().strip()
    return webhook_url


assert _get_webhook()  # Fail at import time if the key is not present.


def send_message_discord(msg: str, image: Optional[Image] = None):
    """
    Send a message to discord. An optional image to send can be provided.

    Args:
            msg (str): Message text to send.
            img (Optional[Image]): Image to send (Optional).
    """
    webhook = SyncWebhook.from_url(_get_webhook())
    if image is None:
        webhook.send(msg)
    else:
        img_format = "jpeg"
        filename = f"test.{img_format}"
        img_file = discord.File(
            image.as_bytes_stream(img_format),
            filename=filename,
        )
        webhook.send(content=msg, file=img_file)
    print("Discord message sent successfully.")

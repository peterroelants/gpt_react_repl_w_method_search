"""
Slack API Wrappers.

Slack App: `slack_simple_agent`:
- https://api.slack.com/apps/A04HN97V4FJ
- OAuth token: https://api.slack.com/apps/A04HN97V4FJ/oauth?

"""
import json
from pathlib import Path

import requests

from react_repl_agent.utils.exceptions import SelfDescriptiveError

from ..method_index.doc_utils import get_method_description, get_signature
from .image import Image


class SlackApiError(SelfDescriptiveError):
    ...


def _get_tokens() -> dict[str, str]:
    """Get the Slack API tokens."""
    SLACK_KEY_FILE = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "secrets"
        / "slack.json.key"
    )
    assert (
        SLACK_KEY_FILE.exists()
    ), f"SLACK API token file does not exist! Make sure to provide a valid key file at '{SLACK_KEY_FILE}'!"
    with SLACK_KEY_FILE.open("r") as f:
        token_dict = json.load(f)
    return token_dict


assert _get_tokens()  # Fail at import time if the key is not present.


def _get_bot_headers() -> dict:
    slack_bearer_token = _get_tokens()["bot-token"]
    headers = {"Authorization": f"Bearer {slack_bearer_token}"}
    return headers


def list_slack_channels() -> dict:
    """
    Lists all channels in a Slack team.

    Returns:
            List of slack channels.
    """
    # Finding a conversation (Channel)
    # https://api.slack.com/methods/conversations.list
    slack_api_url = "https://slack.com/api/conversations.list"
    channels_result = requests.get(slack_api_url, headers=_get_bot_headers())
    if channels_result.status_code != 200:
        raise SlackApiError(
            "Error getting the Slack channels! "
            f"status_code={channels_result.status_code!r} "
            f"content={channels_result.content!s}"
        )
    channels_result_dct = channels_result.json()
    if not channels_result_dct["ok"]:
        raise SlackApiError(
            "Error getting the Slack channels! "
            f"status_code={channels_result.status_code!r} "
            f"json_response={channels_result_dct}"
        )
    return channels_result_dct["channels"]


def get_slack_channel_id(channel_name: str) -> str:
    """
    Return the Slack channel ID with the given name.

    Args:
            channel_name (str): Slack channel name to find ID for.

    Returns:
            ID for of the channel with the given name.
            OR "ID NOT FOUND" if no slack channel with given name can be found.
    """
    channel_name = channel_name.lower().strip().lstrip("#")
    channels = list_slack_channels()
    channel_ids = [
        c["id"] for c in channels if c["name"].lower().strip() == channel_name
    ]
    if len(channel_ids) == 0:
        return "ID NOT FOUND"
    else:
        return channel_ids[0]


def send_slack_message(msg: str, channel_id: str):
    """
    Send a message to the Slack channel with the specified ID.

    Args:
            msg (str): Message text to send.
            channel_id (str): Slack channel ID to send message to.
    """
    # https://api.slack.com/methods/chat.postMessage
    post_msg_data = {"channel": channel_id.strip(), "text": msg}
    post_msg_result = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers=_get_bot_headers(),
        json=post_msg_data,
    )
    if post_msg_result.status_code != 200:
        raise SlackApiError(
            "Error sending slack message! "
            f"status_code={post_msg_result.status_code!r}, "
            f"content={post_msg_result.content!s}\n"
            f"Make sure to call the method correctly.\n"
            f"Documentation of this method `{get_signature(send_slack_message)}: "
            f"{get_method_description(send_slack_message)}."
        )
    post_msg_result_dct = post_msg_result.json()
    if not post_msg_result_dct["ok"]:
        raise SlackApiError(
            "Error sending slack message! "
            f"status_code={post_msg_result.status_code}, "
            f"json_response={post_msg_result_dct}\n"
            f"Make sure to call the method correctly.\n"
            f"Documentation of this method `{get_signature(send_slack_message)}: "
            f"{get_method_description(send_slack_message)}."
        )
    return "Post message successful."


def send_slack_image(img: Image, msg: str, channel: str):
    """
    Send the given image and corresponding message to the Slack channel with the given name or ID.

    Args:
            img (Image): Image to send.
            msg (str): Message text to send along with image.
            channel_id (str): Slack channel name or ID to send image to.
    """
    img_format = "jpeg"
    filename = f"test.{img_format}"
    # Upload file
    # https://api.slack.com/methods/files.upload
    upload_img_data = {
        "channels": [channel],
        "content": img.as_bytes(img_format),
        "filename": filename,
        "initial_comment": msg,
    }
    headers = _get_bot_headers()
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    upload_image_result = requests.post(
        "https://slack.com/api/files.upload",
        headers=headers,
        data=upload_img_data,
    )
    if upload_image_result.status_code != 200:
        raise SlackApiError(
            "Error sending slack image! "
            f"status_code={upload_image_result.status_code!r} "
            f"content={upload_image_result.content!s}\n"
            f"Make sure to call the method correctly.\n"
            f"Documentation of this method `{get_signature(send_slack_image)}: "
            f"{get_method_description(send_slack_image)}."
        )
    upload_image_result_dct = upload_image_result.json()
    if not upload_image_result_dct["ok"]:
        raise SlackApiError(
            "Error sending slack image! "
            f"status_code={upload_image_result.status_code} "
            f"json_response={upload_image_result_dct}\n"
            f"Make sure to call the method correctly.\n"
            f"Documentation of this method `{get_signature(send_slack_image)}: "
            f"{get_method_description(send_slack_image)}."
        )
    return "Sending image successful!"

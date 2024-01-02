import asyncio
import aiohttp
import random
from bs4 import BeautifulSoup
import re
import discord
from config import BOT_QUEUE, CALLBACK_URL, DEBUG_CHANNEL, VIDEO_AGE_LIMIT
from queries.youtube_queries import add_channel, add_video, get_channel_by_id, get_channels, get_video_by_id, remove_channel

from utils.logging_utils import setup_logger, unexpected_error_handler
from google_auth_creds import get_googleapi_credentials
from googleapiclient.discovery import build

from views.youtube.VideoView import VideoView
from datetime import datetime, timedelta, timezone

logger = setup_logger(__name__)


def youtube_parser(content: str) -> str:
    """Parse the content of a YouTube feed and return the link to the video"""
    # id, title, channelId, watchTime, duration
    video = dict()
    try:
        soup = BeautifulSoup(content, 'xml')
        if not soup.entry:
            logger.critical(f"Received invalid response: {content}")
            return None
        entry = soup.entry
        video = {
            "_id": entry.videoId.text,
            "channelId": entry.channelId.text,
            "title": entry.title.text,
        }

        with build("youtube", "v3", credentials=get_googleapi_credentials()) as youtube:
            request = youtube.videos().list(
                part=["contentDetails", "snippet"],
                id=video["_id"],
            )
            response = request.execute()
            if not response["items"]:
                logger.critical(f"Received invalid response: {response}")
                return None
            video["duration"] = response["items"][0]["contentDetails"]["duration"]

        published_time = datetime.fromisoformat(
            response["items"][0]["snippet"]["publishedAt"])
        published_timedelta = datetime.now(
            timezone.utc) - published_time
        if published_timedelta > timedelta(days=VIDEO_AGE_LIMIT):
            logger.info(f"Video is too old: {video}")
            return None

        if video["channelId"] == DEBUG_CHANNEL:
            return video

        existing_video = get_video_by_id(video["_id"])
        if existing_video:
            logger.info(f"Video already exists: {video}")
            return None

        channel = get_channel_by_id(video["channelId"])
        if "keywords" in channel and channel["keywords"]:
            if "$SHORT" in channel["keywords"]:
                if check_short(video["duration"]):
                    return video

                logger.info(f"Video is too long: {video}")
                return None
            if not check_keywords(video["title"], channel["keywords"]):
                logger.info(f"Video does not match keywords: {video}")
                return None

        return video
    except Exception as e:
        unexpected_error_handler(logger, e, content=content, response=response)
        return None

def check_short(duration_str: str) -> bool:
    if "H" in duration_str or "D" in duration_str:
        return False

    if "M" in duration_str:
        minutes = int(re.search(r"(\d+)M", duration_str).group(1))
        if minutes > 2:
            return False
    
    return True


def check_keywords(title: str, keywords: list[str]) -> bool:
    return any(keyword in title for keyword in keywords)


def hook_handler(data):
    try:
        video = youtube_parser(data)
        if not video:
            return
        msg = {
            'type': 'youtube',
            'data': video,
        }
        BOT_QUEUE.put(msg)
        logger.info(f"Added {msg} to queue")
    except Exception as e:
        unexpected_error_handler(logger, e, data=str(data))


async def queue_handler(channel: discord.TextChannel, video: dict):
    try:
        if add_video(video):

            duration: str = video["duration"].replace("PT", "")
            if "S" not in duration:
                duration += "00"
            if "M" not in duration and "H" not in duration:
                duration = duration.replace("S", "s")
            duration = duration.replace("H", ":").replace(
                "M", ":").replace("S", "")
            await channel.send(
                content=f"New video ({duration}): {videoId_to_url(video['_id'])}",
                view=VideoView(
                    video["_id"], no_db_log=video["channelId"] == DEBUG_CHANNEL)
            )
            logger.info(
                f"Sent video \"{video['title']}\" to channel {channel}")
    except Exception as e:
        unexpected_error_handler(logger, e, video=video, channel=channel.name)


async def random_videoId_from_playlistId(playlistId: str) -> str:
    try:
        # Get the number of items in the playlist
        with build("youtube", "v3", credentials=get_googleapi_credentials()) as youtube:
            request = youtube.playlists().list(
                part="contentDetails",
                id=playlistId,
                maxResults=1
            )

            response = request.execute()
            item_count = response["items"][0]["contentDetails"]["itemCount"]

        random_index: int = random.randint(0, item_count - 1)
        page_token: str = ''
        for _ in range((random_index // 50) + 1):
            response = await request_videos_by_playlistId(playlistId, page_token=page_token)
            if "nextPageToken" not in response:
                break
            page_token = response["nextPageToken"]
        videoId = response["items"][random_index %
                                    50]["contentDetails"]["videoId"]
        return videoId
    except Exception as e:
        unexpected_error_handler(
            logger, e, playlistId=playlistId, response=response, random_index=random_index)
        return None


async def request_videos_by_playlistId(playlistId: str, part: str = "contentDetails", max_results: int = 50, page_token: str = '') -> dict[str, str]:
    try:
        with build("youtube", "v3", credentials=get_googleapi_credentials()) as youtube:
            request = youtube.playlistItems().list(
                part=part,
                playlistId=playlistId,
                maxResults=max_results,
                pageToken=page_token
            )

            response = request.execute()
            return response
    except Exception as e:
        unexpected_error_handler(logger, e, playlistId=playlistId)
        return None


async def resubscribe():
    channels = get_channels(limit=0)
    for channel in channels:
        title = channel["title"]
        logger.info(f"Resubbing {title}")

        channel_id = channel["_id"]
        await toggle_subscription(channel_id, "unsubscribe")
        await asyncio.sleep(1)
        await toggle_subscription(channel_id, "subscribe")
        await asyncio.sleep(1)


async def subscribe(channel: dict[str, str]) -> bool:
    existing_channel = get_channel_by_id(channel["_id"])
    if existing_channel:
        raise ValueError("Already subscribed")
    add_channel(channel)
    await toggle_subscription(channel["_id"], "subscribe")
    return True


async def unsubscribe(channel_id: str):
    result = remove_channel(channel_id)
    if result.deleted_count == 1:
        await toggle_subscription(channel_id, "unsubscribe")
    elif result.deleted_count == 0:
        logger.error(result)
        raise ValueError("Not subscribed")
    else:
        raise Exception(f"Unexpected result: {result}")


async def toggle_subscription(channel_id: str, mode: str) -> int:
    topic = f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}"
    verify = "async"
    async with aiohttp.ClientSession() as session:
        async with session.post(
                "https://pubsubhubbub.appspot.com/subscribe",
                data={
                    "hub.callback": f"{CALLBACK_URL}/webhook/youtube",
                    "hub.topic": topic,
                    "hub.verify": verify,
                    "hub.mode": mode,
                }
        ) as resp:
            return resp.status


def channelId_to_url(channel_id: str) -> str:
    return f"https://www.youtube.com/channel/{channel_id}"


def channelUrl_to_id(channel_url: str) -> str:
    return channel_url.split("/")[-1]


def videoId_to_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def videoUrl_to_id(video_url: str) -> str:
    return video_url.split("=")[-1]


def request_video_by_id(video_id: str) -> dict[str, str]:
    video = None
    try:
        with build("youtube", "v3", credentials=get_googleapi_credentials()) as youtube:
            request = youtube.videos().list(
                part="snippet",
                id=video_id
            )
            response = request.execute()
        video = response["items"][0]
    except KeyError:
        logger.info(f"video_id: {video_id}, response: {response}")
    except Exception as e:
        unexpected_error_handler(logger, e)
    finally:
        return video


def request_channelTitle_by_id(channel_id: str) -> str:
    title = None
    try:
        with build("youtube", "v3", credentials=get_googleapi_credentials()) as youtube:
            request = youtube.channels().list(
                part="snippet",
                id=channel_id
            )
            response = request.execute()
        title = response["items"][0]["snippet"]["title"]
    except KeyError:
        logger.info(response)
    except Exception as e:
        unexpected_error_handler(logger, e)
    finally:
        return title


def request_videos_by_channelId(channel_id: str) -> list[dict[str, str]]:
    videos = []
    try:
        with build("youtube", "v3", credentials=get_googleapi_credentials()) as youtube:
            request = youtube.search().list(
                part="snippet",
                channelId=channel_id,
                maxResults=25,
                order="date",
                type="video"
            )
            response = request.execute()
        videos = response["items"]
    except KeyError as e:
        unexpected_error_handler(logger, e, response=response)
    except Exception as e:
        unexpected_error_handler(logger, e)
    finally:
        return videos

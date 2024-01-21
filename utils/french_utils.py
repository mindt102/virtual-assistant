import random
from googleapiclient.discovery import build

from google_auth_creds import get_googleapi_credentials
from queries.french_queries import add_video, get_random_playlist, get_video_by_id
from utils import youtube_utils
from utils.logging_utils import setup_logger, unexpected_error_handler

logger = setup_logger(__name__)

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
    
async def random_video(playlists: list = None) -> dict[str, str]:
    try:
        video = None
        while not video or ("private" in video and video["private"]):
            if not playlists:
                random_playlist = get_random_playlist()
            else:
                random_playlist = random.choice(playlists)
            video_id = await random_videoId_from_playlistId(playlistId=random_playlist["_id"])
            
            # Check if video is already in the database
            video = get_video_by_id(video_id)
            if video:
                logger.info(f"Video already in database: {video}")
                continue


            response = youtube_utils.request_video_by_id(video_id)
            
            # If video is private
            if not response:
                add_video(
                    {
                        "_id": video_id,
                        "playlist": random_playlist["_id"],
                        "private": True
                    })
                logger.warning(f"Private video: {video_id}")
            else:
                video = {
                    "_id": video_id,
                    "title": response["snippet"]["title"],
                    "duration": response["contentDetails"]["duration"],
                    "playlist": random_playlist["_id"],
                }
                add_video(video)
                logger.info(f"Added video: {video}")
        return video
    except Exception as e:
        unexpected_error_handler(logger, e, video=video, random_playlist=random_playlist["title"], video_id=video_id, response=response)
        return None

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
            if not response["items"]:
                logger.critical(f"Playlist {playlistId} not found. Response: {response}")
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
            logger, e, playlistId=playlistId, response=response)
        return None
    
def playlistId_to_url(playlist_id: str) -> str:
    return f"https://www.youtube.com/playlist?list={playlist_id}"

def request_playlistTitle_by_id(playlist_id: str) -> str:
    title = None
    try:
        with build("youtube", "v3", credentials=get_googleapi_credentials()) as youtube:
            request = youtube.playlists().list(
                part="snippet",
                id=playlist_id
            )
            response = request.execute()
        title = response["items"][0]["snippet"]["title"]
    except KeyError:
        logger.info(response)
    except Exception as e:
        unexpected_error_handler(logger, e)
    finally:
        return title
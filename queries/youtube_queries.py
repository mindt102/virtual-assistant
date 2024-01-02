
from datetime import datetime
import pymongo
from config import DEBUG_CHANNEL
from utils.database_utils import query
from utils.logging_utils import setup_logger, unexpected_error_handler

logger = setup_logger(__name__)


@query(db="youtube", collection="channels")
def add_channel(channel: dict[str, str], collection: pymongo.collection.Collection) -> None:
    try:
        collection.insert_one(channel)
    except Exception as e:
        unexpected_error_handler(logger, e)


@query(db="youtube", collection="channels")
def get_channels_count(collection: pymongo.collection.Collection) -> int:
    try:
        return collection.count_documents({})
    except Exception as e:
        unexpected_error_handler(logger, e)


@query(db="youtube", collection="channels")
def get_channels(collection: pymongo.collection.Collection, start_title: str = "", limit: int = 10, reverse: bool = False) -> list[dict[str, str]]:
    try:
        return list(
            collection.
            find({"title": {"$gt": start_title} if not reverse else {"$lt": start_title}}).
            sort([("title", pymongo.ASCENDING if not reverse else pymongo.DESCENDING)]).
            limit(limit)
        )
    except Exception as e:
        unexpected_error_handler(logger, e)


@query(db="youtube", collection="channels")
def update_channel_by_id(channel_id: str, channel: dict[str, str], collection: pymongo.collection.Collection) -> pymongo.results.UpdateResult:
    try:
        return collection.update_one({"_id": channel_id}, {"$set": channel})
    except Exception as e:
        unexpected_error_handler(logger, e)


@ query(db="youtube", collection="channels")
def remove_channel(channel_id: str, collection: pymongo.collection.Collection) -> pymongo.results.DeleteResult:
    try:
        return collection.delete_one({"_id": channel_id})
    except Exception as e:
        unexpected_error_handler(logger, e)


@ query(db="youtube", collection="channels")
def get_channel_by_id(chanel_id: str, collection: pymongo.collection.Collection) -> dict[str, str]:
    try:
        return collection.find_one({"_id": chanel_id})
    except Exception as e:
        unexpected_error_handler(logger, e)


@ query(db="youtube", collection="videos")
def add_video(video: dict[str, str], collection: pymongo.collection.Collection) -> str:
    try:
        if video["channelId"] == DEBUG_CHANNEL:
            return video["_id"]
        return collection.insert_one(video).inserted_id
    except pymongo.errors.DuplicateKeyError as e:
        logger.info(f"Video already exists: {video}")
    except Exception as e:
        unexpected_error_handler(logger, e, video=video)


@ query(db="youtube", collection="videos")
def get_videos(collection: pymongo.collection.Collection) -> list[dict[str, str]]:
    try:
        return list(collection.find())
    except Exception as e:
        unexpected_error_handler(logger, e)


@ query(db="youtube", collection="videos")
def get_video_by_id(video_id: str, collection: pymongo.collection.Collection) -> dict[str, str]:
    try:
        return collection.find_one({"_id": video_id})
    except Exception as e:
        unexpected_error_handler(logger, e)


@ query(db="youtube", collection="videos")
def update_watched_at(video_id: str, collection: pymongo.collection.Collection):
    try:
        collection.update_one({"_id": video_id}, {
                              "$set": {"watched_at": int(datetime.now().timestamp())}})
    except Exception as e:
        unexpected_error_handler(logger, e)

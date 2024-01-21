import datetime
import pymongo

from utils.database_utils import query
from utils.logging_utils import setup_logger, unexpected_error_handler

logger = setup_logger(__name__)

@query(db="french", collection="playlists")
def add_playlist(playlist: dict[str, str], collection: pymongo.collection.Collection) -> None:
    try:
        collection.insert_one(playlist)
    except Exception as e:
        unexpected_error_handler(logger, e)

@query(db="french", collection="playlists")
def get_playlists_count(collection: pymongo.collection.Collection) -> int:
    try:
        return collection.count_documents({})
    except Exception as e:
        unexpected_error_handler(logger, e)

@query(db="french", collection="playlists")
def get_playlists(collection: pymongo.collection.Collection, start_title: str = "", limit: int = 10, reverse: bool = False) -> list[dict[str, str]]:
    try:
        return list(
            collection.
            find({"title": {"$gt": start_title} if not reverse else {"$lt": start_title}}).
            sort([("title", pymongo.ASCENDING if not reverse else pymongo.DESCENDING)]).
            limit(limit)
        )
    except Exception as e:
        unexpected_error_handler(logger, e)

@query(db="french", collection="playlists")
def get_random_playlist(collection: pymongo.collection.Collection) -> dict[str, str]:
    try:
        return collection.aggregate([{"$sample": {"size": 1}}]).next()
    except Exception as e:
        unexpected_error_handler(logger, e)


@query(db="french", collection="playlists")
def update_playlist_by_id(playlist_id: str, playlist: dict[str, str], collection: pymongo.collection.Collection) -> pymongo.results.UpdateResult:
    try:
        return collection.update_one({"_id": playlist_id}, {"$set": playlist})
    except Exception as e:
        unexpected_error_handler(logger, e)

@ query(db="french", collection="playlists")
def remove_playlist(playlist_id: str, collection: pymongo.collection.Collection) -> pymongo.results.DeleteResult:
    try:
        return collection.delete_one({"_id": playlist_id})
    except Exception as e:
        unexpected_error_handler(logger, e)

@ query(db="french", collection="playlists")
def get_playlist_by_id(playlist_id: str, collection: pymongo.collection.Collection) -> dict[str, str]:
    try:
        return collection.find_one({"_id": playlist_id})
    except Exception as e:
        unexpected_error_handler(logger, e)

@query(db="french", collection="videos")
def get_video_by_id(video_id: str, collection: pymongo.collection.Collection) -> dict[str, str]:
    try:
        return collection.find_one({"_id": video_id})
    except Exception as e:
        unexpected_error_handler(logger, e)

@query(db="french", collection="videos")
def update_watch(video_id: str, collection: pymongo.collection.Collection) -> None:
    try:
        collection.update_one({"_id": video_id}, {"$inc": {"watch": 1}, "$set": {"last_watch": int(datetime.datetime.now().timestamp())}})
    except Exception as e:
        unexpected_error_handler(logger, e)

@query(db="french", collection="videos")
def add_video(video: dict[str, str], collection: pymongo.collection.Collection) -> None:
    try:
        return collection.insert_one(video).inserted_id
    except Exception as e:
        unexpected_error_handler(logger, e)
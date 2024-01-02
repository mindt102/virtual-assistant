import pymongo
from config import MONGODB_PASSWORD, MONGODB_USERNAME, MONGODB_URI


def query(db: str, collection: str):
    def inner(func):
        def wrapper(*args, **kwargs):
            client = pymongo.MongoClient(
                f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_URI}/?retryWrites=true&w=majority")
            kwargs["collection"] = client[db][collection]
            result = func(*args, **kwargs)
            client.close()
            return result
        return wrapper
    return inner

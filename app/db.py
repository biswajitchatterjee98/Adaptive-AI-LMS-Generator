from __future__ import annotations

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.config import mongodb_url


CLIENT = MongoClient(mongodb_url())
DB: Database = CLIENT.get_default_database()


def sessions_collection() -> Collection:
    return DB["sessions"]


def progress_events_collection() -> Collection:
    return DB["progress_events"]


def init_db() -> None:
    sessions_collection().create_index([("session_id", ASCENDING)], unique=True)
    progress_events_collection().create_index([("session_id", ASCENDING), ("id", ASCENDING)], unique=True)

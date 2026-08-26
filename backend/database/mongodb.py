from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from backend.settings import get_settings


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    settings = get_settings()
    if not settings.mongodb_uri or settings.mongodb_uri.startswith("mongodb://localhost"):
        raise RuntimeError("A MongoDB Atlas MONGODB_URI is required")
    return MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)


def get_database() -> Database:
    database_name = get_settings().mongodb_database
    if not database_name:
        raise RuntimeError("MONGODB_DATABASE is required")
    return get_mongo_client()[database_name]


def close_mongo_client() -> None:
    get_mongo_client.cache_clear()
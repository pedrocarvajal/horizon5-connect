from pymongo import MongoClient

from configs.db import (
    MONGODB_DATABASE,
    MONGODB_HOST,
    MONGODB_PASSWORD,
    MONGODB_PORT,
    MONGODB_USERNAME,
)
from services.logging import LoggingService


def clean_database() -> None:
    log = LoggingService()
    log.setup("cleandb")

    log.info("Connecting to MongoDB...")

    uri = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/"
    connection = MongoClient(uri)
    database = connection[MONGODB_DATABASE]

    log.info(f"Connected to MongoDB: {connection}")
    log.info(f"Database: {database}")

    collections = database.list_collection_names()

    log.info(f"Collections found: {len(collections)}")
    log.info("-" * 50)

    for collection_name in collections:
        collection = database[collection_name]
        result = collection.delete_many({})

        log.info(f"{collection_name}: {result.deleted_count} documents deleted")

    log.info("-" * 50)
    log.info("Database cleaned successfully")

    connection.close()


if __name__ == "__main__":
    clean_database()

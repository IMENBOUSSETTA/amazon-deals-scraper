# common/db.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()  # <- IMPORTANT: loads .env from project root

def _normalize(uri: str) -> str:
    # add authSource=admin if missing and not using Atlas
    if "mongodb+srv://" in uri:
        return uri
    if "authSource=" not in uri:
        sep = "&" if "?" in uri else "?"
        uri = f"{uri}{sep}authSource=admin"
    return uri

MONGO_URI = _normalize(os.getenv("MONGO_URI", "mongodb://root:example@localhost:27017"))
DB_NAME   = os.getenv("MONGO_DB", "deals")
COLL_NAME = os.getenv("MONGO_COLLECTION", "products")

_client = MongoClient(MONGO_URI)
def get_collection():
    return _client[DB_NAME][COLL_NAME]

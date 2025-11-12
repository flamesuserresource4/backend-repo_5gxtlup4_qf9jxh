from typing import Any, Dict, List, Optional
import os
from datetime import datetime
from pymongo import MongoClient

DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "appdb")

_client: Optional[MongoClient] = None
_db = None


def get_db():
    global _client, _db
    if _db is not None:
        return _db
    _client = MongoClient(DATABASE_URL)
    _db = _client[DATABASE_NAME]
    return _db


def create_document(collection_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    now = datetime.utcnow().isoformat()
    data_with_meta = {**data, "created_at": now, "updated_at": now}
    result = db[collection_name].insert_one(data_with_meta)
    data_with_meta["_id"] = str(result.inserted_id)
    return data_with_meta


def get_documents(collection_name: str, filter_dict: Optional[Dict[str, Any]] = None, limit: int = 50) -> List[Dict[str, Any]]:
    db = get_db()
    filter_dict = filter_dict or {}
    docs = list(db[collection_name].find(filter_dict).limit(limit))
    for d in docs:
        d["_id"] = str(d["_id"])  # convert ObjectId to string
    return docs

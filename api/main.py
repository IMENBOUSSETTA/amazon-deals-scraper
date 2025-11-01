from fastapi import FastAPI, Query
from pymongo import MongoClient
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="Amazon Deals API")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:example@localhost:27017/?authSource=admin")
DB_NAME   = os.getenv("MONGO_DB", "deals")
COLL_NAME = os.getenv("MONGO_COLLECTION", "products")

client = MongoClient(MONGO_URI)
col = client[DB_NAME][COLL_NAME]

@app.get("/products")
def get_products(
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: float = 0,
    max_price: float = 10000,
    min_rating: float = 0,
    skip: int = 0,
    limit: int = 10,
):
    query = {"price": {"$gte": min_price, "$lte": max_price}, "rating": {"$gte": min_rating}}
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    if brand:
        query["brand"] = {"$regex": brand, "$options": "i"}
    docs = list(col.find(query, {"_id": 0}).skip(skip).limit(limit))
    return {"count": len(docs), "results": docs}

@app.get("/best-deals")
def best_deals(limit: int = 10):
    docs = list(
        col.find({"discount_pct": {"$ne": None}}, {"_id": 0})
        .sort([("discount_pct", -1), ("rating", -1)])
        .limit(limit)
    )
    return {"count": len(docs), "results": docs}

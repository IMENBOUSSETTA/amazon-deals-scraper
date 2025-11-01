import json, os, asyncio
from common.db import get_collection
SAMPLE = os.path.join(os.path.dirname(__file__), "..", "sample_data", "products.sample.json")
async def main():
    col = get_collection()
    with open(SAMPLE, "r", encoding="utf-8") as f:
        docs = json.load(f)
    for d in docs:
        await col.update_one({"title": d["title"], "source": d.get("source","sample")},
                             {"$set": d}, upsert=True)
    count = await col.count_documents({})
    print(f"Collection now has {count} documents.")
if __name__ == "__main__":
    asyncio.run(main())

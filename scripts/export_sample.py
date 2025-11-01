import os, csv, json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI", "mongodb://root:example@localhost:27017"))
db  = client[os.getenv("MONGO_DB", "deals")]
col = db[os.getenv("MONGO_COLLECTION", "products")]

fields = ["category","title","brand","price","original_price","discount_pct",
          "rating","reviews","product_link","image","availability","source"]

def export_json(path="data_sample.json", limit=100):
    docs = list(col.find({}, {"_id":0}).limit(limit))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)
    print(f"Saved JSON: {path} ({len(docs)} rows)")

def export_csv(path="data_sample.csv", limit=100):
    docs = list(col.find({}, {"_id":0}).limit(limit))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for d in docs:
            w.writerow({k: d.get(k) for k in fields})
    print(f"Saved CSV: {path} ({len(docs)} rows)")

if __name__ == "__main__":
    os.makedirs("samples", exist_ok=True)
    export_json("samples/data_sample.json", limit=150)
    export_csv("samples/data_sample.csv", limit=150)

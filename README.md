<<<<<<< HEAD
## Setup
docker compose up -d
python -m venv .venv311
.\.venv311\Scripts\activate
pip install -r requirements.txt

## Run
python -m scraper.scraper.scrape_amazon_pdp "soin visage" --pages 1
uvicorn api.main:app --host 0.0.0.0 --port 8000
streamlit run frontend/app.py
=======
# 🛍 Amazon Deals Scraper & Dashboard

Scrapes Amazon product data (title, brand, price, discount, rating, etc.), stores results in MongoDB, and provides a REST API with FastAPI + a Streamlit dashboard for visualization.

## 🚀 Features
- Playwright-based scraper (multi-page support)
- MongoDB database
- FastAPI REST endpoints (`/products`, `/best-deals`)
- Streamlit dashboard
- Docker Compose setup for MongoDB + API + UI

## 🧱 Stack
Python · Playwright · MongoDB · FastAPI · Streamlit · Docker

## ▶️ Run locally
```bash
docker compose up -d
python -m scraper.scraper.scrape_amazon_pdp "soin visage" --pages 1

>>>>>>> ffaf9496f167347e66a6bc7b702ef7c9dd52f582

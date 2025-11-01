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


# 🛍 Amazon Deals Scraper & Dashboard

Scrapes Amazon product data (title, brand, price, discount, rating, etc.), stores results in MongoDB, and provides a REST API with FastAPI + a Streamlit dashboard for visualization.

##  Features
- Playwright-based scraper (multi-page support)
- MongoDB database
- FastAPI REST endpoints (`/products`, `/best-deals`)
- Streamlit dashboard
- Docker Compose setup for MongoDB + API + UI

##  Stack
Python · Playwright · MongoDB · FastAPI · Streamlit · Docker

---

##  Setup

```bash
# 1️⃣ Start MongoDB (and optional mongo-express)
docker compose up -d

# 2️⃣ Create virtual environment
python -m venv .venv311
.\.venv311\Scripts\activate

# 3️⃣ Install dependencies
pip install -r requirements.txt

## Setup
docker compose up -d
python -m venv .venv311
.\.venv311\Scripts\activate
pip install -r requirements.txt

## Run
python -m scraper.scraper.scrape_amazon_pdp "soin visage" --pages 1
uvicorn api.main:app --host 0.0.0.0 --port 8000
streamlit run frontend/app.py

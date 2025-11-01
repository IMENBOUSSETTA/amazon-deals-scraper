# frontend/app.py
import os
import math
import requests
import streamlit as st
from urllib.parse import urlencode

# ---------- Config ----------
DEFAULT_API = os.getenv("API_URL", "http://127.0.0.1:8000")


st.set_page_config(page_title="Amazon Best Deals Dashboard", layout="wide")
st.title("🛒 Amazon Best Deals Dashboard")

# ---------- Sidebar: API base + Filters ----------
with st.sidebar:
    st.subheader("Backend")
    api_base = st.text_input("API base URL", DEFAULT_API).rstrip("/")
    st.caption("Example: http://127.0.0.1:8000 or http://192.168.1.102:8000")

    st.markdown("---")
    st.subheader("Filters (for /products)")
    category = st.text_input("Category (e.g., ssd 1to, soin visage)")
    brand = st.text_input("Brand (optional)")
    min_price, max_price = st.slider("Price range (€)", 0, 2000, (0, 1000))
    min_rating = st.slider("Minimum rating", 0.0, 5.0, 0.0, 0.1)
    page_size = st.selectbox("Page size", [10, 12, 20, 30, 50], index=1)

tabs = st.tabs(["🔍 Products", "🔥 Best Deals"])

# ---------- Helpers ----------
def fetch_json(path: str, params=None):
    url = f"{api_base}{path}"
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Request failed: {e}\nURL: {url}\nParams: {params}")
        return None

def product_card(p):
    # small product card with image + key info
    with st.container(border=True):
        cols = st.columns([1, 3])
        with cols[0]:
            if p.get("image"):
                st.image(p["image"])
        with cols[1]:
            title = p.get("title") or "Untitled"
            link = p.get("product_link")
            if link:
                st.markdown(f"**[{title}]({link})**")
            else:
                st.markdown(f"**{title}**")

            meta = []
            if p.get("brand"): meta.append(f"**Brand:** {p['brand']}")
            if p.get("category"): meta.append(f"**Category:** {p['category']}")
            if p.get("availability"): meta.append(f"**Availability:** {p['availability']}")
            if meta: st.write(" • ".join(meta))

            price = p.get("price")
            orig  = p.get("original_price")
            disc  = p.get("discount_pct")
            rating= p.get("rating")
            reviews = p.get("reviews")

            line = []
            if price is not None:  line.append(f"**€{price:.2f}**")
            if orig  is not None:  line.append(f"~~€{orig:.2f}~~")
            if disc  is not None:  line.append(f"**-{disc:.0f}%**")
            if rating is not None: line.append(f"⭐ {rating:.1f}")
            if reviews:            line.append(f"({reviews} reviews)")
            if line: st.write(" ".join(line))

# ---------- Tab 1: /products ----------
with tabs[0]:
    left, right = st.columns([1, 1])
    with left:
        query_btn = st.button("🔎 Fetch Products", use_container_width=True)
    with right:
        sort_by = st.selectbox("Sort by", ["price", "discount_pct", "rating"], index=1)
        order = st.radio("Order", ["desc", "asc"], horizontal=True, index=0)

    if query_btn:
        params = {
            "category": category or None,
            "brand": brand or None,
            "min_price": float(min_price),
            "max_price": float(max_price),
            "min_rating": float(min_rating),
            "sort_by": sort_by,
            "order": order,
            "page": 1,
            "page_size": page_size,
        }
        data = fetch_json("/products", params)
        if data:
            total = data.get("total", data.get("count", 0))  # support either shape
            results = data.get("results", [])
            st.success(f"Found {total} products.")
            if not results:
                st.info("No items for these filters.")
            else:
                # pagination controls
                total_pages = max(1, math.ceil(total / page_size))
                page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
                if page != 1:
                    params["page"] = page
                    data = fetch_json("/products", params)
                    results = data.get("results", [])

                # grid display (2 columns)
                grid_cols = st.columns(2)
                for i, item in enumerate(results):
                    with grid_cols[i % 2]:
                        product_card(item)

                # deep link to API call
                qs = urlencode({k: v for k, v in params.items() if v not in (None, "")})
                st.caption(f"API call: `{api_base}/products?{qs}`")

# ---------- Tab 2: /best-deals ----------
with tabs[1]:
    colA, colB = st.columns([1, 1])
    with colA:
        bd_limit = st.slider("How many items?", 5, 50, 20, 1)
    with colB:
        bd_min_reviews = st.number_input("Min reviews (optional)", min_value=0, value=0, step=50)

    if st.button("🔥 Show Best Deals", use_container_width=True):
        params = {"limit": bd_limit}
        if bd_min_reviews > 0:
            params["min_reviews"] = bd_min_reviews
        data = fetch_json("/best-deals", params)
        if data:
            items = data.get("results", [])
            st.success(f"{len(items)} items")
            # grid display (3 columns)
            grid_cols = st.columns(3)
            for i, item in enumerate(items):
                with grid_cols[i % 3]:
                    product_card(item)
            qs = urlencode(params)
            st.caption(f"API call: `{api_base}/best-deals?{qs}`")

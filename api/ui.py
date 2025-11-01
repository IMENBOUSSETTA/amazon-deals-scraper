import streamlit as st
import requests

API = "http://127.0.0.1:8000"  # FastAPI backend

st.set_page_config(page_title="Amazon Deals Dashboard", layout="wide")
st.title("🛒 Amazon Best Deals Dashboard")

st.sidebar.header("🔍 Filters")
cat = st.sidebar.text_input("Category")
brand = st.sidebar.text_input("Brand")
min_price, max_price = st.sidebar.slider("Price range (€)", 0, 2000, (0, 1000))
min_rating = st.sidebar.slider("Minimum rating", 0.0, 5.0, 3.0)

if st.sidebar.button("Fetch Products"):
    params = {
        "category": cat,
        "brand": brand,
        "min_price": min_price,
        "max_price": max_price,
        "min_rating": min_rating,
    }
    try:
        res = requests.get(f"{API}/products", params=params, timeout=10)
        data = res.json()
        if data["count"] == 0:
            st.warning("No products found for your filters.")
        else:
            st.success(f"✅ Found {data['count']} products.")
            st.dataframe(data["results"])
    except Exception as e:
        st.error(f"❌ Error: {e}")

st.markdown("---")
if st.button("🔥 Show Best Deals"):
    try:
        res = requests.get(f"{API}/best-deals", timeout=10)
        data = res.json()
        st.dataframe(data["results"])
    except Exception as e:
        st.error(f"❌ Error: {e}")

import os, asyncio
import time
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus, urljoin
from dotenv import load_dotenv
from pymongo import UpdateOne
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from common.db import get_collection

load_dotenv()

COUNTRY  = os.getenv("SCRAPER_COUNTRY_DOMAIN", "fr")
BASE     = f"https://www.amazon.{COUNTRY}"
BROWSER  = os.getenv("SCRAPER_BROWSER", "firefox").lower()   # "firefox" or "chromium"
HEADLESS = os.getenv("SCRAPER_HEADLESS", "false").lower() in ("1","true","yes")
SLOW_MO  = int(os.getenv("SCRAPER_SLOW_MO", "150"))
MAX_LINKS_PER_PAGE = int(os.getenv("SCRAPER_MAX_LINKS", "24"))

def _price_to_float(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    s = s.strip().replace("\xa0", " ").replace("\u202f", " ")
    digits = "".join(ch for ch in s if (ch.isdigit() or ch in ".,"))
    if not digits:
        return None
    try:
        return float(digits.replace(",", "."))
    except:
        return None

async def _accept_cookies(page):
    selectors = [
        "#sp-cc-accept", "input#sp-cc-accept", "button[name='accept']",
        "text=Accepter les cookies", "text=Accepter",
        "text=J’accepte", "text=J'accepte",
        "text=Allow all cookies", "text=Tout accepter",
        "button:has-text('Accepter')", "button:has-text('Tout accepter')",
    ]
    for sel in selectors:
        try:
            if await page.is_visible(sel, timeout=2000):
                await page.click(sel)
                await page.wait_for_timeout(800)
                return
        except:
            pass

async def _scroll(page, steps=18, dy=1600, pause=350):
    for _ in range(steps):
        await page.mouse.wheel(0, dy)
        await page.wait_for_timeout(pause)

async def _collect_search_links(page, query: str, page_no: int) -> List[str]:
    url = f"{BASE}/s?k={quote_plus(query)}&page={page_no}"
    print("[SEARCH]", url)
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    await _accept_cookies(page)
    try:
        await page.wait_for_selector(
            "div.s-result-item[data-component-type='s-search-result']",
            timeout=60000
        )
    except PWTimeout:
        print("No result cards found (timeout). Dumping HTML...")
        open("last_search.html", "w", encoding="utf-8").write(await page.content())
        return []
    await _scroll(page, steps=18)
    open("last_search.html", "w", encoding="utf-8").write(await page.content())

    links: List[str] = []

    # Preferred: links inside result cards with data-asin
    cards = await page.query_selector_all(
        "div.s-result-item[data-component-type='s-search-result'][data-asin]"
    )
    for c in cards:
        a = await c.query_selector("h2 a.a-link-normal") or await c.query_selector("h2 a")
        if not a:
            continue
        href = await a.get_attribute("href")
        if not href:
            continue
        if href.startswith("/"):
            href = urljoin(BASE, href)
        if "/dp/" in href:
            links.append(href)
        if len(links) >= MAX_LINKS_PER_PAGE:
            break

    # Fallback: any anchor containing '/dp/'
    if len(links) < 5:
        anchors = await page.query_selector_all("a[href*='/dp/']")
        seen = set(links)
        for a in anchors:
            href = await a.get_attribute("href")
            if not href:
                continue
            if href.startswith("/"):
                href = urljoin(BASE, href)
            if "/dp/" not in href or href in seen:
                continue
            links.append(href)
            seen.add(href)
            if len(links) >= MAX_LINKS_PER_PAGE:
                break

    print(f"Collected {len(links)} PDP links on page {page_no}")
    return links

async def _parse_pdp(page) -> Tuple[Optional[float], Optional[float], Optional[float],
                                    Optional[float], Optional[int], Optional[str]]:
    price_selectors = [
        "#corePrice_desktop span.a-price > span.a-offscreen",
        "span.apexPriceToPay > span.a-offscreen",
        "span.a-price.a-text-price.a-size-medium.apexPriceToPay > span.a-offscreen",
        "span.a-price > span.a-offscreen",
        "#price_inside_buybox",
    ]
    price_txt = None
    for sel in price_selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                t = (await el.inner_text()).strip()
                if t:
                    price_txt = t
                    break
        except:
            pass
    price = _price_to_float(price_txt)

    orig_selectors = [
        "#corePrice_desktop span.a-text-price > span.a-offscreen",
        "span.a-price.a-text-price > span.a-offscreen",
        "#priceblock_ourprice",
    ]
    orig_txt = None
    for sel in orig_selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                t = (await el.inner_text()).strip()
                if t and t != price_txt:
                    orig_txt = t
                    break
        except:
            pass
    original = _price_to_float(orig_txt)
    discount = round(100 * (original - price) / original, 2) if (price is not None and original and original > 0) else None

    rating = None
    try:
        el = await page.query_selector("span[data-hook='rating-out-of-text'], span#acrPopover span.a-icon-alt")
        if el:
            txt = (await el.inner_text()).strip()
            if "sur 5" in txt:
                rating = float(txt.split()[0].replace(",", "."))
            elif "out of" in txt:
                rating = float(txt.split(" out of")[0])
    except:
        pass

    reviews = None
    try:
        el = await page.query_selector("#acrCustomerReviewText, #acrCustomerReviewText .a-size-base")
        if el:
            t = (await el.inner_text()).strip().split()[0]
            t = t.replace(" ", "").replace(",", "").replace(".", "")
            if t.isdigit():
                reviews = int(t)
    except:
        pass

    image = None
    for sel in ["#imgTagWrapperId img", "#landingImage", "img#landingImage"]:
        try:
            el = await page.query_selector(sel)
            if el:
                image = await el.get_attribute("src")
                if image:
                    break
        except:
            pass

    return price, original, discount, rating, reviews, image

async def scrape_search_to_pdp(query: str, pages: int = 1) -> List[Dict]:
    out: List[Dict] = []
    async with async_playwright() as p:
        if BROWSER == "chromium":
            browser = await p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
        else:
            browser = await p.firefox.launch(headless=HEADLESS, slow_mo=SLOW_MO)

        ctx = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"),
            viewport={"width": 1440, "height": 900},
            locale="fr-FR" if COUNTRY == "fr" else "en-US",
        )
        page = await ctx.new_page()

        await page.goto(BASE, wait_until="domcontentloaded", timeout=60000)
        await _accept_cookies(page)
        try:
            await ctx.add_cookies([
                {"name": "i18n-prefs", "value": "EUR", "domain": f".amazon.{COUNTRY}", "path": "/"},
                {"name": "lc-main", "value": "fr_FR" if COUNTRY == "fr" else "en_US",
                 "domain": f".amazon.{COUNTRY}", "path": "/"},
            ])
        except:
            pass

        links: List[str] = []
        for pno in range(1, pages + 1):
            more = await _collect_search_links(page, query, pno)
            links.extend(more)
        print(f"Total PDP links collected: {len(links)}")

        for idx, link in enumerate(links, 1):
            try:
                print(f"[PDP {idx}/{len(links)}] {link}")
                await page.goto(link, wait_until="domcontentloaded", timeout=60000)
                await _accept_cookies(page)
                await page.wait_for_timeout(800)

                title = None
                try:
                    te = await page.query_selector("#productTitle")
                    if te:
                        title = (await te.inner_text()).strip()
                except:
                    pass

                price, original, discount, rating, reviews, image = await _parse_pdp(page)

                if title and (price is not None):
                    out.append({
                        "category": query,
                        "title": title,
                        "brand": None,
                        "price": price,
                        "original_price": original,
                        "discount_pct": discount,
                        "rating": rating,
                        "reviews": reviews,
                        "product_link": link,
                        "image": image,
                        "availability": None,
                        "source": f"amazon.{COUNTRY}",
                    })
            except Exception as e:
                print("PDP error:", e)

        await browser.close()
    return out

async def save_many(docs):
    """Upsert docs without blocking the event loop."""
    if not docs:
        return 0
    col = get_collection()
    ops = []
    for d in docs:
        key = {"title": d.get("title"), "source": d.get("source")}
        ops.append(UpdateOne(key, {"$set": d}, upsert=True))

    def _write():
        # synchronous call executed in a worker thread
        return col.bulk_write(ops, ordered=False)

    try:
        res = await asyncio.to_thread(_write)
        return (res.upserted_count or 0) + (res.modified_count or 0)
    except Exception as e:
        # Optional safety net: save to JSON so you don't lose the scrape
        os.makedirs("data/out", exist_ok=True)
        path = f"data/out/scraped_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)
        print(f"⚠️ Mongo unavailable ({e.__class__.__name__}). Saved {len(docs)} docs to {path}")
        return 0

async def main_async(query: str, pages: int):
    docs = await scrape_search_to_pdp(query, pages)
    print(f"Scraped {len(docs)} items. Saving...")
    changed = await save_many(docs)
    print(f"Upserted/updated: {changed} documents.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--pages", type=int, default=1)
    args = parser.parse_args()
    asyncio.run(main_async(args.query, args.pages))

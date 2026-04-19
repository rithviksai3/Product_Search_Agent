"""Tool to search for products across multiple e-commerce websites."""

import json
import re
from duckduckgo_search import DDGS
from config import ECOMMERCE_SITES, MAX_RESULTS_PER_SITE
from tools.zenserp_client import zenserp_search


def _extract_price_from_text(text: str) -> dict:
    """Extract price information from a text snippet."""
    patterns = [
        r'\$\s*([\d,]+\.?\d*)',             # $99.99
        r'USD\s*([\d,]+\.?\d*)',            # USD 99.99
        r'Rs\.?\s*([\d,]+\.?\d*)',          # Rs. 4999
        r'₹\s*([\d,]+\.?\d*)',             # ₹4999
        r'INR\s*([\d,]+\.?\d*)',            # INR 4999
        r'£\s*([\d,]+\.?\d*)',             # £99.99
        r'€\s*([\d,]+\.?\d*)',             # €99.99
    ]
    currency_map = {
        0: "$", 1: "$", 2: "₹", 3: "₹", 4: "₹", 5: "£", 6: "€",
    }
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, text)
        if match:
            price_str = match.group(1).replace(",", "")
            try:
                price_val = float(price_str)
                currency = currency_map.get(i, "$")
                return {
                    "price": f"{currency}{price_val:,.2f}",
                    "extracted_price": price_val,
                    "currency": currency,
                }
            except ValueError:
                continue
    return {"price": "See link", "extracted_price": None, "currency": None}


def search_products_on_ecommerce(
    product_name: str,
    specifications: str = "",
    sites: list[str] | None = None,
) -> str:
    """Search for a product across multiple e-commerce websites."""
    if sites is None:
        sites = ECOMMERCE_SITES

    all_results = {}

    for site in sites:
        query = f"{product_name} site:{site}"
        if specifications:
            query += f" {specifications}"

        site_results = []

        # Zenserp Google Shopping for structured results
        shop_data = zenserp_search(f"{product_name} {specifications}".strip(), tbm="shop")
        if shop_data:
            for item in shop_data.get("shopping_results", [])[:MAX_RESULTS_PER_SITE]:
                price_str = item.get("price", "N/A")
                price_info = _extract_price_from_text(price_str) if price_str != "N/A" else {"extracted_price": None}
                site_results.append({
                    "title": item.get("title", ""),
                    "price": price_str,
                    "extracted_price": price_info.get("extracted_price"),
                    "link": item.get("url", item.get("link", "")),
                    "source": item.get("source", site),
                    "rating": item.get("rating"),
                    "reviews_count": item.get("reviews"),
                })

        # DuckDuckGo fallback for site-specific results
        if len(site_results) < 3:
            try:
                with DDGS() as ddgs:
                    ddg_results = ddgs.text(query, max_results=MAX_RESULTS_PER_SITE)
                    for item in ddg_results:
                        text = f"{item.get('title', '')} {item.get('body', '')}"
                        price_info = _extract_price_from_text(text)
                        site_results.append({
                            "title": item.get("title", ""),
                            "price": price_info["price"],
                            "extracted_price": price_info["extracted_price"],
                            "link": item.get("href", ""),
                            "source": site,
                            "snippet": item.get("body", ""),
                        })
            except Exception:
                pass

        all_results[site] = site_results[:MAX_RESULTS_PER_SITE]

    return json.dumps({
        "product": product_name,
        "specifications": specifications,
        "results_by_site": all_results,
        "total_results": sum(len(v) for v in all_results.values()),
    })


def search_google_shopping(product_name: str, specifications: str = "") -> str:
    """Search Google Shopping for product listings with prices and links."""
    query = f"{product_name}"
    if specifications:
        query += f" {specifications}"

    results = []

    # Zenserp Shopping search
    data = zenserp_search(query, tbm="shop")
    if data:
        for item in data.get("shopping_results", [])[:10]:
            price_str = item.get("price", "N/A")
            price_info = _extract_price_from_text(price_str) if price_str != "N/A" else {"extracted_price": None}
            results.append({
                "title": item.get("title", ""),
                "price": price_str,
                "extracted_price": price_info.get("extracted_price"),
                "link": item.get("url", item.get("link", "")),
                "source": item.get("source", ""),
                "rating": item.get("rating"),

            })

    # DuckDuckGo fallback
    if len(results) < 5:
        try:
            with DDGS() as ddgs:
                ddg_results = ddgs.text(f"buy {query} price", max_results=15)
                for item in ddg_results:
                    text = f"{item.get('title', '')} {item.get('body', '')}"
                    price_info = _extract_price_from_text(text)
                    results.append({
                        "title": item.get("title", ""),
                        "price": price_info["price"],
                        "extracted_price": price_info["extracted_price"],
                        "link": item.get("href", ""),
                        "source": "DuckDuckGo",
                        "snippet": item.get("body", ""),
                    })
        except Exception:
            pass

    return json.dumps({
        "query": query,
        "shopping_results": results,
        "total": len(results),
    })

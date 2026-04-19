"""Tool to compare prices of products across different platforms."""

import json
import re
from duckduckgo_search import DDGS
from tools.zenserp_client import zenserp_search


def _extract_price_from_text(text: str) -> dict:
    """Extract price information from a text snippet."""
    patterns = [
        r'\$\s*([\d,]+\.?\d*)',
        r'USD\s*([\d,]+\.?\d*)',
        r'Rs\.?\s*([\d,]+\.?\d*)',
        r'₹\s*([\d,]+\.?\d*)',
        r'INR\s*([\d,]+\.?\d*)',
        r'£\s*([\d,]+\.?\d*)',
        r'€\s*([\d,]+\.?\d*)',
    ]
    currency_map = {0: "$", 1: "$", 2: "₹", 3: "₹", 4: "₹", 5: "£", 6: "€"}
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, text)
        if match:
            price_str = match.group(1).replace(",", "")
            try:
                price_val = float(price_str)
                currency = currency_map.get(i, "$")
                return {"price": f"{currency}{price_val:,.2f}", "extracted_price": price_val, "currency": currency}
            except ValueError:
                continue
    return {"price": "See link", "extracted_price": None, "currency": None}


def compare_prices(product_name: str, specifications: str = "") -> str:
    """Compare prices for a specific product across multiple e-commerce platforms."""
    query = f"{product_name}"
    if specifications:
        query += f" {specifications}"

    price_entries = []

    # Zenserp Google Shopping for structured price data
    data = zenserp_search(query, tbm="shop")
    if data:
        for item in data.get("shopping_results", [])[:10]:
            price_str = item.get("price", "")
            price_info = _extract_price_from_text(price_str) if price_str else {"extracted_price": None}
            if price_info.get("extracted_price"):
                price_entries.append({
                    "title": item.get("title", ""),
                    "price": price_str,
                    "extracted_price": price_info["extracted_price"],
                    "source": item.get("source", "Unknown"),
                    "link": item.get("url", item.get("link", "")),
                    "rating": item.get("rating"),
                    "reviews_count": item.get("reviews"),
                })

    # DuckDuckGo fallback — search each major site for prices
    if len(price_entries) < 5:
        sites = ["amazon.com", "flipkart.com", "bestbuy.com", "walmart.com", "ebay.com"]
        for site in sites:
            try:
                with DDGS() as ddgs:
                    ddg_results = ddgs.text(
                        f"{query} price site:{site}", max_results=3
                    )
                    for item in ddg_results:
                        text = f"{item.get('title', '')} {item.get('body', '')}"
                        price_info = _extract_price_from_text(text)
                        price_entries.append({
                            "title": item.get("title", ""),
                            "price": price_info["price"],
                            "extracted_price": price_info["extracted_price"],
                            "source": site.split(".")[0].capitalize(),
                            "link": item.get("href", ""),
                            "snippet": item.get("body", ""),
                        })
            except Exception:
                pass

    # Sort by price (lowest first) where possible
    priced = [p for p in price_entries if p.get("extracted_price")]
    unpriced = [p for p in price_entries if not p.get("extracted_price")]
    priced.sort(key=lambda x: x["extracted_price"])

    sorted_results = priced + unpriced

    # Calculate price stats
    prices = [p["extracted_price"] for p in priced]
    stats = {}
    if prices:
        stats = {
            "lowest_price": min(prices),
            "highest_price": max(prices),
            "average_price": round(sum(prices) / len(prices), 2),
            "price_range": round(max(prices) - min(prices), 2),
            "best_deal_source": priced[0]["source"] if priced else "N/A",
            "best_deal_link": priced[0]["link"] if priced else "N/A",
        }

    return json.dumps({
        "product": product_name,
        "price_comparison": sorted_results,
        "price_statistics": stats,
        "total_listings": len(sorted_results),
    })

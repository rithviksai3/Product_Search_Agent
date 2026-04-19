"""Tool to fetch reviews and ratings for products."""

import json
from duckduckgo_search import DDGS
from config import MAX_REVIEW_RESULTS
from tools.zenserp_client import zenserp_search


def get_product_reviews(product_name: str) -> str:
    """Fetch reviews and ratings for a specific product from the web."""
    results = []

    # Zenserp for Google search results with review snippets
    data = zenserp_search(f"{product_name} reviews ratings")
    if data:
        for item in data.get("organic_results", [])[:MAX_REVIEW_RESULTS]:
            review_entry = {
                "title": item.get("title", ""),
                "source": item.get("displayed_link", item.get("url", "")),
                "link": item.get("url", ""),
                "snippet": item.get("description", ""),
            }
            # Extract rich snippets (ratings) if available
            rich = item.get("rich_snippet", {})
            if rich:
                top = rich.get("top", {})
                review_entry["rating"] = top.get("detected_extensions", {}).get("rating")
                review_entry["reviews_count"] = top.get("detected_extensions", {}).get("reviews")
            results.append(review_entry)

    # Also check Zenserp shopping for ratings
    if len(results) < 5:
        shop_data = zenserp_search(product_name, tbm="shop")
        if shop_data:
            for item in shop_data.get("shopping_results", [])[:5]:
                if item.get("rating"):
                    results.append({
                        "title": item.get("title", ""),
                        "source": item.get("source", ""),
                        "link": item.get("url", item.get("link", "")),
                        "rating": item.get("rating"),
                        "reviews_count": item.get("reviews"),
                        "price": item.get("price", ""),
                    })

    # DuckDuckGo fallback for reviews
    if len(results) < 5:
        try:
            with DDGS() as ddgs:
                ddg_results = ddgs.text(
                    f"{product_name} review rating",
                    max_results=MAX_REVIEW_RESULTS,
                )
                for item in ddg_results:
                    results.append({
                        "title": item.get("title", ""),
                        "source": "Web",
                        "link": item.get("href", ""),
                        "snippet": item.get("body", ""),
                    })
        except Exception:
            pass

    return json.dumps({
        "product": product_name,
        "reviews": results[:MAX_REVIEW_RESULTS],
        "total_reviews_found": len(results),
    })


def get_expert_reviews(product_name: str) -> str:
    """
    Fetch expert/editorial reviews from tech review sites.

    Args:
        product_name: The product to search expert reviews for

    Returns:
        JSON string with expert reviews from trusted sources.
    """
    review_sites = [
        "techradar.com",
        "tomsguide.com",
        "cnet.com",
        "rtings.com",
    ]

    results = []
    for site in review_sites:
        try:
            with DDGS() as ddgs:
                ddg_results = ddgs.text(
                    f"{product_name} review site:{site}",
                    max_results=2,
                )
                for item in ddg_results:
                    results.append({
                        "title": item.get("title", ""),
                        "source": site,
                        "link": item.get("href", ""),
                        "snippet": item.get("body", ""),
                    })
        except Exception:
            continue

    return json.dumps({
        "product": product_name,
        "expert_reviews": results,
        "sources_checked": review_sites,
    })

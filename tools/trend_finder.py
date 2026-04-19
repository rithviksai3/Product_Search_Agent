"""Tool to find trending models and brands for a given product category."""

import json
from duckduckgo_search import DDGS
from tools.zenserp_client import zenserp_search


def find_trending_products(product_query: str, specifications: str = "") -> str:
    """
    Find trending models and brands for a product category.

    Args:
        product_query: The product to search for (e.g., "wireless earbuds")
        specifications: Optional specs like "under $100, noise cancelling"

    Returns:
        JSON string of trending products with brand, model, and key features.
    """
    search_query = f"best trending {product_query} 2026"
    if specifications:
        search_query += f" {specifications}"

    results = []

    # Try Zenserp first (Google search)
    data = zenserp_search(search_query)
    if data:
        for item in data.get("organic_results", [])[:8]:
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("description", ""),
                "link": item.get("url", ""),
            })

    # Fallback / supplement with DuckDuckGo
    if len(results) < 5:
        try:
            with DDGS() as ddgs:
                ddg_results = ddgs.text(search_query, max_results=10)
                for item in ddg_results:
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("body", ""),
                        "link": item.get("href", ""),
                    })
        except Exception:
            pass

    return json.dumps({
        "query": search_query,
        "trending_results": results[:5],
    })


def extract_brands_and_models(product_query: str, specifications: str = "") -> str:
    """
    Search specifically for top brands and models in a product category.

    Args:
        product_query: The product category
        specifications: Optional specifications

    Returns:
        JSON string with brand/model recommendations.
    """
    search_query = f"top 10 best {product_query} brands models 2026"
    if specifications:
        search_query += f" {specifications}"

    results = []

    # Try Zenserp first
    data = zenserp_search(search_query)
    if data:
        for item in data.get("organic_results", [])[:10]:
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("description", ""),
                "link": item.get("url", ""),
            })

    # Fallback to DuckDuckGo
    if len(results) < 5:
        try:
            with DDGS() as ddgs:
                ddg_results = ddgs.text(search_query, max_results=10)
                for item in ddg_results:
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("body", ""),
                        "link": item.get("href", ""),
                    })
        except Exception:
            pass

    return json.dumps({
        "query": search_query,
        "brand_model_results": results,
    })

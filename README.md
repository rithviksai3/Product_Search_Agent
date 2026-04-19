# 🛒 Product Search Agent

An AI-powered product search agent that helps you find the best products by researching across multiple e-commerce platforms, comparing prices, and gathering reviews & ratings — powered by **Groq** (free LLM API), **Zenserp** (Google Search/Shopping), and **DuckDuckGo** as fallback.

## What It Does

1. **Finds Trending Products** — Discovers the most popular and recommended brands/models in any product category
2. **Searches E-Commerce Sites** — Searches across Amazon, Flipkart, Best Buy, Walmart, eBay, and more
3. **Compares Prices** — Side-by-side price comparison across platforms with best-deal identification
4. **Fetches Reviews & Ratings** — User reviews, ratings, and expert reviews from trusted sources (CNET, TechRadar, Tom's Guide, RTINGS)
5. **Provides Purchase Links** — Direct links to buy from each platform

## Architecture

```
User Query
    │
    ▼
┌──────────────────────────────────────┐
│   Groq LLM (llama-3.3-70b-versatile)│
│   Function Calling Orchestrator      │
└──────────┬───────────────────────────┘
           │
    ┌──────┼──────────┬──────────────┬────────────────┐
    ▼      ▼          ▼              ▼                ▼
┌───────┐┌────────┐┌───────────┐┌───────────┐┌────────────┐
│Trend  ││Product ││  Price    ││  Review   ││  Expert    │
│Finder ││Search  ││Comparator ││  Fetcher  ││  Reviews   │
└───┬───┘└───┬────┘└─────┬─────┘└─────┬─────┘└──────┬─────┘
    │        │           │            │              │
    ▼        ▼           ▼            ▼              ▼
┌─────────────────────────────────────────────────────────┐
│  Zenserp (Google Search/Shopping) + DuckDuckGo Fallback │
└─────────────────────────────────────────────────────────┘
```

## Setup

### 1. Install Dependencies

```bash
cd product-search-agent
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

| Key | Required | Source |
|-----|----------|--------|
| `GROQ_API_KEY` | **Yes** | [Groq Console](https://console.groq.com/keys) — free tier available |
| `ZENSERP_API_KEY` | Recommended | [Zenserp](https://zenserp.com/) — free tier: 50 searches/month |
| `GROQ_MODEL` | No | Defaults to `llama-3.3-70b-versatile` |

> **Note:** Without `ZENSERP_API_KEY`, the agent falls back to DuckDuckGo search, which provides less structured product data (no prices or ratings in search results). Zenserp is strongly recommended for the best experience.

### 3. Run the Agent

```bash
python main.py
```

## Usage Examples

```
You: Find me the best wireless earbuds under $100 with noise cancellation

You: I need a gaming laptop with RTX 4060, 16GB RAM, under $1200

You: Compare the latest Samsung and iPhone flagship phones

You: What's the best robot vacuum cleaner for pet hair?

You: Best sneakers under 2000 rupees
```

## Project Structure

```
product-search-agent/
├── main.py                    # Entry point — interactive CLI
├── config.py                  # Configuration and API keys
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (API keys)
├── agent/
│   ├── __init__.py
│   └── product_agent.py       # Groq function-calling agent
├── tools/
│   ├── __init__.py
│   ├── zenserp_client.py      # Zenserp API client with fallback
│   ├── trend_finder.py        # Find trending products & brands
│   ├── product_search.py      # Search e-commerce sites
│   ├── price_comparator.py    # Compare prices across platforms
│   └── review_fetcher.py      # Fetch reviews & ratings
└── utils/
    └── __init__.py             # Display utilities (Rich formatting)
```

## Tools Overview

| Tool | Purpose | Data Source |
|------|---------|-------------|
| `find_trending_products` | Discover trending models/brands | Zenserp + DuckDuckGo |
| `extract_brands_and_models` | Get top brands in a category | Zenserp + DuckDuckGo |
| `search_products_on_ecommerce` | Search across 5 e-commerce sites | Zenserp Shopping + DuckDuckGo |
| `search_google_shopping` | Structured shopping results | Zenserp Shopping + DuckDuckGo |
| `compare_prices` | Price comparison with stats | Zenserp Shopping + DuckDuckGo |
| `get_product_reviews` | User reviews & ratings | Zenserp + DuckDuckGo |
| `get_expert_reviews` | Expert reviews from tech sites | TechRadar, Tom's Guide, CNET, RTINGS |

## Customization

### Add More E-Commerce Sites

Edit `ECOMMERCE_SITES` in `config.py`:

```python
ECOMMERCE_SITES = [
    "amazon.com",
    "flipkart.com",
    "bestbuy.com",
    "walmart.com",
    "ebay.com",
    "newegg.com",      # Add more sites
    "target.com",
]
```

### Change the AI Model

Set `GROQ_MODEL` in `.env`:

```
GROQ_MODEL=llama-3.3-70b-versatile    # Best quality (default)
GROQ_MODEL=llama-3.1-8b-instant       # Faster, lower token usage
```

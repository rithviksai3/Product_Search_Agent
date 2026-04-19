import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ZENSERP_API_KEY = os.getenv("ZENSERP_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

ECOMMERCE_SITES = [
    "amazon.com",
    "flipkart.com",
    "bestbuy.com",
    "walmart.com",
    "ebay.com",
]

MAX_RESULTS_PER_SITE = 3
MAX_REVIEW_RESULTS = 5

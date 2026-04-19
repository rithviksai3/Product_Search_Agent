"""Product Search Agent using Groq API (free, OpenAI-compatible)."""

import json
import re
from openai import OpenAI, BadRequestError
from config import GROQ_API_KEY, GROQ_MODEL
from tools.trend_finder import find_trending_products, extract_brands_and_models
from tools.product_search import search_products_on_ecommerce, search_google_shopping
from tools.price_comparator import compare_prices
from tools.review_fetcher import get_product_reviews, get_expert_reviews

# ── Map tool names to actual functions ────────────────────────────────────────

TOOL_MAP = {
    "find_trending_products": find_trending_products,
    "extract_brands_and_models": extract_brands_and_models,
    "search_products_on_ecommerce": search_products_on_ecommerce,
    "search_google_shopping": search_google_shopping,
    "compare_prices": compare_prices,
    "get_product_reviews": get_product_reviews,
    "get_expert_reviews": get_expert_reviews,
}

# Maximum characters per tool result to stay within Groq token limits
MAX_TOOL_RESULT_CHARS = 1500

# ── Tool definitions (OpenAI format — works with Groq) ───────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "find_trending_products",
            "description": (
                "Find trending models and brands for a product category. "
                "Use this FIRST to discover what's popular in the market."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_query": {
                        "type": "string",
                        "description": "The product category to search for (e.g., 'wireless earbuds', 'gaming laptop')",
                    },
                    "specifications": {
                        "type": "string",
                        "description": "Optional specifications like 'under $100', 'noise cancelling', '16GB RAM'",
                    },
                },
                "required": ["product_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "extract_brands_and_models",
            "description": "Search specifically for top brands and models in a product category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_query": {
                        "type": "string",
                        "description": "The product category",
                    },
                    "specifications": {
                        "type": "string",
                        "description": "Optional specifications",
                    },
                },
                "required": ["product_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_products_on_ecommerce",
            "description": (
                "Search for a specific product across multiple e-commerce websites "
                "(Amazon, Flipkart, Best Buy, Walmart, eBay). Returns product listings with prices and links."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Specific product name or model to search for",
                    },
                    "specifications": {
                        "type": "string",
                        "description": "Optional specifications to narrow the search",
                    },
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_google_shopping",
            "description": (
                "Search Google Shopping for product listings with structured price data, "
                "ratings, and direct purchase links."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Product to search for",
                    },
                    "specifications": {
                        "type": "string",
                        "description": "Optional specifications",
                    },
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_prices",
            "description": (
                "Compare prices for a specific product across multiple platforms. "
                "Returns prices sorted from lowest to highest with price statistics."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "The exact product name/model to compare prices for",
                    },
                    "specifications": {
                        "type": "string",
                        "description": "Optional specifications",
                    },
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_reviews",
            "description": (
                "Fetch reviews and ratings for a specific product from across the web. "
                "Returns user reviews, ratings, and review summaries."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "The exact product name/model to get reviews for",
                    },
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_expert_reviews",
            "description": (
                "Fetch expert/editorial reviews from trusted tech review sites "
                "(TechRadar, Tom's Guide, CNET, RTINGS, Wirecutter, etc.)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "The product to search expert reviews for",
                    },
                },
                "required": ["product_name"],
            },
        },
    },
]

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a Product Search Agent — an expert shopping assistant that helps users \
find the best products by researching across multiple e-commerce platforms.

Your workflow for every product query:

1. **Understand the Query**: Parse the user's product request and any specifications \
   (budget, features, brand preferences).

2. **Find Trending Products**: Use `find_trending_products` and `extract_brands_and_models` \
   to discover what's popular and recommended in the category.

3. **Search E-Commerce Sites**: Use `search_products_on_ecommerce` and/or \
   `search_google_shopping` to find specific products across Amazon, Flipkart, \
   Best Buy, Walmart, eBay, etc.

4. **Compare Prices**: Use `compare_prices` to compare pricing across platforms \
   for the top products you found.

5. **Get Reviews & Ratings**: Use `get_product_reviews` and `get_expert_reviews` \
   to fetch user reviews, ratings, and expert opinions.

6. **Present Results**: Compile everything into a clear, structured recommendation with:
   - **Top Picks** (3-5 products) with name, key specs, and why they're recommended
   - **Price Comparison Table** showing prices across platforms with purchase links
   - **Ratings & Reviews Summary** with scores from users and experts
   - **Best Overall Pick** with reasoning
   - **Best Budget Pick** if applicable
   - **Direct Purchase Links** for each product on each platform

Always provide direct purchase links. Be honest about trade-offs between products. \
If a product has known issues, mention them. Format your final response with clear \
markdown formatting for readability.
"""


class ProductSearchAgent:
    """Agent that orchestrates product search, comparison, and review gathering."""

    def __init__(self):
        self.client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    @staticmethod
    def _truncate_result(result: str, max_chars: int = MAX_TOOL_RESULT_CHARS) -> str:
        """Truncate tool result to stay within token limits."""
        if len(result) <= max_chars:
            return result
        return result[:max_chars] + '\n... (truncated)'

    def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool function by name with given arguments."""
        func = TOOL_MAP.get(tool_name)
        if not func:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        try:
            result = func(**arguments)
            return self._truncate_result(result)
        except Exception as e:
            return json.dumps({"error": f"Tool execution failed: {str(e)}"})

    def _parse_failed_generation(self, failed_text: str):
        """Parse Groq's failed_generation format to extract tool calls.

        Handles format like: <function=tool_name{"arg": "val"}</function>
        """
        pattern = r'<function=(\w+)(.*?)</function>'
        matches = re.findall(pattern, failed_text, re.DOTALL)
        calls = []
        for name, args_str in matches:
            args_str = args_str.strip()
            try:
                args = json.loads(args_str) if args_str else {}
            except json.JSONDecodeError:
                args = {}
            if name in TOOL_MAP:
                calls.append((name, args))
        return calls

    def chat(self, user_message: str, on_tool_call=None) -> str:
        """
        Process a user message through the agent.

        Args:
            user_message: The user's product search query
            on_tool_call: Optional callback(tool_name, args) for UI updates

        Returns:
            The agent's final response with product recommendations.
        """
        self.conversation_history.append(
            {"role": "user", "content": user_message}
        )

        while True:
            try:
                response = self.client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=self.conversation_history,
                    tools=TOOLS,
                    tool_choice="auto",
                )
            except BadRequestError as e:
                # Handle Groq's tool_use_failed by parsing the raw generation
                error_body = e.body if hasattr(e, "body") else {}
                if isinstance(error_body, dict) and error_body.get("code") == "tool_use_failed":
                    failed_text = error_body.get("failed_generation", "")
                    parsed_calls = self._parse_failed_generation(failed_text)
                    if parsed_calls:
                        # Execute the parsed tool calls and feed results back
                        tool_results = []
                        for tool_name, arguments in parsed_calls:
                            if on_tool_call:
                                on_tool_call(tool_name, arguments)
                            result = self._execute_tool(tool_name, arguments)
                            tool_results.append(f"[{tool_name}] {result}")

                        # Add results as an assistant + user exchange
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": f"I called the following tools:\n" + "\n".join(
                                f"- {name}({json.dumps(args)})" for name, args in parsed_calls
                            ),
                        })
                        self.conversation_history.append({
                            "role": "user",
                            "content": "Here are the tool results:\n\n" + "\n\n".join(tool_results)
                            + "\n\nPlease analyze these results and continue with your workflow. "
                            "Call more tools if needed, or provide your final recommendation.",
                        })
                        continue
                raise

            message = response.choices[0].message

            # If the model wants to call tools
            if message.tool_calls:
                self.conversation_history.append(message)

                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)

                    if on_tool_call:
                        on_tool_call(tool_name, arguments)

                    result = self._execute_tool(tool_name, arguments)

                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })

                # Continue the loop to let the model process tool results
                continue

            # Model is done — return the final response
            assistant_message = message.content or ""
            self.conversation_history.append(
                {"role": "assistant", "content": assistant_message}
            )
            return assistant_message

    def reset(self):
        """Reset conversation history."""
        self.conversation_history = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

import json
import logging

from anthropic import Anthropic

logger = logging.getLogger(__name__)


def _build_prompt(merchant_names: list[str], category_names: list[str]) -> str:
    categories_str = ", ".join(category_names)
    merchants_str = "\n".join(f"- {name}" for name in merchant_names)

    return f"""Classify each merchant name into exactly one spending category.

Categories: {categories_str}

Merchant names:
{merchants_str}

Respond with ONLY a JSON array. Each element must have "merchant_name" (exactly as given) and "category" (from the list above). Example:
[{{"merchant_name": "WHOLE FOODS", "category": "Groceries"}}]"""


def classify_merchants(
    merchant_names: list[str],
    category_names: list[str],
) -> dict[str, str]:
    """Classify merchant names via Claude API. Returns {merchant_name: category}."""
    if not merchant_names:
        return {}

    try:
        client = Anthropic()
        prompt = _build_prompt(merchant_names, category_names)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        classifications = json.loads(text)

        result = {}
        valid_categories = set(category_names)
        for item in classifications:
            name = item["merchant_name"]
            category = item["category"]
            if category in valid_categories:
                result[name] = category
            else:
                logger.warning(f"Invalid category '{category}' for '{name}', skipping")

        return result

    except Exception:
        logger.exception("Classification API call failed")
        return {}

# DeepSeek V4 Flash prices per 1,000,000 tokens.
# Source: DeepSeek API docs, Models & Pricing page.
PRICE_INPUT_CACHE_HIT_PER_1M = 0.0028
PRICE_INPUT_CACHE_MISS_PER_1M = 0.14
PRICE_OUTPUT_PER_1M = 0.28


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    *,
    prompt_cache_hit_tokens: int = 0,
    prompt_cache_miss_tokens: int | None = None,
) -> float:
    """
    Calculate DeepSeek V4 Flash API cost.

    If cache hit/miss split is unavailable, all input tokens are priced as cache-miss.
    Reasoning/thinking tokens should be included in output_tokens before calling.
    """
    if prompt_cache_miss_tokens is None:
        prompt_cache_miss_tokens = max(input_tokens - prompt_cache_hit_tokens, 0)

    input_cost = (
        (prompt_cache_hit_tokens / 1_000_000) * PRICE_INPUT_CACHE_HIT_PER_1M
        + (prompt_cache_miss_tokens / 1_000_000) * PRICE_INPUT_CACHE_MISS_PER_1M
    )
    output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT_PER_1M

    return input_cost + output_cost

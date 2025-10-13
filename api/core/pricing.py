# Precios por 1,000,000 tokens para Gemini 2.5 Pro (prompts < 128k tokens)
PRICE_INPUT_LT_128K = 1.25
PRICE_OUTPUT_LT_128K = 10.0

# Precios por 1,000,000 tokens para Gemini 2.5 Pro (prompts > 128k tokens)
PRICE_INPUT_GT_128K = 2.50
PRICE_OUTPUT_GT_128K = 15.0

def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """
    Calcula el costo de una llamada a la API de Gemini 2.5 Pro,
    considerando los diferentes precios según el volumen de tokens.
    Los 'thought_tokens' deben ser sumados a los 'output_tokens' antes de llamar a esta función.
    """
    if input_tokens <= 128000:
        input_cost = (input_tokens / 1_000_000) * PRICE_INPUT_LT_128K
        output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT_LT_128K
    else:
        input_cost = (input_tokens / 1_000_000) * PRICE_INPUT_GT_128K
        output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT_GT_128K
        
    return input_cost + output_cost
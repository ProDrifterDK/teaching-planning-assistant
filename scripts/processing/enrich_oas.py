# Requisitos: pip install httpx tqdm python-dotenv

import argparse
import json
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
from dotenv import load_dotenv
from tqdm import tqdm

# DeepSeek V4 Flash prices per 1,000,000 tokens.
PRICE_INPUT_CACHE_HIT_PER_1M = 0.0028
PRICE_INPUT_CACHE_MISS_PER_1M = 0.14
PRICE_OUTPUT_PER_1M = 0.28


class Stats:
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cache_hit_tokens = 0
        self.total_cache_miss_tokens = 0
        self.total_cost = 0.0
        self.lock = threading.Lock()

    def update(self, input_tokens, output_tokens, cache_hit_tokens, cache_miss_tokens, cost):
        with self.lock:
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_cache_hit_tokens += cache_hit_tokens
            self.total_cache_miss_tokens += cache_miss_tokens
            self.total_cost += cost


def setup_logging():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/enrichment.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def calculate_cost(input_tokens: int, output_tokens: int, cache_hit_tokens: int = 0, cache_miss_tokens: int | None = None) -> float:
    if cache_miss_tokens is None:
        cache_miss_tokens = max(input_tokens - cache_hit_tokens, 0)

    input_cost = (
        (cache_hit_tokens / 1_000_000) * PRICE_INPUT_CACHE_HIT_PER_1M
        + (cache_miss_tokens / 1_000_000) * PRICE_INPUT_CACHE_MISS_PER_1M
    )
    output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT_PER_1M
    return input_cost + output_cost


def load_data(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Archivo no encontrado: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error(f"Error de JSON en el archivo: {filepath}")
        sys.exit(1)


def save_data(data, filepath):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"\nDatos guardados exitosamente en: {filepath}")
    except IOError as e:
        logging.error(f"No se pudo escribir en el archivo {filepath}: {e}")
        sys.exit(1)


def build_deepseek_prompt(oa_text):
    return f"""
Rol: Eres un experto en pedagogía y diseño curricular con un profundo conocimiento de la Taxonomía de Bloom.
Contexto: Analiza el texto de un objetivo de aprendizaje para identificar las habilidades cognitivas clave.
La Tarea: Analiza el siguiente texto:
---
{oa_text}
---
Restricción de Formato de Salida: Responde únicamente con un objeto JSON válido con una clave "skills", que contenga una lista de cadenas de texto (ej: "Analizar", "Crear").
"""


def parse_json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]).strip()
        if text.lower().startswith("json\n"):
            text = text[5:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def get_skills_from_deepseek(text_to_analyze, client, base_url, api_key, model):
    max_retries, backoff_factor, wait_time = 5, 2, 1
    prompt = build_deepseek_prompt(text_to_analyze)
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert Chilean curriculum assistant. Return only one valid JSON object.",
            },
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
        "max_tokens": 512,
    }

    for attempt in range(max_retries):
        try:
            response = client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            response_payload = response.json()
            content = response_payload["choices"][0]["message"]["content"]
            data = parse_json_object(content)
            usage = response_payload.get("usage") or {}
            input_tokens = usage.get("prompt_tokens", 0) or 0
            output_tokens = usage.get("completion_tokens", 0) or 0
            cache_hit_tokens = usage.get("prompt_cache_hit_tokens", 0) or 0
            cache_miss_tokens = usage.get("prompt_cache_miss_tokens", 0) or max(input_tokens - cache_hit_tokens, 0)

            if "skills" in data and isinstance(data["skills"], list):
                return data["skills"], input_tokens, output_tokens, cache_hit_tokens, cache_miss_tokens

            logging.warning(f"Respuesta JSON inesperada: {data}")
            return [], input_tokens, output_tokens, cache_hit_tokens, cache_miss_tokens

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logging.error(f"Error decodificando o procesando respuesta de DeepSeek: {e}")
            return [], 0, 0, 0, 0
        except Exception as e:
            logging.warning(f"Error en la API DeepSeek (intento {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(wait_time)
                wait_time *= backoff_factor
            else:
                logging.error(f"Fallo en la API DeepSeek después de {max_retries} intentos.")
                return [], 0, 0, 0, 0
    return [], 0, 0, 0, 0


def process_single_oa(oa, client, base_url, api_key, model, stats):
    text_to_analyze = oa.get("descripcion_oa", "")
    if desglose := oa.get("desglose_componentes"):
        text_to_analyze += "\n" + "\n".join(desglose)

    if not text_to_analyze.strip():
        oa["habilidades"] = []
        return

    skills, input_tokens, output_tokens, cache_hit_tokens, cache_miss_tokens = get_skills_from_deepseek(
        text_to_analyze, client, base_url, api_key, model
    )
    oa["habilidades"] = sorted(list(set(skills))) if skills else []

    cost = calculate_cost(input_tokens, output_tokens, cache_hit_tokens, cache_miss_tokens)
    stats.update(input_tokens, output_tokens, cache_hit_tokens, cache_miss_tokens, cost)


def process_oas_concurrently(data, client, base_url, api_key, model, max_workers, stats):
    tasks = [oa for asignatura in data for eje in asignatura.get("ejes", []) for oa in eje.get("oas", [])]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_single_oa, oa, client, base_url, api_key, model, stats)
            for oa in tasks
        }

        for future in tqdm(as_completed(futures), total=len(tasks), desc="Procesando OAs"):
            try:
                future.result()
            except Exception as exc:
                logging.error(f"Un OA generó una excepción: {exc}")
    logging.info("Procesamiento concurrente finalizado.")
    return data


def main():
    load_dotenv()
    setup_logging()

    parser = argparse.ArgumentParser(description="Enriquece OAs con habilidades cognitivas.")
    parser.add_argument("input_file", nargs="?", default="data/raw/structured_data_raw.json", help="Ruta al JSON de entrada.")
    parser.add_argument("output_file", nargs="?", default="data/processed/structured_data_enriched.json", help="Ruta al JSON de salida.")
    parser.add_argument("--workers", type=int, default=10, help="Número de hilos concurrentes.")
    args = parser.parse_args()

    start_time = time.time()
    logging.info(f"Iniciando. In: {args.input_file}, Out: {args.output_file}, Workers: {args.workers}")

    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("AI_API_KEY")
    if not api_key:
        logging.error("DEEPSEEK_API_KEY no configurada.")
        sys.exit(1)

    base_url = os.getenv("DEEPSEEK_BASE_URL") or os.getenv("AI_BASE_URL") or "https://api.deepseek.com/v1"
    model = os.getenv("DEEPSEEK_MODEL") or os.getenv("AI_MODEL") or "deepseek-v4-flash"

    stats = Stats()
    data_to_process = load_data(args.input_file)
    with httpx.Client(timeout=httpx.Timeout(30.0, read=90.0)) as client:
        enriched_data = process_oas_concurrently(
            data_to_process, client, base_url, api_key, model, args.workers, stats
        )
    save_data(enriched_data, args.output_file)

    elapsed_time = time.time() - start_time
    logging.info("--- RESUMEN ---")
    logging.info(f"Tiempo total: {elapsed_time:.2f}s.")
    logging.info(f"Tokens Totales (In/Out): {stats.total_input_tokens}/{stats.total_output_tokens}")
    logging.info(f"Cache hit/miss tokens: {stats.total_cache_hit_tokens}/{stats.total_cache_miss_tokens}")
    logging.info(f"Costo Total Estimado: ${stats.total_cost:.6f}")
    logging.info("Finalizado.")


if __name__ == "__main__":
    main()

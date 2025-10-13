# Requisitos: pip install google-genai tqdm python-dotenv

from google.genai import types
import google.genai as genai
import json
import os
import sys
import time
import logging
import argparse
import threading
from tqdm import tqdm
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Precios por 1,000,000 tokens para Gemini 1.5 Pro
PRICE_INPUT_LT_128K = 1.25
PRICE_OUTPUT_LT_128K = 10.0
PRICE_INPUT_GT_128K = 2.50
PRICE_OUTPUT_GT_128K = 15.0

class Stats:
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_thought_tokens = 0
        self.total_cost = 0.0
        self.lock = threading.Lock()

    def update(self, input_tokens, output_tokens, thought_tokens, cost):
        with self.lock:
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.total_thought_tokens += thought_tokens
            self.total_cost += cost

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/enrichment.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    if input_tokens <= 128000:
        input_cost = (input_tokens / 1_000_000) * PRICE_INPUT_LT_128K
        output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT_LT_128K
    else:
        input_cost = (input_tokens / 1_000_000) * PRICE_INPUT_GT_128K
        output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT_GT_128K
    return input_cost + output_cost

def load_data(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
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
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"Datos guardados en: {filepath}")
    except IOError as e:
        logging.error(f"No se pudo escribir en el archivo {filepath}: {e}")
        sys.exit(1)

def build_gemini_prompt(oa_text):
    return f"""
Rol: Eres un experto en pedagogía y diseño curricular, con un profundo conocimiento de la Taxonomía de Bloom.
Contexto: Analiza el siguiente objetivo de aprendizaje para identificar las habilidades cognitivas clave que un estudiante debe demostrar.
La Tabla de la Taxonomía: ... (La tabla completa se omitió por brevedad, pero estaría aquí) ...
La Tarea: Analiza el siguiente texto:
---
{oa_text}
---
Restricción de Formato de Salida: Devuelve tu respuesta únicamente como un objeto JSON válido con una sola clave "skills", que contiene una lista de cadenas de texto de la taxonomía.
"""

def get_skills_from_gemini(text_to_analyze, client):
    max_retries = 5
    backoff_factor = 2
    wait_time = 1
    prompt = build_gemini_prompt(text_to_analyze)
    
    full_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=-1,
            include_thoughts=True
        )
    )

    for attempt in range(max_retries):
        raw_response_text = ""
        input_tokens, output_tokens, thought_tokens = 0, 0, 0
        try:
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config=full_config
            )
            raw_response_text = response.text
            data = json.loads(raw_response_text.strip().replace("```json", "").replace("```", "").strip())

            if response.usage_metadata:
                input_tokens = response.usage_metadata.prompt_token_count or 0
                output_tokens = response.usage_metadata.candidates_token_count or 0
                thought_tokens = response.usage_metadata.thoughts_token_count or 0

            if "skills" in data and isinstance(data["skills"], list):
                return data["skills"], input_tokens, output_tokens, thought_tokens
            else:
                logging.warning(f"Respuesta JSON inesperada: {raw_response_text}.")
                return [], input_tokens, output_tokens, thought_tokens

        except json.JSONDecodeError:
            logging.error(f"No se pudo decodificar JSON: '{raw_response_text}'")
            return [], input_tokens, output_tokens, thought_tokens
        except Exception as e:
            logging.warning(f"Error en la API (intento {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(wait_time)
                wait_time *= backoff_factor
            else:
                logging.error(f"Fallo en la API después de {max_retries} intentos.")
                return [], input_tokens, output_tokens, thought_tokens
    return [], 0, 0, 0

def process_oas(data, client, max_workers, stats):
    tasks = [oa for asignatura in data for eje in asignatura.get('ejes', []) for oa in eje.get('oas', [])]

    def worker(oa, stats_obj):
        oa_id = oa.get('oa_codigo_oficial', 'ID Desconocido')
        text_to_analyze = oa.get('descripcion_oa', '')
        desglose = oa.get('desglose_componentes')
        if desglose and isinstance(desglose, list):
            text_to_analyze += "\n" + "\n".join(desglose)
        
        if not text_to_analyze.strip():
            oa['habilidades'] = []
            return
        
        skills, input_tokens, output_tokens, thought_tokens = get_skills_from_gemini(text_to_analyze, client)
        oa['habilidades'] = sorted(skills) if skills else []
        cost = calculate_cost(input_tokens, output_tokens + thought_tokens)
        stats_obj.update(input_tokens, output_tokens, thought_tokens, cost)

        if skills:
            logging.info(f"OA {oa_id} OK. Costo: ${cost:.6f}, Tokens(I/O/T): {input_tokens}/{output_tokens}/{thought_tokens}")
        else:
            logging.warning(f"OA {oa_id} FAILED.")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker, oa, stats) for oa in tasks}
        for future in tqdm(as_completed(futures), total=len(tasks), desc="Procesando OAs"):
            future.result()

    return data

def main():
    load_dotenv()
    setup_logging()
    parser = argparse.ArgumentParser(description="Enriquece OAs con habilidades cognitivas.")
    parser.add_argument("input_file", nargs='?', default="data/raw/structured_data_raw.json")
    parser.add_argument("output_file", nargs='?', default="data/processed/structured_data_enriched.json")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()
    
    start_time = time.time()
    logging.info(f"Iniciando. In: {args.input_file}, Out: {args.output_file}, Workers: {args.workers}")

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logging.error("GEMINI_API_KEY no configurada.")
        sys.exit(1)
    
    stats = Stats()
    client = genai.Client(api_key=api_key)

    data = load_data(args.input_file)
    enriched_data = process_oas(data, client, args.workers, stats)
    save_data(enriched_data, args.output_file)
    
    elapsed_time = time.time() - start_time
    logging.info("--- RESUMEN ---")
    logging.info(f"Tiempo total: {elapsed_time:.2f}s.")
    logging.info(f"Tokens Totales (In/Out/Thought): {stats.total_input_tokens}/{stats.total_output_tokens}/{stats.total_thought_tokens}")
    logging.info(f"Costo Total: ${stats.total_cost:.6f}")
    logging.info("Finalizado.")

if __name__ == "__main__":
    main()
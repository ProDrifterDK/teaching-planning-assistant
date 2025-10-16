# Requisitos: pip install google-genai tqdm python-dotenv

import google.genai as genai
from google.genai import types
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
    # Este script probablemente no superará los 128k tokens por prompt.
    input_cost = (input_tokens / 1_000_000) * PRICE_INPUT_LT_128K
    output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT_LT_128K
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
        logging.info(f"\nDatos guardados exitosamente en: {filepath}")
    except IOError as e:
        logging.error(f"No se pudo escribir en el archivo {filepath}: {e}")
        sys.exit(1)

def build_gemini_prompt(oa_text):
    # Omitimos la tabla de taxonomía por brevedad, pero estaría aquí como en la versión anterior.
    return f"""
Rol: Eres un experto en pedagogía y diseño curricular con un profundo conocimiento de la Taxonomía de Bloom.
Contexto: Analiza el texto de un objetivo de aprendizaje para identificar las habilidades cognitivas clave.
La Tarea: Analiza el siguiente texto:
---
{oa_text}
---
Restricción de Formato de Salida: Responde únicamente con un objeto JSON válido con una clave "skills", que contenga una lista de cadenas de texto (ej: "Analizar", "Crear").
"""

def get_skills_from_gemini(text_to_analyze, client):
    max_retries, backoff_factor, wait_time = 5, 2, 1
    prompt = build_gemini_prompt(text_to_analyze)
    
    # La configuración ahora es un objeto `types.GenerationConfig`
    generation_config = types.GenerationConfig(
        response_mime_type="application/json",
        candidate_count=1,
        temperature=0.3
    )
    
    model = client.get_model('gemini-2.5-pro-latest')
    
    for attempt in range(max_retries):
        response = None
        try:
            response = model.generate_content(
                contents=prompt,
                generation_config=generation_config
            )
            data = json.loads(response.text)
            
            usage = response.usage_metadata
            input_tokens = usage.prompt_token_count if usage else 0
            output_tokens = usage.candidates_token_count if usage else 0
            
            if "skills" in data and isinstance(data["skills"], list):
                return data["skills"], input_tokens, output_tokens
            else:
                logging.warning(f"Respuesta JSON inesperada: {data}")
                return [], input_tokens, output_tokens

        except (json.JSONDecodeError, AttributeError) as e:
            error_text = response.text if response and hasattr(response, 'text') else 'No response text available'
            logging.error(f"Error decodificando o procesando respuesta: {error_text}. Error: {e}")
            return [], 0, 0
        except Exception as e:
            logging.warning(f"Error en la API (intento {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(wait_time)
                wait_time *= backoff_factor
            else:
                logging.error(f"Fallo en la API después de {max_retries} intentos.")
                return [], 0, 0
    return [], 0, 0

def process_single_oa(oa, client, stats):
    oa_id = oa.get('oa_codigo_oficial', 'ID Desconocido')
    text_to_analyze = oa.get('descripcion_oa', '')
    if desglose := oa.get('desglose_componentes'):
        text_to_analyze += "\n" + "\n".join(desglose)
    
    if not text_to_analyze.strip():
        oa['habilidades'] = []
        return
    
    skills, input_tokens, output_tokens = get_skills_from_gemini(text_to_analyze, client)
    oa['habilidades'] = sorted(list(set(skills))) if skills else []
    
    # El nuevo SDK no devuelve `thought_tokens` en la respuesta estándar.
    cost = calculate_cost(input_tokens, output_tokens)
    stats.update(input_tokens, output_tokens, 0, cost)

def process_oas_concurrently(data, client, max_workers, stats):
    tasks = [oa for asignatura in data for eje in asignatura.get('ejes', []) for oa in eje.get('oas', [])]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_oa, oa, client, stats) for oa in tasks}
        
        for future in tqdm(as_completed(futures), total=len(tasks), desc="Procesando OAs"):
            try:
                future.result()
            except Exception as exc:
                logging.error(f'Un OA generó una excepción: {exc}')
    logging.info("Procesamiento concurrente finalizado.")
    return data

def main():
    load_dotenv()
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Enriquece OAs con habilidades cognitivas.")
    parser.add_argument("input_file", nargs='?', default="data/raw/structured_data_raw.json", help="Ruta al JSON de entrada.")
    parser.add_argument("output_file", nargs='?', default="data/processed/structured_data_enriched.json", help="Ruta al JSON de salida.")
    parser.add_argument("--workers", type=int, default=10, help="Número de hilos concurrentes.")
    args = parser.parse_args()
    
    start_time = time.time()
    logging.info(f"Iniciando. In: {args.input_file}, Out: {args.output_file}, Workers: {args.workers}")
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logging.error("GEMINI_API_KEY no configurada.")
        sys.exit(1)
    
    stats = Stats()
    client = genai.Client(api_key=api_key)

    data_to_process = load_data(args.input_file)
    enriched_data = process_oas_concurrently(data_to_process, client, args.workers, stats)
    save_data(enriched_data, args.output_file)
    
    elapsed_time = time.time() - start_time
    logging.info("--- RESUMEN ---")
    logging.info(f"Tiempo total: {elapsed_time:.2f}s.")
    logging.info(f"Tokens Totales (In/Out): {stats.total_input_tokens}/{stats.total_output_tokens}")
    logging.info(f"Costo Total Estimado: ${stats.total_cost:.6f}")
    logging.info("Finalizado.")

if __name__ == "__main__":
    main()
# Requisitos: pip install google-generativeai tqdm python-dotenv

from google import genai
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

# Precios por 1,000,000 tokens para Gemini 1.5 Pro (prompts < 128k tokens)
PRICE_INPUT_TEXT = 1.25
PRICE_OUTPUT_TEXT = 10.0

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

def get_gemini_api_key():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logging.error("La variable de entorno 'GEMINI_API_KEY' no está configurada.")
        sys.exit(1)
    return api_key

def load_data(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Archivo no encontrado en la ruta: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error(f"Error al decodificar el JSON del archivo: {filepath}")
        sys.exit(1)

def save_data(data, filepath):
    try:
        output_dir = os.path.dirname(filepath)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logging.info(f"Directorio de salida creado en: {output_dir}")
            
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"Datos enriquecidos guardados exitosamente en: {filepath}")
    except IOError as e:
        logging.error(f"No se pudo escribir en el archivo de salida {filepath}: {e}")
        sys.exit(1)

def build_gemini_prompt(oa_text):
    bloom_taxonomy_table = """
| Nivel (Level) | Definición para la IA | Verbos de Acción Asociados | Tarea de Ejemplo |
| :---- | :---- | :---- | :---- |
| **Recordar (Remember)** | Recuperar hechos, términos, conceptos básicos y respuestas de la memoria a largo plazo. | definir, listar, nombrar, recordar, repetir, relatar, reconocer, seleccionar | Listar las capitales de los países de América del Sur. |
| **Comprender (Understand)** | Construir significado a partir de mensajes, incluyendo comunicación oral, escrita y gráfica. | clasificar, describir, discutir, explicar, identificar, reportar, resumir, traducir | Explicar con sus propias palabras el concepto de fotosíntesis. |
| **Aplicar (Apply)** | Usar o implementar un procedimiento en una situación dada o desconocida. | aplicar, elegir, demostrar, implementar, resolver, usar, ejecutar, dramatizar | Resolver un problema matemático de dos pasos utilizando la fórmula correcta. |
| **Analizar (Analyze)** | Descomponer la información en sus partes constituyentes para explorar relaciones y la estructura organizativa. | analizar, comparar, contrastar, diferenciar, examinar, organizar, deconstruir, atribuir | Comparar y contrastar las motivaciones de dos personajes principales en una novela. |
| **Evaluar (Evaluate)** | Hacer juicios y justificar decisiones basadas en criterios y estándares. | argumentar, criticar, defender, juzgar, justificar, valorar, recomendar, evaluar | Escribir una crítica de una película, justificando la calificación con ejemplos específicos. |
| **Crear (Create)** | Juntar elementos para formar un todo coherente o funcional; generar, planificar o producir para crear un nuevo producto o punto de vista. | construir, diseñar, formular, generar, inventar, planificar, producir, componer | Diseñar un experimento para probar una hipótesis sobre el crecimiento de las plantas. |
"""

    prompt_structure = f"""
Rol: Eres un experto en pedagogía y diseño curricular, con un profundo conocimiento de la Taxonomía de Bloom.
Contexto: Se te proporcionará el texto de un objetivo de aprendizaje. Tu tarea es analizar este texto e identificar las principales habilidades cognitivas que un estudiante debe demostrar. Utiliza la tabla proporcionada de los niveles y verbos de la Taxonomía de Bloom como tu guía.
La Tabla de la Taxonomía: Aquí está la definición de la Taxonomía de Bloom a la que debes adherirte estrictamente:
{bloom_taxonomy_table}
La Tarea: Analiza el siguiente texto del objetivo de aprendizaje:
---
{oa_text}
---
Restricción de Formato de Salida: Devuelve tu respuesta únicamente como un objeto JSON válido con una sola clave "skills", que contiene una lista de cadenas de texto. Las cadenas deben ser uno de los seis nombres oficiales de nivel de la taxonomía: "Recordar", "Comprender", "Aplicar", "Analizar", "Evaluar", "Crear". No proporciones ninguna otra explicación o texto fuera del objeto JSON.
"""
    return prompt_structure

def get_skills_from_gemini(text_to_analyze, client):
    max_retries = 5
    backoff_factor = 2
    wait_time = 1

    prompt = build_gemini_prompt(text_to_analyze)
    
    thinking_config = genai.types.ThinkingConfig(
        thinking_budget=-1,  # Activar pensamiento dinámico
        include_thoughts=True
    )

    for attempt in range(max_retries):
        raw_response_text = ""
        input_tokens, output_tokens, thought_tokens = 0, 0, 0
        try:
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                thinking_config=thinking_config
            )
            raw_response_text = response.text
            cleaned_response = raw_response_text.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_response)

            if hasattr(response, 'usage_metadata'):
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count
                thought_tokens = response.usage_metadata.thoughts_token_count if hasattr(response.usage_metadata, 'thoughts_token_count') else 0

            if "skills" in data and isinstance(data["skills"], list):
                return data["skills"], input_tokens, output_tokens, thought_tokens
            else:
                logging.warning(f"Respuesta JSON inesperada: {cleaned_response}.")
                return [], input_tokens, output_tokens, thought_tokens

        except json.JSONDecodeError:
            logging.error(f"No se pudo decodificar la respuesta JSON: '{raw_response_text}'")
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
    
    tasks = []
    for asignatura_curso in data:
        for eje in asignatura_curso.get('ejes', []):
            for oa in eje.get('oas', []):
                tasks.append(oa)

    def worker(oa, stats_obj):
        oa_id = oa.get('oa_codigo_oficial', 'ID Desconocido')
        text_to_analyze = oa.get('descripcion_oa', '')
        desglose = oa.get('desglose_componentes')

        if desglose and isinstance(desglose, list):
            text_to_analyze += "\n" + "\n".join(desglose)
        
        if not text_to_analyze.strip():
            logging.warning(f"OA {oa_id} sin texto. Saltando.")
            oa['habilidades'] = []
            return
        
        skills, input_tokens, output_tokens, thought_tokens = get_skills_from_gemini(text_to_analyze, client)
        oa['habilidades'] = sorted(skills) if skills else []

        cost = (input_tokens / 1000000 * PRICE_INPUT_TEXT) + ((output_tokens + thought_tokens) / 1000000 * PRICE_OUTPUT_TEXT)
        stats_obj.update(input_tokens, output_tokens, thought_tokens, cost)

        if skills:
            logging.info(f"OA {oa_id} OK. Costo: ${cost:.6f}, Tokens(I/O/T): {input_tokens}/{output_tokens}/{thought_tokens}, Skills: {oa['habilidades']}")
        else:
            logging.warning(f"OA {oa_id} FAILED. No se obtuvieron skills.")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker, oa, stats) for oa in tasks}
        for future in tqdm(as_completed(futures), total=len(tasks), desc="Procesando OAs"):
            try:
                future.result()
            except Exception as exc:
                logging.error(f'Un OA generó una excepción: {exc}')

    return data

def main():
    load_dotenv()
    setup_logging()
    parser = argparse.ArgumentParser(description="Enriquece OAs con habilidades cognitivas usando la API de Gemini.")
    parser.add_argument("input_file", nargs='?', default="data/raw/structured_data_raw.json", help="Ruta al archivo JSON de entrada.")
    parser.add_argument("output_file", nargs='?', default="data/processed/structured_data_enriched.json", help="Ruta al archivo JSON de salida.")
    parser.add_argument("--workers", type=int, default=10, help="Número de hilos paralelos.")
    
    args = parser.parse_args()
    
    start_time = time.time()
    logging.info("Inicio del script de enriquecimiento.")
    logging.info(f"Archivo de entrada: {args.input_file}")
    logging.info(f"Archivo de salida: {args.output_file}")
    logging.info(f"Usando {args.workers} workers.")

    get_gemini_api_key()

    stats = Stats()
    stats.total_thought_tokens = 0

    try:
        client = genai.Client()
    except Exception as e:
        logging.error(f"Fallo al inicializar el Cliente Gemini: {e}")
        sys.exit(1)

    data = load_data(args.input_file)
    enriched_data = process_oas(data, client, args.workers, stats)
    save_data(enriched_data, args.output_file)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    logging.info("--- RESUMEN DE EJECUCIÓN ---")
    logging.info(f"Tiempo total: {elapsed_time:.2f} segundos.")
    logging.info(f"Tokens de entrada totales: {stats.total_input_tokens}")
    logging.info(f"Tokens de salida totales: {stats.total_output_tokens}")
    logging.info(f"Tokens de pensamiento totales: {stats.total_thought_tokens}")
    logging.info(f"Costo total estimado: ${stats.total_cost:.6f}")
    logging.info("Script de enriquecimiento finalizado.")

if __name__ == "__main__":
    main()
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
import os
import logging
import time

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
BASE_URL = "https://www.curriculumnacional.cl"
OUTPUT_FILE = "curriculum_structured_data/02_structured_json/structured_data_scraped.json"

def get_soup(url):
    """Fetches a URL and returns a BeautifulSoup object."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return BeautifulSoup(response.text, 'html.parser') # Use .text to get decoded string
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_subject_data(subject_url):
    """Extracts all curriculum data from a single subject page into a structured dictionary."""
    soup = get_soup(subject_url)
    if not soup:
        return None

    # Extract Asignatura and Curso from the H1 title
    h1_element = soup.find('h1')
    title_text = h1_element.get_text(strip=True) if h1_element else 'Asignatura Desconocida 0° Desconocido'
    
    match = re.match(r'(.+?)\s+([\d°]+(?:st|nd|rd|th)?\s*\w+)', title_text, re.IGNORECASE)
    if match:
        asignatura_name = match.group(1).strip()
        curso_name = match.group(2).strip()
    else:
        asignatura_name = "Desconocida"
        curso_name = "Desconocido"

    # --- Structured Data Initialization ---
    subject_data = {
        "asignatura": asignatura_name,
        "curso": curso_name,
        "actitudes": [],
        "habilidades": [],
        "ejes": []
    }

    # --- Scrape Actitudes ---
    actitud_header = soup.find('h2', id=re.compile(r'^actitud-'))
    if actitud_header:
        # Navigate to the wrapper containing all attitude items
        current_element = actitud_header.find_next_sibling()
        while current_element:
            actitud_items = current_element.select('div.item-wrapper')
            for item in actitud_items:
                codigo_element = item.select_one('span.number-title')
                desc_element = item.select_one('div.field--name-description')
                if codigo_element and desc_element:
                    subject_data["actitudes"].append({
                        "codigo": codigo_element.get_text(strip=True),
                        "descripcion": desc_element.get_text(strip=True)
                    })
            # This logic assumes attitudes for a subject are grouped together
            if current_element.find_next_sibling('h2'): # Stop if we hit the next major header
                break
            current_element = current_element.find_next_sibling()
            
    # --- Scrape Ejes and their OAs ---
    eje_headers = soup.select('div.content-wrapper h3[id^="eje-"]')
    eje_dict = {}
    for eje_header in eje_headers:
        eje_name = eje_header.get_text(strip=True)
        eje_obj = {"nombre_eje": eje_name, "oas": []}
        subject_data["ejes"].append(eje_obj)
        
        # Find all OA items under this eje
        items_wrapper = eje_header.find_next_sibling('div', class_='item-wrappers')
        if not items_wrapper:
            continue
            
        oa_items = items_wrapper.select('div.item-wrapper')
        for item in oa_items:
            oa_title_element = item.select_one('h4.wrapper-title-oa span.oa-title')
            oa_number_element = item.select_one('h4.wrapper-title-oa span.number-title')
            description_element = item.select_one('div.field--name-description')
            
            if not oa_title_element or not description_element:
                continue

            oa_number = oa_number_element.get_text(strip=True) if oa_number_element else ""
            
            desglose = [li.get_text(strip=True) for li in description_element.select('ul > li')]
            
            # Get main description text without the list items
            main_desc = ""
            p_tag = description_element.find('p')
            if p_tag:
                 main_desc = p_tag.get_text(strip=True)
            else: # Fallback if no <p> tag
                 main_desc = description_element.get_text(strip=True).split('\n')[0]


            eje_obj["oas"].append({
                "oa_codigo_oficial": oa_number,
                "descripcion_oa": main_desc,
                "desglose_componentes": desglose
            })
            
    return subject_data

def generate_urls():
    """Generates the full list of curriculum URLs to scrape."""
    urls = []
    base_url = "https://www.curriculumnacional.cl/curriculum"

    # --- 1° a 6° Básico ---
    grade_range_1_6 = "1o-6o-basico"
    grades_1_6 = [f"{i}-basico" for i in range(1, 7)]
    subjects_1_6 = [
        "lenguaje-comunicacion", "matematica", "ciencias-naturales",
        "artes-visuales", "educacion-fisica-salud",
        "historia-geografia-ciencias-sociales", "ingles-propuesta",
        "lengua-cultura-pueblos-originarios-ancestrales",
        "musica", "orientacion", "religion", "tecnologia"
    ]
    for subject in subjects_1_6:
        for grade in grades_1_6:
            urls.append(f"{base_url}/{grade_range_1_6}/{subject}/{grade}")
            
    # --- 7° Básico a 2° Medio ---
    grade_range_7_2 = "7o-basico-2o-medio"
    grades_7_2 = ["7-basico", "8-basico", "1-medio", "2-medio"]
    # Corrected subject slugs for the higher grades, based on user feedback
    subjects_7_2 = [
        "lengua-literatura", "matematica", "ciencias-naturales", "artes-visuales",
        "educacion-fisica-salud", "historia-geografia-ciencias-sociales",
        "ingles", "musica", "orientacion", "tecnologia"
    ]
    for subject in subjects_7_2:
        for grade in grades_7_2:
            urls.append(f"{base_url}/{grade_range_7_2}/{subject}/{grade}")

    logging.info(f"Generated a total of {len(urls)} URLs to scrape.")
    return urls

def main():
    """Main function to orchestrate the scraping process."""
    logging.info("--- Starting Web Scraping Process ---")
    start_time = time.time()

    target_urls = generate_urls()
    all_data = []
    
    for i, url in enumerate(target_urls):
        logging.info(f"Scraping URL {i+1}/{len(target_urls)}: {url}")
        data = extract_subject_data(url)
        if data and (data['ejes'] or data['actitudes']):
            all_data.append(data)
            num_oas = sum(len(eje.get('oas', [])) for eje in data.get('ejes', []))
            num_actitudes = len(data.get('actitudes', []))
            logging.info(f"  -> Success: Found {num_oas} OAs and {num_actitudes} Actitudes.")
        else:
            logging.warning(f"  -> Warning: No data extracted from {url}. This may be expected (e.g., 'Religión') or a broken link.")
        time.sleep(0.1) # A small delay to be polite to the server

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Save the final data to a JSON file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)
        
    end_time = time.time()
    duration = end_time - start_time
    logging.info(f"--- Scraping Complete in {duration:.2f} seconds ---")
    logging.info(f"Successfully saved {len(all_data)} items to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
import os
import logging
import time
from unidecode import unidecode

# --- Configuration ---
# Set up basic logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Set up a specific logger for 404 errors to a file
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)
file_handler = logging.FileHandler('not_found_urls.log', 'w', 'utf-8')
file_handler.setFormatter(logging.Formatter('%(message)s'))
error_logger.addHandler(file_handler)

BASE_URL = "https://www.curriculumnacional.cl"
OUTPUT_FILE = "curriculum_structured_data/02_structured_json/structured_data_scraped.json"

def get_soup(url):
    """Fetches a URL and returns a BeautifulSoup object."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            error_logger.error(f"404 Client Error: Not Found for url {url}")
        else:
            logging.error(f"HTTP Error fetching {url}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        return None

def extract_subject_data(subject_url):
    """Extracts all curriculum data from a single subject page into a structured dictionary."""
    soup = get_soup(subject_url)
    if not soup:
        return None

    h1_element = soup.find('h1')
    title_text = h1_element.get_text(strip=True) if h1_element else 'Asignatura Desconocida 0° Desconocido'
    
    match = re.match(r'(.+?)\s+(\d+[°º]?\s+Medio\s+(?:FG|HC|TP)|[\d°]+(?:st|nd|rd|th)?\s*\w+)', title_text, re.IGNORECASE)
    if match:
        asignatura_name = match.group(1).strip()
        curso_name = match.group(2).strip()
    else:
        parts = title_text.split()
        asignatura_name = " ".join(parts[:-2]) if len(parts) > 2 else "Desconocida"
        curso_name = " ".join(parts[-2:]) if len(parts) > 2 else "Desconocido"

    subject_data = {
        "asignatura": asignatura_name,
        "curso": curso_name,
        "actitudes": [],
        "habilidades": [],
        "ejes": []
    }

    actitud_header = soup.find('h2', id=re.compile(r'^actitud-'))
    if actitud_header:
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
            if current_element.find_next_sibling('h2'):
                break
            current_element = current_element.find_next_sibling()
            
    eje_headers = soup.select('div.content-wrapper h3[id^="eje-"]')
    
    if eje_headers:
        for eje_header in eje_headers:
            eje_name = eje_header.get_text(strip=True)
            eje_obj = {"nombre_eje": eje_name, "oas": []}
            subject_data["ejes"].append(eje_obj)
            
            items_wrapper = eje_header.find_next_sibling('div', class_='item-wrappers')
            if items_wrapper:
                oa_items = items_wrapper.select('div.item-wrapper')
                for item in oa_items:
                    extract_and_append_oa(item, eje_obj)
    else:
        eje_obj = {"nombre_eje": "Formación General", "oas": []}
        if 'tp' in curso_name.lower():
            eje_obj["nombre_eje"] = "Formación Técnico-Profesional"

        subject_data["ejes"].append(eje_obj)
        
        oa_items = soup.select('div.content-wrapper .item-wrapper')
        for item in oa_items:
            if item.select_one('h4.wrapper-title-oa span.oa-title'):
                 extract_and_append_oa(item, eje_obj)
    
    if len(subject_data["ejes"]) == 1 and not subject_data["ejes"][0]["oas"]:
        if not subject_data["actitudes"]:
             return None
        subject_data["ejes"] = []

    return subject_data

def extract_and_append_oa(item_soup, eje_obj):
    """Helper function to extract a single OA and append it to the eje object."""
    oa_code_element = item_soup.select_one('h4.wrapper-title-oa span.number-title, h4.wrapper-title-oa span.oa-title')
    description_element = item_soup.select_one('div.field--name-description')

    if not oa_code_element or not description_element:
        return

    oa_code = oa_code_element.get_text(strip=True)
    parts = oa_code.split()
    if len(parts) > 1 and " ".join(parts[:len(parts)//2]) == " ".join(parts[len(parts)//2:]):
        oa_code = " ".join(parts[:len(parts)//2])

    desglose = [li.get_text(strip=True) for li in description_element.select('ul > li')]
    
    main_desc = ""
    p_tag = description_element.find('p', recursive=False)
    if p_tag:
        main_desc = p_tag.get_text(strip=True)
    else:
        clone = BeautifulSoup(str(description_element), 'html.parser')
        ul_tag = clone.find('ul')
        if ul_tag:
            ul_tag.decompose()
        main_desc = clone.get_text(strip=True)

    eje_obj["oas"].append({
        "oa_codigo_oficial": oa_code,
        "descripcion_oa": main_desc,
        "desglose_componentes": desglose
    })

def slugify(text):
    """Convert text to a URL-friendly slug."""
    text = unidecode(text) # Transliterate unicode chars to ASCII
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text).strip('-')
    return text

def generate_urls_from_json(json_data, grade_range_slug, grade_slug):
    """Generates URLs from the site's internal JSON structure."""
    urls = []
    base_url = "https://www.curriculumnacional.cl/curriculum"
    
    custom_slugs = {
        "Artes visuales, audiovisuales y multimediales": "artes-visuales-audiovisuales-multimediales",
        "Creación y composición musical": "creacion-composicion-musical",
        "Diseño y arquitectura": "diseno-arquitectura",
        "Interpretación musical": "interpretacion-musical",
        "Interpretación y creación en danza": "interpretacion-creacion-danza",
        "Interpretación y creación en teatro": "interpretacion-creacion-teatro",
        "Biología celular y molecular": "biologia-celular-molecular",
        "Biología de los ecosistemas": "biologia-ecosistemas",
        "Ciencias de la salud": "ciencias-salud",
        "Física": "fisica",
        "Química": "quimica",
        "Ciencias del ejercicio físico y deportivo": "ciencias-ejercicio-fisico-deportivo",
        "Expresión corporal": "expresion-corporal",
        "Promoción de estilos de vida activos y saludables": "promocion-estilos-vida-activos-saludables",
        "Estética": "estetica",
        "Filosofía política": "filosofia-politica",
        "Seminario de filosofía": "seminario-filosofia",
        "Comprensión histórica del presente": "comprension-historica-presente",
        "Economía y sociedad": "economia-sociedad",
        "Geografía, territorio y desafíos socioambientales": "geografia-territorio-desafios-socioambientales",
        "Lectura y escritura especializadas": "lectura-escritura-especializadas",
        "Participación y argumentación en democracia": "participacion-argumentacion-democracia",
        "Taller de literatura": "taller-literatura",
        "Geometría 3D": "geometria-3d",
        "Límites, derivadas e integrales": "limites-derivadas-integrales",
        "Pensamiento computacional y programación": "pensamiento-computacional-programacion",
        "Probabilidades y estadística descriptiva e inferencial": "probabilidades-estadistica-descriptiva-inferencial",
        "Educación ciudadana (4M)": "educacion-ciudadana-4m",
        "Filosofía 4º medio": "filosofia-4o-medio",
        "Chile y la región latinoamericana": "chile-region-latinoamericana",
        "Inglés 4º medio": "ingles-4o-medio",
        "Lengua y literatura 4º medio": "lengua-literatura-4o-medio",
        "Matemática 4º medio": "matematica-4o-medio",
        "Ambiente y sostenibilidad": "ambiente-sostenibilidad",
        "Bienestar y salud": "bienestar-salud",
        "Seguridad, prevención y autocuidado": "seguridad-prevencion-autocuidado",
        "Tecnología y sociedad": "tecnologia-sociedad",
        "Educación física y salud 1": "educacion-fisica-salud-1",
        "Educación física y salud 2": "educacion-fisica-salud-2",
        "Religión ": "religion",
        "Especialidad Elaboración Industrial de Alimentos": "especialidad-elaboracion-industrial-alimentos",
        "Especialidad Gastronomía - Mención Pastelería y Repostería": "especialidad-gastronomia-mencion-pasteleria-reposteria",
        "Especialidad Vestuario y Confección Textil": "especialidad-vestuario-confeccion-textil",
        "Especialidad Construcción - Mención Obras Viales e Infraestructura": "especialidad-construccion-mencion-obras-viales-infraestructura",
        "Especialidad Construcción - Mención Terminaciones de la Construcción": "especialidad-construccion-mencion-terminaciones-construccion",
        "Especialidad Refrigeración y Climatización": "especialidad-refrigeracion-climatizacion",
        "Especialidad Servicios de Hotelería": "especialidad-servicios-hoteleria",
        "Especialidad Servicios de Turismo": "especialidad-servicios-turismo",
        "Especialidad Muebles y Terminaciones en Madera": "especialidad-muebles-terminaciones-madera",
        "Especialidad Tripulación de Naves Mercantes y Especiales": "especialidad-tripulacion-naves-mercantes-especiales",
        "Especialidad Mecánica de Mantenimiento de Aeronaves": "especialidad-mecanica-mantenimiento-aeronaves",
        "Especialidad Asistencia en Geología": "especialidad-asistencia-geologia",
        "Especialidad Atención de Enfermería": "especialidad-atencion-enfermeria",
        "Especialidad Atención de Enfermería - Mención Adulto Mayor": "especialidad-atencion-enfermeria-mencion-adulto",
        "Especialidad Atención de Párvulos": "especialidad-atencion-parvulos",
        "Especialidad Conectividad y Redes": "especialidad-conectividad-redes",
        "Especialidad Administración": "especialidad-administracion",
        "Especialidad Administración - Mención Logística": "especialidad-administracion-mencion-logistica",
        "Especialidad Administración - Mención Recursos Humanos": "especialidad-administracion-mencion-recursos-humanos",
        "Especialidad Contabilidad": "especialidad-contabilidad",
        "Especialidad Agropecuaria": "especialidad-agropecuaria",
        "Especialidad Agropecuaria - Mención Agricultura": "especialidad-agropecuaria-mencion-agricultura",
        "Especialidad Agropecuaria - Mención Pecuaria": "especialidad-agropecuaria-mencion-pecuaria",
        "Especialidad Agropecuaria - Mención Vitivinícola": "especialidad-agropecuaria-mencion-vitivinicola",
        "Especialidad Gastronomía": "especialidad-gastronomia",
        "Especialidad Gastronomía - Mención Cocina": "especialidad-gastronomia-mencion-cocina",
        "Especialidad Construcción": "especialidad-construccion",
        "Especialidad Construcción - Mención Edificación": "especialidad-construccion-mencion-edificacion",
        "Especialidad Instalaciones Sanitarias": "especialidad-instalaciones-sanitarias",
        "Especialidad Montaje Industrial": "especialidad-montaje-industrial",
        "Especialidad Electricidad": "especialidad-electricidad",
        "Especialidad Electrónica": "especialidad-electronica",
        "Especialidad Dibujo Técnico": "especialidad-dibujo-tecnico",
        "Especialidad Gráfica": "especialidad-grafica",
        "Especialidad Forestal": "especialidad-forestal",
        "Especialidad Acuicultura": "especialidad-acuicultura",
        "Especialidad Operaciones Portuarias": "especialidad-operaciones-portuarias",
        "Especialidad Pesquería": "especialidad-pesqueria",
        "Especialidad Construcciones Metálicas": "especialidad-construcciones-metalicas",
        "Especialidad Mecánica Automotriz": "especialidad-mecanica-automotriz",
        "Especialidad Mecánica Industrial": "especialidad-mecanica-industrial",
        "Especialidad Mecánica Industrial - Mención Mantenimiento Electromecánico": "especialidad-mecanica-industrial-mencion-mantenimiento-electromecanico",
        "Especialidad Mecánica Industrial - Mención Máquinas-Herramientas": "especialidad-mecanica-industrial-mencion-maquinas-herramientas",
        "Especialidad Mecánica Industrial - Mención Matricería": "especialidad-mecanica-industrial-mencion-matriceria",
        "Especialidad Explotación Minera": "especialidad-explotacion-minera",
        "Especialidad Metalúrgica Extractiva": "especialidad-metalurgica-extractiva",
        "Especialidad Química Industrial": "especialidad-quimica-industrial",
        "Especialidad Química Industrial - Mención Laboratorio Químico": "especialidad-quimica-industrial-mencion-laboratorio-quimico",
        "Especialidad Química Industrial - Mención Planta Química": "especialidad-quimica-industrial-mencion-planta-quimica",
        "Especialidad Atención de Enfermería - Mención Enfermería": "especialidad-atencion-enfermeria-mencion-enfermeria",
        "Especialidad Programación": "especialidad-programacion",
        "Especialidad Telecomunicaciones": "especialidad-telecomunicaciones",
    }

    for category in json_data:
        if category.get("key") == "_none":
            continue
        if "value" in category and isinstance(category["value"], list):
            for subject in category["value"]:
                subject_name = subject["value"]
                subject_slug = custom_slugs.get(subject_name, slugify(subject_name))
                url = f"{base_url}/{grade_range_slug}/{subject_slug}/{grade_slug}?priorizacion=0"
                urls.append(url)
    return urls

def generate_urls():
    """Generates the full list of curriculum URLs to scrape."""
    urls = []
    base_url = "https://www.curriculumnacional.cl/curriculum"

    # --- 1° a 6° Básico ---
    grade_range_1_6 = "1o-6o-basico"
    grades_1_6 = [f"{i}-basico" for i in range(1, 7)]
    subjects_1_6 = [
        "lenguaje-comunicacion", "matematica", "ciencias-naturales", "artes-visuales",
        "educacion-fisica-salud", "historia-geografia-ciencias-sociales", "ingles-propuesta",
        "lengua-cultura-pueblos-originarios-ancestrales", "musica", "orientacion", "religion", "tecnologia"
    ]
    for subject in subjects_1_6:
        for grade in grades_1_6:
            urls.append(f"{base_url}/{grade_range_1_6}/{subject}/{grade}")

    # --- 7° Básico a 2° Medio ---
    grade_range_7_2 = "7o-basico-2o-medio"
    grades_7_2 = ["7-basico", "8-basico", "1-medio", "2-medio"]
    subjects_7_2 = [
        "lengua-literatura", "matematica", "ciencias-naturales", "artes-visuales",
        "educacion-fisica-salud", "historia-geografia-ciencias-sociales", "ingles",
        "musica", "orientacion", "tecnologia"
    ]
    for subject in subjects_7_2:
        for grade in grades_7_2:
            urls.append(f"{base_url}/{grade_range_7_2}/{subject}/{grade}")
    
    # --- 3° Medio FG (Formación General) ---
    urls.extend([
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/artes-visuales/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/danza/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/musica/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/teatro/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/ambiente-sostenibilidad/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/bienestar-salud/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/seguridad-prevencion-autocuidado/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/tecnologia-sociedad/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/educacion-ciudadana-3m/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/educacion-fisica-salud-1/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/educacion-fisica-salud-2/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/filosofia-3m/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/filosofia-4o-medio/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/chile-region-latinoamericana/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/mundo-global/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/ingles-3o-medio/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/lengua-literatura-3o-medio/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/matematica-3o-medio/3-medio-fg?priorizacion=0",
        "https://www.curriculumnacional.cl/curriculum/3o-4o-medio/religion/3-medio-fg?priorizacion=0"
    ])

    # --- 3° Medio HC (Humanista-Científico) ---
    json_3_medio_hc = [
        {"key": "Artes", "value": [{"key": "53", "value": "Artes visuales, audiovisuales y multimediales"}, {"key": "54", "value": "Creación y composición musical"}, {"key": "55", "value": "Diseño y arquitectura"}, {"key": "58", "value": "Interpretación musical"}, {"key": "56", "value": "Interpretación y creación en danza"}, {"key": "57", "value": "Interpretación y creación en teatro"}]},
        {"key": "Ciencias", "value": [{"key": "59", "value": "Biología celular y molecular"}, {"key": "60", "value": "Biología de los ecosistemas"}, {"key": "61", "value": "Ciencias de la salud"}, {"key": "62", "value": "Física"}, {"key": "63", "value": "Química"}]},
        {"key": "Educación física y salud", "value": [{"key": "64", "value": "Ciencias del ejercicio físico y deportivo"}, {"key": "65", "value": "Expresión corporal"}, {"key": "66", "value": "Promoción de estilos de vida activos y saludables"}]},
        {"key": "Filosofía", "value": [{"key": "89", "value": "Estética"}, {"key": "90", "value": "Filosofía política"}, {"key": "91", "value": "Seminario de filosofía"}]},
        {"key": "Historia, geografía y ciencias sociales", "value": [{"key": "92", "value": "Comprensión histórica del presente"}, {"key": "93", "value": "Economía y sociedad"}, {"key": "94", "value": "Geografía, territorio y desafíos socioambientales"}]},
        {"key": "Lengua y literatura", "value": [{"key": "95", "value": "Lectura y escritura especializadas"}, {"key": "96", "value": "Participación y argumentación en democracia"}, {"key": "97", "value": "Taller de literatura"}]},
        {"key": "Matemática", "value": [{"key": "98", "value": "Geometría 3D"}, {"key": "99", "value": "Límites, derivadas e integrales"}, {"key": "100", "value": "Pensamiento computacional y programación"}, {"key": "101", "value": "Probabilidades y estadística descriptiva e inferencial"}]}
    ]
    urls.extend(generate_urls_from_json(json_3_medio_hc, "3o-4o-medio", "3-medio-hc"))

    # --- 4° Medio FG (Formación General) ---
    json_4_medio_fg = [
        {"key": "Artes", "value": [{"key": "67", "value": "Artes visuales"}, {"key": "73", "value": "Danza"}, {"key": "87", "value": "Música"}, {"key": "88", "value": "Teatro"}]},
        {"key": "Ciencias para la ciudadanía", "value": [{"key": "69", "value": "Ambiente y sostenibilidad"}, {"key": "70", "value": "Bienestar y salud"}, {"key": "71", "value": "Seguridad, prevención y autocuidado"}, {"key": "72", "value": "Tecnología y sociedad"}]},
        {"key": "Educación ciudadana", "value": [{"key": "75", "value": "Educación ciudadana (4M)"}]},
        {"key": "Educación física y salud", "value": [{"key": "76", "value": "Educación física y salud 1"}, {"key": "77", "value": "Educación física y salud 2"}]},
        {"key": "Filosofía", "value": [{"key": "79", "value": "Filosofía 4º medio"}]},
        {"key": "Historia, geografía y ciencias sociales", "value": [{"key": "68", "value": "Chile y la región latinoamericana"}, {"key": "86", "value": "Mundo global"}]},
        {"key": "Inglés", "value": [{"key": "81", "value": "Inglés 4º medio"}]},
        {"key": "Lengua y literatura", "value": [{"key": "83", "value": "Lengua y literatura 4º medio"}]},
        {"key": "Matemática", "value": [{"key": "85", "value": "Matemática 4º medio"}]},
        {"key": "Religión ", "value": [{"key": "135", "value": "Religión "}]}
    ]
    urls.extend(generate_urls_from_json(json_4_medio_fg, "3o-4o-medio", "4-medio-fg"))

    # --- 4° Medio HC (Humanista-Científico) ---
    json_4_medio_hc = [
        {"key": "Artes", "value": [{"key": "53", "value": "Artes visuales, audiovisuales y multimediales"}, {"key": "54", "value": "Creación y composición musical"}, {"key": "55", "value": "Diseño y arquitectura"}, {"key": "58", "value": "Interpretación musical"}, {"key": "56", "value": "Interpretación y creación en danza"}, {"key": "57", "value": "Interpretación y creación en teatro"}]},
        {"key": "Ciencias", "value": [{"key": "59", "value": "Biología celular y molecular"}, {"key": "60", "value": "Biología de los ecosistemas"}, {"key": "61", "value": "Ciencias de la salud"}, {"key": "62", "value": "Física"}, {"key": "63", "value": "Química"}]},
        {"key": "Educación física y salud", "value": [{"key": "64", "value": "Ciencias del ejercicio físico y deportivo"}, {"key": "65", "value": "Expresión corporal"}, {"key": "66", "value": "Promoción de estilos de vida activos y saludables"}]},
        {"key": "Filosofía", "value": [{"key": "89", "value": "Estética"}, {"key": "90", "value": "Filosofía política"}, {"key": "91", "value": "Seminario de filosofía"}]},
        {"key": "Historia, geografía y ciencias sociales", "value": [{"key": "92", "value": "Comprensión histórica del presente"}, {"key": "93", "value": "Economía y sociedad"}, {"key": "94", "value": "Geografía, territorio y desafíos socioambientales"}]},
        {"key": "Lengua y literatura", "value": [{"key": "95", "value": "Lectura y escritura especializadas"}, {"key": "96", "value": "Participación y argumentación en democracia"}, {"key": "97", "value": "Taller de literatura"}]},
        {"key": "Matemática", "value": [{"key": "98", "value": "Geometría 3D"}, {"key": "99", "value": "Límites, derivadas e integrales"}, {"key": "100", "value": "Pensamiento computacional y programación"}, {"key": "101", "value": "Probabilidades y estadística descriptiva e inferencial"}]}
    ]
    urls.extend(generate_urls_from_json(json_4_medio_hc, "3o-4o-medio", "4-medio-hc"))

    # --- 3° Medio TP (Técnico Profesional) ---
    json_3_medio_tp = [
        {"key": "Administración", "value": [{"key": "1", "value": "Especialidad Administración"}, {"key": "36", "value": "Especialidad Administración - Mención Logística"}, {"key": "37", "value": "Especialidad Administración - Mención Recursos Humanos"}, {"key": "2", "value": "Especialidad Contabilidad"}]},
        {"key": "Agropecuario", "value": [{"key": "5", "value": "Especialidad Agropecuaria"}, {"key": "40", "value": "Especialidad Agropecuaria - Mención Agricultura"}, {"key": "41", "value": "Especialidad Agropecuaria - Mención Pecuaria"}, {"key": "42", "value": "Especialidad Agropecuaria - Mención Vitivinícola"}]},
        {"key": "Alimentación", "value": [{"key": "3", "value": "Especialidad Elaboración Industrial de Alimentos"}, {"key": "4", "value": "Especialidad Gastronomía"}, {"key": "38", "value": "Especialidad Gastronomía - Mención Cocina"}, {"key": "39", "value": "Especialidad Gastronomía - Mención Pastelería y Repostería"}]},
        {"key": "Confección", "value": [{"key": "6", "value": "Especialidad Vestuario y Confección Textil"}]},
        {"key": "Construcción", "value": [{"key": "7", "value": "Especialidad Construcción"}, {"key": "43", "value": "Especialidad Construcción - Mención Edificación"}, {"key": "44", "value": "Especialidad Construcción - Mención Obras Viales e Infraestructura"}, {"key": "45", "value": "Especialidad Construcción - Mención Terminaciones de la Construcción"}, {"key": "8", "value": "Especialidad Instalaciones Sanitarias"}, {"key": "9", "value": "Especialidad Montaje Industrial"}, {"key": "10", "value": "Especialidad Refrigeración y Climatización"}]},
        {"key": "Electricidad", "value": [{"key": "11", "value": "Especialidad Electricidad"}, {"key": "12", "value": "Especialidad Electrónica"}]},
        {"key": "Gráfico", "value": [{"key": "13", "value": "Especialidad Dibujo Técnico"}, {"key": "14", "value": "Especialidad Gráfica"}]},
        {"key": "Hotelería y Turismo", "value": [{"key": "15", "value": "Especialidad Servicios de Hotelería"}, {"key": "16", "value": "Especialidad Servicios de Turismo"}]},
        {"key": "Maderero", "value": [{"key": "17", "value": "Especialidad Forestal"}, {"key": "18", "value": "Especialidad Muebles y Terminaciones en Madera"}]},
        {"key": "Marítimo", "value": [{"key": "26", "value": "Especialidad Acuicultura"}, {"key": "27", "value": "Especialidad Operaciones Portuarias"}, {"key": "28", "value": "Especialidad Pesquería"}, {"key": "29", "value": "Especialidad Tripulación de Naves Mercantes y Especiales"}]},
        {"key": "Metalmecánica", "value": [{"key": "19", "value": "Especialidad Construcciones Metálicas"}, {"key": "20", "value": "Especialidad Mecánica Automotriz"}, {"key": "22", "value": "Especialidad Mecánica de Mantenimiento de Aeronaves"}, {"key": "21", "value": "Especialidad Mecánica Industrial"}, {"key": "46", "value": "Especialidad Mecánica Industrial - Mención Mantenimiento Electromecánico"}, {"key": "47", "value": "Especialidad Mecánica Industrial - Mención Máquinas-Herramientas"}, {"key": "48", "value": "Especialidad Mecánica Industrial - Mención Matricería"}]},
        {"key": "Minero", "value": [{"key": "23", "value": "Especialidad Asistencia en Geología"}, {"key": "24", "value": "Especialidad Explotación Minera"}, {"key": "25", "value": "Especialidad Metalúrgica Extractiva"}]},
        {"key": "Química e Industria", "value": [{"key": "30", "value": "Especialidad Química Industrial"}, {"key": "49", "value": "Especialidad Química Industrial - Mención Laboratorio Químico"}, {"key": "50", "value": "Especialidad Química Industrial - Mención Planta Química"}]},
        {"key": "Salud y Educación", "value": [{"key": "31", "value": "Especialidad Atención de Enfermería"}, {"key": "51", "value": "Especialidad Atención de Enfermería - Mención Adulto Mayor"}, {"key": "52", "value": "Especialidad Atención de Enfermería - Mención Enfermería"}, {"key": "32", "value": "Especialidad Atención de Párvulos"}]},
        {"key": "Tecnología y Comunicaciones", "value": [{"key": "33", "value": "Especialidad Conectividad y Redes"}, {"key": "34", "value": "Especialidad Programación"}, {"key": "35", "value": "Especialidad Telecomunicaciones"}]}
    ]
    urls.extend(generate_urls_from_json(json_3_medio_tp, "3o-4o-medio-tecnico-profesional", "3-medio-tp"))

    # --- 4° Medio TP (Técnico Profesional) ---
    json_4_medio_tp = [
        {"key": "Administración", "value": [{"key": "1", "value": "Especialidad Administración"}, {"key": "36", "value": "Especialidad Administración - Mención Logística"}, {"key": "37", "value": "Especialidad Administración - Mención Recursos Humanos"}, {"key": "2", "value": "Especialidad Contabilidad"}]},
        {"key": "Agropecuario", "value": [{"key": "5", "value": "Especialidad Agropecuaria"}, {"key": "40", "value": "Especialidad Agropecuaria - Mención Agricultura"}, {"key": "41", "value": "Especialidad Agropecuaria - Mención Pecuaria"}, {"key": "42", "value": "Especialidad Agropecuaria - Mención Vitivinícola"}]},
        {"key": "Alimentación", "value": [{"key": "3", "value": "Especialidad Elaboración Industrial de Alimentos"}, {"key": "4", "value": "Especialidad Gastronomía"}, {"key": "38", "value": "Especialidad Gastronomía - Mención Cocina"}, {"key": "39", "value": "Especialidad Gastronomía - Mención Pastelería y Repostería"}]},
        {"key": "Confección", "value": [{"key": "6", "value": "Especialidad Vestuario y Confección Textil"}]},
        {"key": "Construcción", "value": [{"key": "7", "value": "Especialidad Construcción"}, {"key": "43", "value": "Especialidad Construcción - Mención Edificación"}, {"key": "44", "value": "Especialidad Construcción - Mención Obras Viales e Infraestructura"}, {"key": "45", "value": "Especialidad Construcción - Mención Terminaciones de la Construcción"}, {"key": "8", "value": "Especialidad Instalaciones Sanitarias"}, {"key": "9", "value": "Especialidad Montaje Industrial"}, {"key": "10", "value": "Especialidad Refrigeración y Climatización"}]},
        {"key": "Electricidad", "value": [{"key": "11", "value": "Especialidad Electricidad"}, {"key": "12", "value": "Especialidad Electrónica"}]},
        {"key": "Gráfico", "value": [{"key": "13", "value": "Especialidad Dibujo Técnico"}, {"key": "14", "value": "Especialidad Gráfica"}]},
        {"key": "Hotelería y Turismo", "value": [{"key": "15", "value": "Especialidad Servicios de Hotelería"}, {"key": "16", "value": "Especialidad Servicios de Turismo"}]},
        {"key": "Maderero", "value": [{"key": "17", "value": "Especialidad Forestal"}, {"key": "18", "value": "Especialidad Muebles y Terminaciones en Madera"}]},
        {"key": "Marítimo", "value": [{"key": "26", "value": "Especialidad Acuicultura"}, {"key": "27", "value": "Especialidad Operaciones Portuarias"}, {"key": "28", "value": "Especialidad Pesquería"}, {"key": "29", "value": "Especialidad Tripulación de Naves Mercantes y Especiales"}]},
        {"key": "Metalmecánica", "value": [{"key": "19", "value": "Especialidad Construcciones Metálicas"}, {"key": "20", "value": "Especialidad Mecánica Automotriz"}, {"key": "22", "value": "Especialidad Mecánica de Mantenimiento de Aeronaves"}, {"key": "21", "value": "Especialidad Mecánica Industrial"}, {"key": "46", "value": "Especialidad Mecánica Industrial - Mención Mantenimiento Electromecánico"}, {"key": "47", "value": "Especialidad Mecánica Industrial - Mención Máquinas-Herramientas"}, {"key": "48", "value": "Especialidad Mecánica Industrial - Mención Matricería"}]},
        {"key": "Minero", "value": [{"key": "23", "value": "Especialidad Asistencia en Geología"}, {"key": "24", "value": "Especialidad Explotación Minera"}, {"key": "25", "value": "Especialidad Metalúrgica Extractiva"}]},
        {"key": "Química e Industria", "value": [{"key": "30", "value": "Especialidad Química Industrial"}, {"key": "49", "value": "Especialidad Química Industrial - Mención Laboratorio Químico"}, {"key": "50", "value": "Especialidad Química Industrial - Mención Planta Química"}]},
        {"key": "Salud y Educación", "value": [{"key": "31", "value": "Especialidad Atención de Enfermería"}, {"key": "51", "value": "Especialidad Atención de Enfermería - Mención Adulto Mayor"}, {"key": "52", "value": "Especialidad Atención de Enfermería - Mención Enfermería"}, {"key": "32", "value": "Especialidad Atención de Párvulos"}]},
        {"key": "Tecnología y Comunicaciones", "value": [{"key": "33", "value": "Especialidad Conectividad y Redes"}, {"key": "34", "value": "Especialidad Programación"}, {"key": "35", "value": "Especialidad Telecomunicaciones"}]}
    ]
    urls.extend(generate_urls_from_json(json_4_medio_tp, "3o-4o-medio-tecnico-profesional", "4-medio-tp"))


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
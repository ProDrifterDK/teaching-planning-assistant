import json
import sys
import os
import argparse

def clean_file(filepath):
    """
    Lee un archivo JSON, elimina la clave 'habilidades' a nivel superior 
    si está vacía, y sobrescribe el archivo con el contenido limpiado.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Archivo no encontrado en la ruta: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Falla al decodificar el JSON del archivo: {filepath}")
        sys.exit(1)

    # Contadores para el resumen
    items_processed = 0
    items_cleaned = 0

    # Itera sobre cada objeto principal en la lista (cada 'asignatura_curso')
    for item in data:
        items_processed += 1
        # Revisa si 'habilidades' existe y es una lista vacía
        if 'habilidades' in item and isinstance(item['habilidades'], list) and not item['habilidades']:
            del item['habilidades']
            items_cleaned += 1
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Limpieza completada exitosamente para el archivo: {filepath}")
        print(f"Resumen: {items_processed} objetos procesados, {items_cleaned} objetos limpiados.")
    except IOError as e:
        print(f"Error: No se pudo escribir de vuelta en el archivo {filepath}: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Limpia los campos 'habilidades' vacíos del archivo JSON enriquecido.")
    parser.add_argument("file_to_clean", default="data/processed/structured_data_enriched.json", help="Ruta al archivo JSON que se va a limpiar.")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file_to_clean):
        print(f"Error: El archivo especificado no existe: {args.file_to_clean}")
        sys.exit(1)

    clean_file(args.file_to_clean)

if __name__ == "__main__":
    main()
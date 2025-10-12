# -*- coding: utf-8 -*-
import fitz
import os
import sys

def extraer_texto_estructurado(pdf_path, output_path):
    try:
        with fitz.open(pdf_path) as doc:
            texto_estructurado = ""
            for num_pagina, pagina in enumerate(doc):
                texto_estructurado += f"--- Página {num_pagina + 1} ---\n\n"
                
                bloques = pagina.get_text("blocks")
                
                bloques.sort(key=lambda b: (b[1], b[0]))
                
                for bloque in bloques:
                    if bloque[6] == 0:
                        texto_del_bloque = bloque[4]
                        texto_estructurado += texto_del_bloque.strip() + "\n\n"
            
        with open(output_path, "w", encoding="utf-8") as f_out:
            f_out.write(texto_estructurado)
            
        print(f"La extracción estructurada ha finalizado. El contenido se ha guardado en: {output_path}")

    except FileNotFoundError:
        print(f"Error: El archivo PDF no se encontró en la ruta especificada: {pdf_path}")
    except Exception as e:
        print(f"Ha ocurrido un error inesperado durante la extracción: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python extract_text.py <archivo_pdf_entrada> <archivo_markdown_salida>")
    else:
        archivo_pdf_entrada = sys.argv[1]
        archivo_markdown_salida = sys.argv[2]
        extraer_texto_estructurado(archivo_pdf_entrada, archivo_markdown_salida)
import json
from pathlib import Path
from typing import List, Dict, Any

class CurriculumService:
    def __init__(self, data_file: Path):
        self._data_file = data_file
        self._data: List[Dict[str, Any]] = self._load_data()

    def _load_data(self) -> List[Dict[str, Any]]:
        """Carga los datos desde el archivo JSON."""
        if self._data_file.is_file():
            with open(self._data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def get_all_data(self) -> List[Dict[str, Any]]:
        # Para desarrollo: recargar en cada solicitud para ver cambios al instante.
        # En producción, esto debería ser cacheado.
        return self._load_data()

    def get_niveles(self) -> Dict[str, List[str]]:
        niveles: Dict[str, List[str]] = {}
        data = self.get_all_data()
        for item in data:
            curso = item.get('curso')
            asignatura = item.get('asignatura')
            if curso and asignatura:
                if curso not in niveles:
                    niveles[curso] = []
                if asignatura not in niveles[curso]:
                    niveles[curso].append(asignatura)
        return niveles

    def get_oas_by_curso_asignatura(self, curso: str, asignatura: str) -> List[Dict[str, Any]]:
        data = self.get_all_data()
        for item in data:
            if item.get('curso') == curso and item.get('asignatura') == asignatura:
                return item.get('ejes', [])
        return []

    def find_oa_details(self, oa_code: str, curso: str | None = None) -> Dict[str, Any] | None:
        """
        Encuentra el OA completo y su contexto.
        Si se proporciona 'curso', lo usa para desambiguar OAs que existen en múltiples cursos.
        """
        data = self.get_all_data()
        found_item = None

        for item in data:
            # Si se especifica un curso, filtramos por él desde el principio.
            if curso and item.get('curso') != curso:
                continue

            for eje in item.get('ejes', []):
                for oa in eje.get('oas', []):
                    if oa.get('oa_codigo_oficial') == oa_code:
                        # Si encontramos una coincidencia, la guardamos.
                        # Si ya habíamos especificado un curso, esta es la respuesta definitiva.
                        found_item = {
                            "oa_completo": oa,
                            "contexto_asignatura": item,
                            "eje": eje
                        }
                        if curso:
                            return found_item
            
            # Si hemos iterado un 'item' (curso-asignatura) y encontramos algo
            # pero no teníamos un curso especificado, devolvemos esta primera coincidencia.
            # Esto mantiene el comportamiento original si no se envía el curso.
            if found_item and not curso:
                return found_item
                
        # Si hemos especificado un curso pero no encontramos nada, devolvemos None.
        # O si recorrimos todo y no encontramos ninguna coincidencia.
        return found_item


# --- Instancia Singleton ---
# Apuntamos al archivo correcto que el usuario está modificando.
# Usamos una ruta relativa desde la raíz del proyecto.
DATA_FILE = Path("data/processed/structured_data_enriched.json")
curriculum_service = CurriculumService(DATA_FILE)

# --- Funciones de Dependencia para FastAPI ---
def get_curriculum_service() -> CurriculumService:
    return curriculum_service

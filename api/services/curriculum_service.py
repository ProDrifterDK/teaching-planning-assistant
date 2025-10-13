import json
from pathlib import Path
from typing import List, Dict, Any

class CurriculumService:
    def __init__(self, data_file: Path):
        self._data: List[Dict[str, Any]] = []
        if data_file.is_file():
            with open(data_file, "r", encoding="utf-8") as f:
                self._data = json.load(f)

    def get_all_data(self) -> List[Dict[str, Any]]:
        return self._data

    def get_niveles(self) -> Dict[str, List[str]]:
        niveles: Dict[str, List[str]] = {}
        for item in self._data:
            curso = item.get('curso')
            asignatura = item.get('asignatura')
            if curso and asignatura:
                if curso not in niveles:
                    niveles[curso] = []
                if asignatura not in niveles[curso]:
                    niveles[curso].append(asignatura)
        return niveles

    def get_oas_by_curso_asignatura(self, curso: str, asignatura: str) -> List[Dict[str, Any]]:
        for item in self._data:
            if item.get('curso') == curso and item.get('asignatura') == asignatura:
                return item.get('ejes', [])
        return []

    def find_oa_details(self, oa_code: str) -> Dict[str, Any] | None:
        """Encuentra el OA completo y su contexto de asignatura/curso."""
        for item in self._data:
            for eje in item.get('ejes', []):
                for oa in eje.get('oas', []):
                    # Limpiamos el código para que coincida
                    codigo_limpio = oa.get('oa_codigo_oficial', '').replace("Objetivo de aprendizaje ", "")
                    if codigo_limpio == oa_code:
                        return {
                            "oa_completo": oa,
                            "contexto_asignatura": item,
                            "eje": eje
                        }
        return None


# --- Instancia Singleton ---
# Esto asegura que los datos se carguen una sola vez en memoria.
DATA_FILE = Path(__file__).parent.parent / "data/structured_data_final.json"
curriculum_service = CurriculumService(DATA_FILE)

# --- Funciones de Dependencia para FastAPI ---
def get_curriculum_service() -> CurriculumService:
    return curriculum_service

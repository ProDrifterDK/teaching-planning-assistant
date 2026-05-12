# TPA MCP Server — Deploy Guide

El server MCP ya está integrado en el repo de TPA. Se despliega como un
**segundo servicio en Railway** junto a la API existente.

## Archivos agregados al repo TPA

```
teaching-planning-assistant/
├── mcp_server.py          ← MCP server (SSE transport)
├── requirements.txt       ← + mcp>=1.0.0
└── data/processed/
    └── structured_data_enriched.json  ← ya existía
```

## Desplegar en Railway (segundo servicio)

1. Ve al dashboard de Railway → proyecto `teaching-planning-assistant`
2. **+ New Service** → **GitHub Repo** → mismo repo
3. Configura el servicio:
   - **Start Command:** `python mcp_server.py`
   - **Builder:** NIXPACKS (hereda del repo)
4. Despliega

Railway asignará una URL pública tipo:
`https://teaching-planning-assistant-production-XXXX.up.railway.app`

El endpoint SSE estará en: `https://<url>/sse`

## Conectar desde Hermes (máquina de tu pareja)

En el `~/.hermes/config.yaml` de su Hermes:

```yaml
mcp_servers:
  tpa-curriculum:
    transport: sse
    url: https://teaching-planning-assistant-production-XXXX.up.railway.app/sse
```

La URL exacta la obtienes del dashboard de Railway → servicio MCP → Domains.

## Probar localmente

```bash
cd teaching-planning-assistant
pip install mcp>=1.0.0   # si no está instalado
PORT=8001 python mcp_server.py
# → SSE en http://localhost:8001/sse
```

## Herramientas disponibles

| Tool | Uso típico |
|------|-----------|
| `search_oas` | "Busca todos los OAs de fracciones en 5° Básico" |
| `get_oa_detail` | "Dame el detalle del OA LE07 OA 03" |
| `list_courses` | "¿Qué cursos hay disponibles?" |
| `list_subjects` | "¿Qué asignaturas tiene 1° Medio?" |
| `get_curriculum_structure` | "Muéstrame todo el currículum de Matemática 5°" |
| `curriculum_stats` | "¿Cuántos OAs hay en total?" |

## Notas

- **Sin autenticación** — los datos curriculares son públicos (MINEDUC)
- **1837 OAs**, 16 cursos, 113+ asignaturas
- Lee el JSON directo del repo (no depende de la API de TPA)
- Si el JSON se actualiza (se scrapea nuevo currículum), el server lo lee al iniciar
- Para recargar sin reiniciar: `pkill -HUP -f mcp_server.py` (requiere agregar signal handler)

#!/usr/bin/env python3
"""TPA Curriculum MCP Server — Chilean National Curriculum for AI agents.

Deployed as a Railway service alongside the TPA API.
Exposes curriculum data via MCP SSE/HTTP protocol.

Transports: SSE (legacy) and Streamable HTTP
Default port: $PORT (Railway) or 8001 (local)

Data source: data/processed/structured_data_enriched.json (in-repo)

Usage:
    python mcp_server.py                        # local dev
    PORT=8001 python mcp_server.py              # custom port
"""

import os
import sys
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from starlette.applications import Starlette

# ---------------------------------------------------------------------------
# Data Layer (embedded — no external deps beyond stdlib + mcp)
# ---------------------------------------------------------------------------


def _normalize(text: str | None) -> str:
    if not text:
        return ""
    return " ".join(text.lower().split())


class CurriculumData:
    """Read-only access to Chilean curriculum JSON (1837 OAs, 16 courses)."""

    def __init__(self, data_path: Path):
        self._data: list[dict[str, Any]] = []
        self._oa_index: dict[str, dict[str, Any]] = {}
        self._load(data_path)

    def _load(self, path: Path) -> None:
        if not path.is_file():
            raise FileNotFoundError(f"Curriculum data not found at {path}")
        with open(path, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        for entry in self._data:
            curso = entry.get("curso", "")
            asignatura = entry.get("asignatura", "")
            actitudes = entry.get("actitudes", [])
            for eje in entry.get("ejes", []):
                nombre_eje = eje.get("nombre_eje", "")
                for oa in eje.get("oas", []):
                    code = oa.get("oa_codigo_oficial", "")
                    if code:
                        self._oa_index[code] = {
                            "oa": oa,
                            "curso": curso,
                            "asignatura": asignatura,
                            "eje": nombre_eje,
                            "actitudes": actitudes,
                        }

    # -- Queries --

    def get_courses(self) -> list[str]:
        cursos: set[str] = {e.get("curso", "") for e in self._data if e.get("curso")}
        return sorted(cursos)

    def get_subjects_for_course(self, course: str) -> list[str]:
        nc = _normalize(course)
        subjects: list[str] = []
        for e in self._data:
            if _normalize(e.get("curso", "")) == nc:
                a = e.get("asignatura", "")
                if a and a not in subjects:
                    subjects.append(a)
        return sorted(subjects)

    def get_all_subjects(self) -> list[str]:
        subjects: set[str] = {e.get("asignatura", "") for e in self._data if e.get("asignatura")}
        return sorted(subjects)

    def get_oa_detail(self, oa_code: str) -> dict[str, Any] | None:
        if oa_code in self._oa_index:
            return self._oa_index[oa_code]
        nc = _normalize(oa_code)
        for code, info in self._oa_index.items():
            if _normalize(code) == nc or nc in _normalize(code):
                return info
        return None

    def search_oas(
        self, query: str = "", course: str | None = None,
        subject: str | None = None, max_results: int = 15,
    ) -> list[dict[str, Any]]:
        nq = _normalize(query)
        nc = _normalize(course) if course else ""
        ns = _normalize(subject) if subject else ""
        scored: list[tuple[int, str, dict]] = []

        for code, info in self._oa_index.items():
            if nc and _normalize(info["curso"]) != nc:
                continue
            if ns and _normalize(info["asignatura"]) != ns:
                continue

            oa = info["oa"]
            if not nq:
                score = 0
            else:
                score = 0
                desc = _normalize(oa.get("descripcion_oa", ""))
                norm_code = _normalize(code)
                if nq == norm_code:
                    score += 1000
                elif nq in norm_code:
                    score += 500
                for kw in nq.split():
                    if kw in desc:
                        score += 20
                    if kw in norm_code:
                        score += 15
                    for skill in oa.get("habilidades", []):
                        if kw in _normalize(skill):
                            score += 10
                    for comp in oa.get("desglose_componentes", []):
                        if kw in _normalize(comp):
                            score += 8
                if score == 0:
                    continue

            scored.append((score, code, {
                "codigo": code,
                "descripcion": oa.get("descripcion_oa", ""),
                "curso": info["curso"],
                "asignatura": info["asignatura"],
                "eje": info["eje"],
                "habilidades": oa.get("habilidades", []),
                "desglose_componentes": oa.get("desglose_componentes", []),
            }))

        scored.sort(key=lambda x: (-x[0], x[1]))
        return [item[2] for item in scored[:max_results]]

    def get_curriculum_structure(self, course: str, subject: str) -> dict[str, Any] | None:
        nc, ns = _normalize(course), _normalize(subject)
        for e in self._data:
            if _normalize(e.get("curso", "")) == nc and _normalize(e.get("asignatura", "")) == ns:
                return {
                    "curso": e["curso"], "asignatura": e["asignatura"],
                    "actitudes": e.get("actitudes", []), "ejes": e.get("ejes", []),
                }
        return None


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("tpa-mcp")

PORT = int(os.environ.get("PORT", "8001"))
HOST = os.environ.get("HOST", "0.0.0.0")

DATA_PATH = Path(os.environ.get(
    "CURRICULUM_DATA_PATH",
    str(Path(__file__).parent / "data" / "processed" / "structured_data_enriched.json"),
))

log.info("Loading curriculum from %s", DATA_PATH)
curriculum = CurriculumData(DATA_PATH)
log.info("Loaded %s OAs across %s courses", len(curriculum._oa_index), len(curriculum.get_courses()))

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "tpa-curriculum-mcp",
    instructions="""
    Chilean National Curriculum (MINEDUC) — search OAs, browse courses/subjects,
    retrieve full curriculum structures for lesson planning and content generation.
    Covers 1° Básico through 4° Medio (1837 OAs, 16 courses, 113+ subjects).
    """,
    host=HOST,
    port=PORT,
    sse_path="/sse",
    message_path="/messages/",
    streamable_http_path="/mcp",
    json_response=True,
)


@mcp.tool()
def search_oas(query: str = "", course: str | None = None,
               subject: str | None = None, max_results: int = 15) -> str:
    """Search Chilean curriculum OAs by keyword, course, and/or subject."""
    results = curriculum.search_oas(query=query, course=course, subject=subject,
                                    max_results=min(max_results, 50))
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
def get_oa_detail(oa_code: str) -> str:
    """Get full detail for an OA (accepts short codes like LE01 OA 03)."""
    detail = curriculum.get_oa_detail(oa_code)
    if detail is None:
        return json.dumps({"error": f"OA '{oa_code}' not found"}, ensure_ascii=False)
    return json.dumps(detail, ensure_ascii=False, indent=2)


@mcp.tool()
def list_courses() -> str:
    """List all 16 courses (1° Básico to 4° Medio)."""
    return json.dumps(curriculum.get_courses(), ensure_ascii=False, indent=2)


@mcp.tool()
def list_subjects(course: str | None = None) -> str:
    """List subjects for a course, or all 113+ subjects."""
    subjects = curriculum.get_subjects_for_course(course) if course else curriculum.get_all_subjects()
    return json.dumps(subjects, ensure_ascii=False, indent=2)


@mcp.tool()
def get_curriculum_structure(course: str, subject: str) -> str:
    """Get full structure (ejes + OAs + actitudes) for a course+subject."""
    structure = curriculum.get_curriculum_structure(course, subject)
    if structure is None:
        available = curriculum.get_subjects_for_course(course)
        return json.dumps({
            "error": f"No curriculum for '{course}' / '{subject}'",
            "available_subjects_for_course": available,
        }, ensure_ascii=False, indent=2)
    return json.dumps(structure, ensure_ascii=False, indent=2)


@mcp.tool()
def curriculum_stats() -> str:
    """Statistics about the loaded curriculum data."""
    return json.dumps({
        "status": "ok",
        "total_entries": len(curriculum._data),
        "total_courses": len(curriculum.get_courses()),
        "total_subjects": len(curriculum.get_all_subjects()),
        "total_oas": len(curriculum._oa_index),
    }, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def create_app() -> Starlette:
    """Create an ASGI app exposing both MCP HTTP transports.

    Railway's edge can periodically close long-lived SSE/TLS streams. Keeping
    the legacy SSE routes preserves existing clients while `/mcp` gives modern
    clients a Streamable HTTP endpoint that does not require a permanent SSE
    connection.
    """
    sse_app = mcp.sse_app()
    streamable_app = mcp.streamable_http_app()

    @asynccontextmanager
    async def lifespan(app: Starlette):
        async with mcp.session_manager.run():
            yield

    return Starlette(
        debug=mcp.settings.debug,
        routes=[
            *sse_app.routes,
            *streamable_app.routes,
        ],
        lifespan=lifespan,
    )


if __name__ == "__main__":
    log.info(
        "TPA Curriculum MCP → SSE http://%s:%s/sse + Streamable HTTP http://%s:%s/mcp",
        HOST,
        PORT,
        HOST,
        PORT,
    )
    uvicorn.run(create_app(), host=HOST, port=PORT, log_level=mcp.settings.log_level.lower())

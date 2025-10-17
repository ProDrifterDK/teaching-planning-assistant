from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse
import pypandoc
import io
import logging
import re
from weasyprint import HTML, CSS
from tempfile import NamedTemporaryFile

from ..db import models as db_models
from ..models import User
from ..db.session import get_db
from .auth import get_current_active_user
from .pdf_styles import STYLESHEET


router = APIRouter(
    prefix="/api/v1/export",
    tags=["Export"]
)

def preprocess_markdown_for_html(markdown_text: str) -> str:
    """
    Converts GitHub-style alerts into styled HTML divs.
    Example: [!NOTE] becomes <div class="alert alert-note">...</div>
    """
    def alert_replacer(match):
        alert_type = match.group(1).lower()
        content = match.group(2).strip()
        title = alert_type.capitalize()
        return f'<div class="alert alert-{alert_type}"><p class="alert-title">{title}</p>{content}</div>'

    # Regex to find alerts like [!NOTE], [!TIP], etc.
    alert_pattern = re.compile(r'\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*)', re.IGNORECASE)
    processed_text = alert_pattern.sub(alert_replacer, markdown_text)
    
    return processed_text

@router.get("/plan/{planning_id}")
def export_planning(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    planning_id: int,
    format: str = Query(..., regex="^(pdf|docx)$")
):
    """
    Export a planning log to a specified format (PDF or DOCX).
    """
    logging.info(f"Attempting to export planning_id: {planning_id} for user_id: {current_user.id} in format: {format}")

    planning_log = db.query(db_models.PlanningLog).filter(
        db_models.PlanningLog.id == planning_id,
        db_models.PlanningLog.user_id == current_user.id
    ).first()

    if not planning_log:
        logging.warning(f"PlanningLog not found for id: {planning_id} and user_id: {current_user.id}. Access denied.")
        raise HTTPException(status_code=404, detail="Planning not found or access denied")

    logging.info(f"Successfully found PlanningLog with id: {planning_id}. Proceeding with conversion.")
    markdown_content = str(planning_log.plan_markdown)

    if not markdown_content:
        logging.error(f"Markdown content for planning_id {planning_id} is empty.")
        raise HTTPException(status_code=500, detail="Cannot export an empty planning.")

    try:
        if format == "pdf":
            media_type = "application/pdf"
            processed_markdown = preprocess_markdown_for_html(markdown_content)
            html_body = pypandoc.convert_text(processed_markdown, 'html', format='gfm')
            full_html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Planificación</title>
                <link href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap" rel="stylesheet">
            </head>
            <body>
                {html_body}
            </body>
            </html>
            """
            css = CSS(string=STYLESHEET)
            html = HTML(string=full_html)
            output_bytes = html.write_pdf(stylesheets=[css])

        else: # docx
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            with NamedTemporaryFile(delete=True, suffix=".docx") as temp_docx:
                pypandoc.convert_text(
                    markdown_content,
                    'docx',
                    format='gfm',
                    outputfile=temp_docx.name
                )
                temp_docx.seek(0)
                output_bytes = temp_docx.read()
        
        filename = f"planificacion_{planning_id}.{format}"
        
        logging.info(f"Conversion successful. Sending file: {filename}")
        return StreamingResponse(
            io.BytesIO(output_bytes),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logging.error(f"Error during document conversion for planning_id {planning_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate the document")
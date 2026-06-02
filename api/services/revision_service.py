from api.models import ContentRevisionRequest, ContentRevisionResponse
from api.core.config import settings
from api.services.ai_adapter import DeepSeekAIAdapter, ai_adapter
import json
from datetime import datetime

class RevisionService:
    """Service for revising educational content using DeepSeek"""
    
    def __init__(self, adapter: DeepSeekAIAdapter | None = None):
        self.adapter = adapter or ai_adapter
    
    async def revise_content(self, request: ContentRevisionRequest) -> ContentRevisionResponse:
        """
        Revise educational content based on teacher feedback.
        """
        start_time = datetime.utcnow()
        
        try:
            prompt = self._build_revision_prompt(request)
            
            # We want the response to match the structure of ContentRevisionResponse's revised_content.
            # Since revised_content is Dict[str, Any], we ask DeepSeek for a JSON object with
            # 'revised_content' and 'changes_summary'.
            result = await self.adapter.generate_json(
                prompt,
                max_tokens=settings.AI_MAX_OUTPUT_TOKENS,
            )
            result_data = result.data
            
            # Extract parts
            revised_content = result_data.get('revised_content')
            changes_summary = result_data.get('changes_summary')
            
            # Calculate metadata
            original_text = json.dumps(request.original_content)
            revised_text = json.dumps(revised_content)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return ContentRevisionResponse(
                success=True,
                revised_content=revised_content,
                changes_summary=changes_summary,
                revision_metadata={
                    "original_char_count": len(original_text),
                    "revised_char_count": len(revised_text),
                    "complexity_change": "revised", # Placeholder, could be more sophisticated
                    "model": result.model,
                    "tokens_input": result.usage.prompt_tokens,
                    "tokens_output": result.usage.completion_tokens,
                    "tokens_thinking": result.usage.reasoning_tokens,
                    "requested_at": start_time.isoformat(),
                    "completed_at": end_time.isoformat(),
                    "duration_ms": duration_ms
                }
            )
            
        except Exception as e:
            return ContentRevisionResponse(
                success=False,
                revised_content=None,
                changes_summary=None,
                revision_metadata={
                    "requested_at": start_time.isoformat(),
                    "error_time": datetime.utcnow().isoformat()
                },
                error=str(e)
            )

    def _build_revision_prompt(self, request: ContentRevisionRequest) -> str:
        """Build prompt for content revision"""
        
        revision_options_text = ""
        if request.revision_options.simplify_vocabulary:
            revision_options_text += "- Simplificar vocabulario para el nivel\n"
        if request.revision_options.add_examples:
            revision_options_text += "- Agregar más ejemplos explicativos\n"
        if request.revision_options.shorten_content:
            revision_options_text += "- Hacer el contenido más conciso/breve\n"
        if request.revision_options.add_accessibility:
            revision_options_text += "- Agregar características de accesibilidad (descripciones, claridad)\n"
            
        prompt = f"""
You are revising educational content for a Chilean school curriculum.

Original Content:
{json.dumps(request.original_content, indent=2)}

Teacher Feedback:
{request.feedback}

Revision Requirements:
{revision_options_text}

Grade Level: {request.grade_level}
Subject: {request.subject}

Please revise the content maintaining the same structure but applying the requested changes.

Return a JSON object with two keys:
1. "revised_content": The full content object with revisions applied (must match original structure).
2. "changes_summary": A brief text summary of what changes were made.

Example Response Structure:
{{
  "revised_content": {{ ... same structure as original ... }},
  "changes_summary": "Simplified vocabulary in questions 2 and 4, added an example to question 5."
}}
"""
        return prompt

# Singleton instance
revision_service = RevisionService()

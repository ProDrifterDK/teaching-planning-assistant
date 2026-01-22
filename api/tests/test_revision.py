import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from api.models import ContentRevisionRequest, RevisionOptions
from api.services.revision_service import RevisionService

@pytest.mark.asyncio
async def test_revise_content_success():
    # Mock the Gemini model
    mock_response = MagicMock()
    mock_response.text = '{"revised_content": {"quiz": {"questions": []}}, "changes_summary": "Simplified vocabulary"}'
    
    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    
    with patch('google.generativeai.GenerativeModel', return_value=mock_model):
        service = RevisionService()
        service.model = mock_model  # Ensure our mock is used
        
        request = ContentRevisionRequest(
            original_content={"quiz": {"questions": []}},
            content_type="quiz",
            feedback="Simplify",
            revision_options=RevisionOptions(simplify_vocabulary=True),
            grade_level="1° Básico",
            subject="Lenguaje"
        )
        
        response = await service.revise_content(request)
        
        assert response.success is True
        assert response.revised_content == {"quiz": {"questions": []}}
        assert response.changes_summary == "Simplified vocabulary"
        assert response.revision_metadata["model"] == "gemini-2.5-pro"

@pytest.mark.asyncio
async def test_revise_content_failure():
    # Mock exception
    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(side_effect=Exception("API Error"))
    
    with patch('google.generativeai.GenerativeModel', return_value=mock_model):
        service = RevisionService()
        service.model = mock_model
        
        request = ContentRevisionRequest(
            original_content={"quiz": {}},
            content_type="quiz",
            feedback="Fix",
            grade_level="1° Básico",
            subject="Lenguaje"
        )
        
        response = await service.revise_content(request)
        
        assert response.success is False
        assert response.error == "API Error"

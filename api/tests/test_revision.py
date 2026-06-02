import json

import pytest

from api.models import ContentRevisionRequest, RevisionOptions
from api.services.ai_adapter import AIJsonResult, AIUsage
from api.services.revision_service import RevisionService


class FakeAdapter:
    def __init__(self, payload=None, error=None):
        self.payload = payload or {}
        self.error = error
        self.calls = []

    async def generate_json(self, prompt, **kwargs):
        self.calls.append({"prompt": prompt, **kwargs})
        if self.error:
            raise self.error
        return AIJsonResult(
            data=self.payload,
            raw_text=json.dumps(self.payload),
            model="deepseek-v4-flash",
            usage=AIUsage(prompt_tokens=10, completion_tokens=5),
        )


@pytest.mark.asyncio
async def test_revise_content_success():
    service = RevisionService(adapter=FakeAdapter({
        "revised_content": {"quiz": {"questions": []}},
        "changes_summary": "Simplified vocabulary",
    }))

    request = ContentRevisionRequest(
        original_content={"quiz": {"questions": []}},
        content_type="quiz",
        feedback="Simplify",
        revision_options=RevisionOptions(simplify_vocabulary=True),
        grade_level="1° Básico",
        subject="Lenguaje",
    )

    response = await service.revise_content(request)

    assert response.success is True
    assert response.revised_content == {"quiz": {"questions": []}}
    assert response.changes_summary == "Simplified vocabulary"
    assert response.revision_metadata["model"] == "deepseek-v4-flash"
    assert response.revision_metadata["tokens_input"] == 10
    assert response.revision_metadata["tokens_output"] == 5


@pytest.mark.asyncio
async def test_revise_content_failure():
    service = RevisionService(adapter=FakeAdapter(error=Exception("API Error")))

    request = ContentRevisionRequest(
        original_content={"quiz": {}},
        content_type="quiz",
        feedback="Fix",
        grade_level="1° Básico",
        subject="Lenguaje",
    )

    response = await service.revise_content(request)

    assert response.success is False
    assert response.error == "API Error"

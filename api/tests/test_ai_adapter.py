import json

import pytest

from api.services.ai_adapter import AIUsage, DeepSeekAIAdapter


class FakeDeepSeekResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}: {self.text}")

    def json(self):
        return self.payload


class FakeAsyncClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    async def post(self, url, *, headers, json, timeout):
        self.calls.append({
            "url": url,
            "headers": headers,
            "json": json,
            "timeout": timeout,
        })
        return FakeDeepSeekResponse(self.payload)


@pytest.mark.asyncio
async def test_deepseek_adapter_posts_openai_compatible_json_request():
    client = FakeAsyncClient({
        "choices": [{"message": {"content": '{"ok": true}'}}],
        "usage": {
            "prompt_tokens": 11,
            "completion_tokens": 7,
            "completion_tokens_details": {"reasoning_tokens": 2},
        },
    })
    adapter = DeepSeekAIAdapter(
        api_key="test-key",
        base_url="https://api.deepseek.com/v1",
        model="deepseek-v4-flash",
        client=client,
        timeout_seconds=9,
    )

    result = await adapter.generate_json(
        "Return a JSON object for a quiz.",
        schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
    )

    assert result.data == {"ok": True}
    assert result.usage == AIUsage(prompt_tokens=11, completion_tokens=7, reasoning_tokens=2)
    call = client.calls[0]
    assert call["url"] == "https://api.deepseek.com/v1/chat/completions"
    assert call["headers"]["Authorization"] == "Bearer test-key"
    assert call["json"]["model"] == "deepseek-v4-flash"
    assert call["json"]["response_format"] == {"type": "json_object"}
    assert call["json"]["messages"][0]["role"] == "system"
    assert "json" in call["json"]["messages"][0]["content"].lower()
    assert "JSON Schema" in call["json"]["messages"][1]["content"]
    assert call["timeout"] == 9


@pytest.mark.asyncio
async def test_deepseek_adapter_raises_when_api_key_missing():
    adapter = DeepSeekAIAdapter(api_key="", client=FakeAsyncClient({}))

    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
        await adapter.generate_json("Return json")


@pytest.mark.asyncio
async def test_deepseek_adapter_parses_json_wrapped_in_markdown_fence():
    client = FakeAsyncClient({
        "choices": [{"message": {"content": "```json\n{\"ok\": true}\n```"}}],
        "usage": {},
    })
    adapter = DeepSeekAIAdapter(api_key="test-key", client=client)

    result = await adapter.generate_json("Return json")

    assert result.data == {"ok": True}


@pytest.mark.asyncio
async def test_deepseek_adapter_generate_text_omits_json_mode_and_tracks_cache_usage():
    client = FakeAsyncClient({
        "model": "deepseek-v4-flash",
        "choices": [{"message": {"content": "Plan markdown"}}],
        "usage": {
            "prompt_tokens": 20,
            "completion_tokens": 10,
            "prompt_cache_hit_tokens": 3,
            "prompt_cache_miss_tokens": 17,
        },
    })
    adapter = DeepSeekAIAdapter(api_key="test-key", client=client)

    result = await adapter.generate_text("Create a markdown lesson plan")

    assert result.text == "Plan markdown"
    assert result.usage.prompt_tokens == 20
    assert result.usage.completion_tokens == 10
    assert result.usage.prompt_cache_hit_tokens == 3
    assert result.usage.prompt_cache_miss_tokens == 17
    assert "response_format" not in client.calls[0]["json"]

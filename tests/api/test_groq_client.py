import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.api.groq_client import AsyncGroqClient


@pytest.fixture
def fake_sdk_response():
    msg = MagicMock(); msg.content = "hello"
    choice = MagicMock(); choice.message = msg
    completion = MagicMock(); completion.choices = [choice]
    completion.usage.total_tokens = 50
    return completion


@pytest.mark.asyncio
async def test_acall_returns_completion(fake_sdk_response):
    client = AsyncGroqClient(api_key="k", concurrency=4)
    with patch.object(client._sdk.chat.completions, "create",
                      AsyncMock(return_value=fake_sdk_response)):
        result = await client.acall(
            messages=[{"role": "user", "content": "hi"}],
            model="llama-3.1-8b-instant",
        )
    assert result.choices[0].message.content == "hello"
    assert result.usage.total_tokens == 50


@pytest.mark.asyncio
async def test_acall_json_mode_passes_response_format(fake_sdk_response):
    client = AsyncGroqClient(api_key="k", concurrency=4)
    create = AsyncMock(return_value=fake_sdk_response)
    with patch.object(client._sdk.chat.completions, "create", create):
        await client.acall(messages=[], model="m", json_mode=True)
    kwargs = create.call_args.kwargs
    assert kwargs["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_concurrency_semaphore_bounds_inflight():
    client = AsyncGroqClient(api_key="k", concurrency=2)
    inflight = 0
    peak = 0

    async def fake_create(**kw):
        nonlocal inflight, peak
        inflight += 1
        peak = max(peak, inflight)
        await asyncio.sleep(0.05)
        inflight -= 1
        return MagicMock(choices=[MagicMock(message=MagicMock(content=""))],
                         usage=MagicMock(total_tokens=1))

    with patch.object(client._sdk.chat.completions, "create",
                      side_effect=fake_create):
        await asyncio.gather(*[
            client.acall(messages=[], model="m") for _ in range(6)
        ])
    assert peak <= 2

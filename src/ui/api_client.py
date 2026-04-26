"""Async HTTP client wrapping the FastAPI surface. Used by the Gradio
adapter; will be replaced by the Next.js frontend in Spec 1.5.
"""
import json
from typing import Any, AsyncGenerator, Optional
import httpx


class ReasoningAPIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000",
                 http_client: Optional[httpx.AsyncClient] = None,
                 timeout_s: int = 600):
        self.base = base_url.rstrip("/")
        self._http = http_client or httpx.AsyncClient(timeout=timeout_s)
        self._owns_http = http_client is None

    async def aclose(self):
        if self._owns_http:
            await self._http.aclose()

    async def start_run(self, *, query: str, strategy: str, reasoning_model: str,
                        conversation_id: Optional[str] = None,
                        evaluator_model: Optional[str] = None,
                        knobs: Optional[dict] = None,
                        token_budget: Optional[int] = None,
                        temperature: float = 0.7,
                        max_tokens: int = 4000) -> str:
        body = {
            "query": query, "strategy": strategy,
            "reasoning_model": reasoning_model,
            "conversation_id": conversation_id,
            "evaluator_model": evaluator_model,
            "knobs": knobs or {},
            "token_budget": token_budget,
            "temperature": temperature, "max_tokens": max_tokens,
        }
        body = {k: v for k, v in body.items() if v is not None}
        r = await self._http.post(f"{self.base}/runs", json=body)
        r.raise_for_status()
        return r.json()["run_id"]

    async def get_run(self, run_id: str) -> dict:
        r = await self._http.get(f"{self.base}/runs/{run_id}")
        r.raise_for_status()
        return r.json()

    async def stream_events(self, run_id: str,
                            last_event_id: Optional[int] = None
                            ) -> AsyncGenerator[dict[str, Any], None]:
        headers = {}
        if last_event_id is not None:
            headers["Last-Event-ID"] = str(last_event_id)
        async with self._http.stream("GET", f"{self.base}/runs/{run_id}/events",
                                     headers=headers) as r:
            r.raise_for_status()
            data_buf: list[str] = []
            event_type: Optional[str] = None
            event_id: Optional[str] = None
            async for line in r.aiter_lines():
                if not line.strip():
                    if data_buf and event_type:
                        try:
                            payload = json.loads("".join(data_buf))
                        except json.JSONDecodeError:
                            payload = {"raw": "".join(data_buf)}
                        yield {"type": event_type, "id": event_id,
                               **(payload if isinstance(payload, dict) else {})}
                    data_buf, event_type, event_id = [], None, None
                    continue
                if line.startswith(":"):
                    continue
                if line.startswith("id:"):
                    event_id = line[3:].strip()
                elif line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    data_buf.append(line[5:].lstrip())

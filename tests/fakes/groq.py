"""Scripted async Groq client for tests. Returns objects shaped like the
real Groq SDK's `ChatCompletion` (only the fields our code reads).
"""
import json
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class _Usage:
    total_tokens: int = 100


@dataclass
class _Message:
    content: str


@dataclass
class _Choice:
    message: _Message


@dataclass
class FakeChatCompletion:
    choices: list[_Choice]
    usage: _Usage = field(default_factory=_Usage)


class FakeGroqClient:
    """
    `scripted` is either:
      - a list of str | dict — popped per call. dict items are returned as
        JSON strings (for JSON-mode calls).
      - a callable taking the messages list, returning str | dict.
    """
    def __init__(self, scripted):
        self.scripted = scripted
        self.calls: list[dict] = []
        self.sem = None  # strategies access .sem on real client; tests no-op

    async def acall(self, messages: list[dict], *, model: str,
                    temperature: float = 0.7, max_tokens: int = 4000,
                    json_mode: bool = False, tokens_used: int = 100) -> FakeChatCompletion:
        self.calls.append({
            "messages": messages, "model": model, "temperature": temperature,
            "max_tokens": max_tokens, "json_mode": json_mode,
        })
        if callable(self.scripted):
            nxt = self.scripted(messages)
        else:
            if not self.scripted:
                raise RuntimeError("FakeGroqClient: scripted list exhausted")
            nxt = self.scripted.pop(0)

        content = json.dumps(nxt) if isinstance(nxt, dict) else nxt
        return FakeChatCompletion(
            choices=[_Choice(message=_Message(content=content))],
            usage=_Usage(total_tokens=tokens_used),
        )

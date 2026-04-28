---
title: Advanced AI Reasoning System Pro
emoji: 🧠
colorFrom: purple
colorTo: blue
sdk: gradio
sdk_version: 5.6.0
app_file: main.py
pinned: false
license: mit
short_description: Advanced AI reasoning with multiple methodologies
tags:
  - llm
  - reasoning
  - groq
  - ai
  - research
---

# Advanced AI Reasoning System Pro

A research-focused workbench for comparing structured LLM reasoning methodologies (Tree of Thoughts, Self-Consistency, Reflexion, Multi-Agent Debate, and others) against the same problem, with full traceability, persistence, and evaluation tooling.

Final-year project. Active development. The current Gradio UI is the working baseline; a Next.js frontend and a FastAPI backend with real algorithm implementations are on the near-term roadmap (see [Roadmap](#roadmap)).

---

## Status at a glance

| Area | Today | Planned (Spec 1) |
|------|-------|------------------|
| Reasoning modes | Implemented as system prompts (single LLM call per mode) | Real orchestrated algorithms (multi-call, structured events) |
| API | Gradio in-process | FastAPI + SSE streaming, Gradio adapter on top |
| Storage | In-memory only | SQLite (`conversations`, `runs`, `events`) |
| Frontend | Gradio (4 tabs) | Gradio adapter remains; Next.js/TypeScript UI in Spec 1.5 |
| Evaluation | None | Benchmark harness in Spec 2 |
| Retrieval / Tools | None | RAG + tool use in Spec 3 |

---

## Reasoning methodologies

Seven modes are exposed today as research-aligned system prompts. Four of them will gain real algorithmic implementations in Spec 1 (marked below).

| Mode | Reference | Today | Spec 1 |
|------|-----------|-------|--------|
| Tree of Thoughts (ToT) | Yao et al., 2023 | Prompt-only | Real branching + LLM-as-judge scoring + beam pruning |
| Self-Consistency | Wang et al., 2022 | Prompt-only | Parallel sampling (N paths) + JSON-mode answer extraction + majority vote |
| Reflexion | Shinn et al., 2023 | Prompt-only | Iterative critique→refine loop with judge-driven termination |
| Multi-Agent Debate | Du et al., 2023 | Prompt-only | Two distinct agent personas + multi-round exchange + judge synthesis |
| Chain of Thought (CoT) | Wei et al., 2022 | Prompt (single call) | Unchanged — single-call by design |
| Analogical Reasoning | Yasunaga et al., 2023 | Prompt (single call) | Unchanged — single-call by design |
| Simple | — | Direct response | Unchanged |

The single-call modes (CoT, Analogical, Simple) deliberately stay simple — they form the baseline group when Spec 2's evaluation harness benchmarks the orchestrated algorithms against unstructured prompting.

---

## Quick start

### Prerequisites

- Python 3.10+
- A [Groq API key](https://console.groq.com/keys)

### Install

```bash
git clone https://github.com/<your-user>/Advanced-AI-Reasoning-System-Pro.git
cd Advanced-AI-Reasoning-System-Pro

python -m venv venv
# Windows:  venv\Scripts\activate
# Unix:     source venv/bin/activate

pip install -r requirements.txt
```

### Configure

Copy `.env.example` to `.env` and set your key:

```env
GROQ_API_KEY=gsk_...
```

### Run

```bash
python main.py
```

Open http://127.0.0.1:7860 in your browser.

---

## Project structure

```
src/
├── api/              Groq client wrapper (will gain async + JSON-mode helpers)
├── config/           Settings, constants (ReasoningMode, ModelConfig)
├── core/             Reasoning orchestrator + prompt engine + conversation state
│   └── strategies/   (Spec 1) one file per real algorithm
├── models/           Pydantic data classes (entry, metrics)
├── services/         Cache (LRU+TTL), rate limiter (token bucket),
│                     export (JSON/MD/TXT/PDF), analytics
├── storage/          (Spec 1) SQLite schema + DAOs
├── ui/               Gradio app, components, handlers, styles
└── utils/            Logger, decorators, validators, helpers

main.py               Entry point (currently launches Gradio)
docs/superpowers/     Design specs (planning artifacts)
tests/                Pytest suite
```

---

## Configuration reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `GROQ_API_KEY` | — | Required. Groq API key. |
| `CACHE_SIZE` | 100 | LRU cache entries for full-response caching. |
| `CACHE_TTL` | 3600 | Cache entry TTL (seconds). |
| `RATE_LIMIT_REQUESTS` | 50 | Token-bucket capacity. |
| `RATE_LIMIT_WINDOW` | 60 | Token-bucket refill window (seconds). |
| `MAX_RETRIES` | 3 | API retry count on transient failures. |
| `ENABLE_CACHE` | true | Toggle response caching. |
| `ENABLE_RATE_LIMITING` | true | Toggle the rate limiter. |
| `ENABLE_SELF_CRITIQUE` | true | Append a one-shot self-critique pass. |

See `src/config/settings.py` for the full list.

---

## Available models

18 Groq-hosted models are exposed via the model picker, including:

- **Meta** — `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, Llama 4 Maverick/Scout, Llama Guard 4
- **DeepSeek** — `deepseek-r1-distill-llama-70b` (reasoning-tuned)
- **Mixtral** — `mixtral-8x7b-32768` (long context)
- **Google** — `gemma2-9b-it`
- **Moonshot** — `kimi-k2-instruct-0905` (200K context)
- **OpenAI** — `gpt-oss-120b`, `gpt-oss-20b`
- **Qwen** — `qwen3-32b`
- **Groq** — `compound`, `compound-mini`

Once Spec 1 lands, models will split into two roles:
- **Reasoning model** — user-selected, used for the main thinking calls (full prose).
- **Evaluator model** — fast + JSON-capable, used for auxiliary score/extract/judge calls (e.g. `llama-3.1-8b-instant` by default).

---

## Roadmap

### Spec 1 — Real reasoning algorithms + FastAPI backend (in design)

- Refactor reasoner into a Strategy pattern; one file per algorithm in `src/core/strategies/`.
- Real implementations of ToT (branch + score + prune), Self-Consistency (sample N + vote), Reflexion (critique→refine loop), Debate (multi-agent rounds + judge).
- Hybrid I/O: free-text for main reasoning calls, JSON mode for auxiliary `Evaluator` calls (score, extract, judge). Reasoning + evaluator model separation.
- Bounded-parallel execution via asyncio + semaphore — independent branches/samples run concurrently within a process-wide concurrency cap.
- FastAPI server with structured-event SSE: `POST /runs`, `GET /runs/:id/events`, `GET /runs`, `GET /runs/:id`, `GET /models`, `GET /modes`.
- SQLite persistence (`conversations`, `runs`, `events`) so traces survive restarts and become exportable artifacts.
- Algorithm knobs (branching factor, sample count, max iterations, etc.) configurable per request via API; UI shows defaults.
- Existing Gradio UI kept working as a thin adapter that calls FastAPI internally.
- Token-budget cap per run (default 50K) with graceful partial-failure handling (drop failed branches, abort only if all fail).

### Spec 1.5 — Next.js / TypeScript frontend

- React UI consuming the FastAPI/SSE backend. Replaces Gradio.
- Live-animated tree visualization for ToT, vote-tally chart for Self-Consistency, debate transcript view for Debate, iteration timeline for Reflexion.
- Run history browser backed by the SQLite `runs` table.
- Trace export (JSON + PDF) suitable for thesis appendices.

### Spec 2 — Evaluation harness

- Curated benchmark slices (e.g. GSM8K subset, MMLU sample, custom reasoning tasks).
- Programmatic ablation runner (sweeps over algorithm knobs via the API).
- Comparative reports: accuracy vs. latency vs. token cost across modes and models.
- Result tables/charts suitable for the project report.

### Spec 3 — RAG and tool use

- Document upload + retrieval over user-supplied corpora (PDFs, code, notebooks).
- Tool calls: web search, calculator, sandboxed code execution.
- Reasoning algorithms gain tool-use awareness (a thought may invoke a tool mid-branch).

---

## Architecture (planned, post-Spec 1)

```
Client (Gradio adapter today; Next.js in Spec 1.5)
  │
  ▼  HTTP + SSE
FastAPI server
  │
  ▼
Reasoner (orchestrator)
  ├─ Strategy: ToT / Self-Consistency / Reflexion / Debate
  ├─ Evaluator (JSON-mode LLM calls: score, extract, judge)
  ├─ EventBus (fan-out → SSE subscribers + SQLite writer)
  └─ GroqClient (async + global concurrency semaphore)
        │
        ▼
   SQLite (conversations, runs, events)
```

---

## Development

### Running tests

```bash
pytest
```

### Linting / type checking

```bash
# (configure as needed for your environment)
ruff check src/
mypy src/
```

### Notes for contributors

- The current `main` reflects the Gradio baseline. Spec 1 work happens on `fix-and-improve-ui` and successor branches.
- Design specs live in `docs/superpowers/specs/` — read these before opening a PR that touches `src/core/`.

---

## License

MIT — see `LICENSE`.

---

## Acknowledgements

- **Groq** — fast LLM inference.
- **Yao et al. (2023)** — Tree of Thoughts.
- **Wang et al. (2022)** — Self-Consistency.
- **Wei et al. (2022)** — Chain of Thought.
- **Shinn et al. (2023)** — Reflexion.
- **Du et al. (2023)** — Multi-Agent Debate.
- **Yasunaga et al. (2023)** — Analogical reasoning.

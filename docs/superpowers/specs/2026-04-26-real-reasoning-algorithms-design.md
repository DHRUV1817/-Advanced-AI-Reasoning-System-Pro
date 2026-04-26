# Spec 1 — Real reasoning algorithms + FastAPI backend

**Date:** 2026-04-26
**Status:** Design (approved, awaiting implementation plan)
**Branch:** `fix/gradio-6x-compat` → `dev`
**Owners:** Dhruv Pawar (final-year project)

---

## 0. Context and goal

The current codebase exposes seven "reasoning modes" but every mode is a single LLM call with a different system prompt. There is no branching, no voting, no critique loop, no multi-agent exchange — just prompt variation. Storage is in-memory only; restart kills everything.

Spec 1 turns the four flagship modes into real orchestrated algorithms with multi-call control flow, persists every step to SQLite, and exposes the whole thing as a FastAPI service streaming structured events over SSE. The existing Gradio UI is rewritten as a thin client of that API. Spec 1.5 (separate spec) replaces Gradio with Next.js/TypeScript; this spec must not block that.

**Non-goals for Spec 1:** evaluation harness (Spec 2), RAG/tools (Spec 3), Next.js UI (Spec 1.5), authentication, multi-tenancy, distributed deploy.

**Success criteria:**

- POST `/runs` with `strategy=tot` produces a real branching tree, scored and pruned by an evaluator LLM, persisted to SQLite, with intermediate `ThoughtGenerated` / `BranchScored` / `BeamPruned` events streamed over SSE in real time.
- Same for `sc` (Self-Consistency), `reflexion`, `debate`.
- Gradio UI continues to work end-to-end via the new HTTP path with no user-visible regressions.
- A run is reproducible from the events table: replaying events yields the same `final_answer` the run row stores.

---

## 1. Architecture

```
Client (Gradio adapter today; Next.js in Spec 1.5)
  │
  ▼  HTTP + SSE
FastAPI server  (src/api/server.py)
  │
  ▼
Reasoner (orchestrator)            (src/core/reasoner.py — refactored thin)
  ├─ STRATEGY_REGISTRY → ToT / SelfConsistency / Reflexion / Debate
  ├─ Evaluator         (src/core/evaluator.py — JSON-mode LLM calls)
  ├─ EventBus          (src/core/event_bus.py — fan-out → SSE + DB writer)
  └─ GroqClient        (src/api/groq_client.py — async, semaphore-bounded)
        │
        ▼
   SQLite (conversations, runs, events)   (src/storage/)
```

**New modules:** `src/api/server.py`, `src/api/routes/`, `src/core/strategies/`, `src/core/evaluator.py`, `src/core/events.py`, `src/core/event_bus.py`, `src/storage/db.py`, `src/storage/migrations/0001_init.sql`, `src/ui/api_client.py`, `tests/fakes/groq.py`.

**Refactored:** `src/core/reasoner.py` (thin orchestrator over strategy registry), `src/api/groq_client.py` (gains async + JSON-mode helpers), `src/ui/handlers.py` (calls API client, not Reasoner directly).

**Unchanged:** `src/core/prompt_engine.py`, `src/services/{cache_service,rate_limiter,export_service,analytics_service}.py`, `src/config/`, `src/utils/`, `src/models/`.

---

## 2. Strategy abstraction

```python
# src/core/strategies/base.py

@dataclass
class StrategyConfig:
    reasoning_model: str
    evaluator_model: str | None
    temperature: float = 0.7
    max_tokens: int = 4000
    token_budget: int = 50_000
    knobs: dict = field(default_factory=dict)   # per-strategy params

@dataclass
class StrategyResult:
    final_answer: str
    confidence: float          # 0..1, derived per-algorithm (see below)
    tokens_used: int
    elapsed_s: float
    trace_summary: dict        # algo-specific (e.g. ToT: {"best_path_ids": [...]})

class ReasoningStrategy(ABC):
    name: str   # "tot" | "sc" | "reflexion" | "debate"

    def __init__(self, client: GroqClient, evaluator: Evaluator, config: StrategyConfig): ...

    @abstractmethod
    async def run(self, problem: str) -> AsyncGenerator[ReasoningEvent | StrategyResult, None]:
        """Yields events as it works, finishes by yielding a single StrategyResult."""

STRATEGY_REGISTRY: dict[str, type[ReasoningStrategy]] = {
    # Real orchestrated algorithms
    "tot": ToTStrategy, "sc": SelfConsistencyStrategy,
    "reflexion": ReflexionStrategy, "debate": DebateStrategy,
    # Single-call modes wrapped as trivial strategies (one LLM call → FinalAnswer)
    # Keeps /runs and SSE uniform; lets the eval harness in Spec 2 benchmark them
    # against the orchestrated ones with no special-casing.
    "cot": CoTStrategy, "analogical": AnalogicalStrategy, "simple": SimpleStrategy,
}
```

**Reasoner.run():**

```python
async def run(self, run_id: str, problem: str, strategy_name: str, config: StrategyConfig):
    strat = STRATEGY_REGISTRY[strategy_name](self.client, self.evaluator, config)
    await self.bus.publish(run_id, RunStarted(payload={
        "strategy": strategy_name, "model": config.reasoning_model,
        "evaluator_model": config.evaluator_model, "knobs": config.knobs,
    }))
    try:
        async for item in strat.run(problem):
            if isinstance(item, StrategyResult):
                await self.store.complete_run(run_id, item)
                await self.bus.publish(run_id, RunCompleted(payload={"result": item.dict()}))
            else:
                await self.bus.publish(run_id, item)   # bus persists then fans out
    except Exception as e:
        await self.store.fail_run(run_id, str(e))
        await self.bus.publish(run_id, RunFailed(payload={"error": str(e)}))
        raise
```

**Confidence derivation per algorithm** (replaces the current hardcoded 95.0):

| Strategy | `confidence` source |
|----------|--------------------|
| ToT | best beam node's normalized evaluator score |
| SC | winning vote share (count / n_samples) |
| Reflexion | final judge score |
| Debate | judge's stated confidence |

**Why plain async generators (not LangGraph):** the four control flows are simple enough that an explicit `async for` reads cleaner than a graph DSL, and we avoid an extra dependency that adds nothing for the project scope.

---

## 3. Per-algorithm control flow

### 3a. Tree of Thoughts (ToT)

**Knobs (defaults):**

| Knob | Default | Purpose |
|------|---------|---------|
| `branching_factor` | 3 | thoughts generated per node |
| `max_depth` | 3 | tree depth before forced terminate |
| `beam_width` | 2 | top-K nodes kept after each level |
| `score_threshold` | 0.7 | early-stop if any node ≥ this |

**Loop:**

```
root = Node(thought="<problem framing>", depth=0, score=1.0)
frontier = [root]

for depth in 1..max_depth:
    children = []
    # parallel: expand each frontier node
    async for node in frontier:
        thoughts = await reasoning_llm.generate_thoughts(
            problem, node.path, n=branching_factor
        )                                              # 1 LLM call/node
        for t in thoughts:
            child = Node(thought=t, parent=node, depth=depth)
            children.append(child)
            yield ThoughtGenerated(node_id=child.id, parent=node.id, text=t)

    # parallel: score all children via evaluator (JSON mode)
    scores = await asyncio.gather(*[
        evaluator.score_thought(problem, c.path) for c in children
    ])                                                 # 1 eval call/child
    for c, s in zip(children, scores):
        c.score = s.value
        yield BranchScored(node_id=c.id, score=s.value, rationale=s.why)

    frontier = sorted(children, key=lambda n: n.score, reverse=True)[:beam_width]
    yield BeamPruned(kept=[n.id for n in frontier], depth=depth)

    if frontier[0].score >= score_threshold:
        break

best = frontier[0]
final = await reasoning_llm.synthesize(problem, best.path)   # 1 LLM call
yield FinalAnswer(text=final, path=[n.id for n in best.path])
```

**Worst-case calls:** depth 1 expands the root (1 node × `branching_factor`); depths 2..max_depth expand the beam (`beam_width × branching_factor` per level). With defaults: depth 1 = 3, depths 2–3 = 6 each → 15 thought-gen + 15 evaluator + 1 synthesis = **31 calls**.
**Confidence:** `best.score`.
**Partial-failure:** drop failed branch + log `BranchFailed`. Abort only if frontier empties.
**Evaluator JSON contract:** `{"value": 0.0-1.0, "why": "<one sentence>"}`.

### 3b. Self-Consistency (SC)

**Knobs:**

| Knob | Default | Purpose |
|------|---------|---------|
| `n_samples` | 5 | parallel reasoning paths |
| `sample_temperature` | 0.9 | overrides `StrategyConfig.temperature` for the N samples (high diversity) |
| `agreement_threshold` | 0.6 | early-confidence flag |

**Loop:**

```
samples = await asyncio.gather(*[
    reasoning_llm.cot_sample(problem, temperature=temp)
    for _ in range(n_samples)
])                                                    # N LLM calls
for i, s in enumerate(samples):
    yield SampleGenerated(sample_id=i, text=s)

extracted = await asyncio.gather(*[
    evaluator.extract_answer(problem, s) for s in samples
])                                                    # N eval calls
for i, e in enumerate(extracted):
    yield AnswerExtracted(sample_id=i, answer=e.answer, normalized=e.canonical)

tally = Counter(e.canonical for e in extracted)
winner, count = tally.most_common(1)[0]
share = count / n_samples
yield VoteTallied(tally=dict(tally), winner=winner, share=share)

representative = next(s for s, e in zip(samples, extracted) if e.canonical == winner)
yield FinalAnswer(text=representative, vote_share=share)
```

**Worst-case calls:** `2 × n_samples = 10`. All parallel.
**Confidence:** `share`.
**Partial-failure:** drop failed sample + log `SampleFailed`. Abort if <2 samples survive.
**Evaluator JSON contract:** `{"answer": "<extracted>", "canonical": "<normalized>"}`. `canonical` collapses "42" / "42.0" / "forty-two" for voting.

### 3c. Reflexion

**Knobs:**

| Knob | Default | Purpose |
|------|---------|---------|
| `max_iterations` | 3 | hard cap on critique→refine cycles |
| `quality_threshold` | 0.85 | judge score that ends loop early |
| `min_improvement` | 0.05 | stop if iter improves < this |

**Loop:**

```
attempt = await reasoning_llm.solve(problem)            # 1 LLM call
yield AttemptGenerated(iter=0, text=attempt)

prev_score = 0.0
for it in 1..max_iterations:
    judged = await evaluator.judge(problem, attempt)    # 1 eval call
    yield AttemptJudged(iter=it-1, score=judged.score, issues=judged.issues)

    if judged.score >= quality_threshold:
        yield TerminatedEarly(reason="threshold", score=judged.score)
        break
    if judged.score - prev_score < min_improvement and it > 1:
        yield TerminatedEarly(reason="plateau", score=judged.score)
        break

    critique = await reasoning_llm.critique(problem, attempt, judged.issues)  # 1 LLM call
    yield CritiqueGenerated(iter=it, text=critique)

    attempt = await reasoning_llm.refine(problem, attempt, critique)          # 1 LLM call
    yield AttemptGenerated(iter=it, text=attempt)

    prev_score = judged.score

yield FinalAnswer(text=attempt, final_score=prev_score, iterations=it)
```

**Worst-case calls:** `1 + 3 × max_iterations = 10`. Sequential — each iter depends on prior.
**Confidence:** final `judged.score`.
**Partial-failure:** critique/refine failure → return last good attempt + log `IterationFailed`. Initial-solve failure aborts.
**Evaluator JSON contract:** `{"score": 0.0-1.0, "issues": ["<issue 1>", ...]}`. Concrete issues drive better refinement than a bare score.

### 3d. Multi-Agent Debate

**Knobs:**

| Knob | Default | Purpose |
|------|---------|---------|
| `personas` | `["Analyst","Skeptic"]` | distinct system prompts; `n_agents = len(personas)` |
| `n_rounds` | 3 | exchange rounds |

**Loop:**

```
transcripts = {a: [] for a in personas}
opening = await asyncio.gather(*[
    reasoning_llm.debate_open(problem, persona=p) for p in personas
])                                                    # n_agents calls
for p, msg in zip(personas, opening):
    transcripts[p].append(msg)
    yield AgentSpoke(round=1, agent=p, text=msg)

for r in 2..n_rounds:
    others_view = {
        p: [transcripts[other][-1] for other in personas if other != p]
        for p in personas
    }
    responses = await asyncio.gather(*[
        reasoning_llm.debate_respond(problem, persona=p,
                                     own_history=transcripts[p],
                                     others_last=others_view[p])
        for p in personas
    ])                                                # n_agents calls/round
    for p, msg in zip(personas, responses):
        transcripts[p].append(msg)
        yield AgentSpoke(round=r, agent=p, text=msg)

verdict = await evaluator.judge_debate(problem, transcripts)   # 1 eval call
yield JudgeVerdict(winner=verdict.winner, confidence=verdict.confidence,
                   rationale=verdict.rationale)
yield FinalAnswer(text=verdict.synthesis, confidence=verdict.confidence)
```

**Worst-case calls:** `n_agents × n_rounds + 1 = 7`. Within-round parallel; cross-round sequential.
**Confidence:** `verdict.confidence`.
**Partial-failure:** one agent fails in a round → other's message stands + log `AgentFailed`. Both fail same round = abort.
**Evaluator JSON contract:**
```json
{"winner": "Analyst|Skeptic|consensus",
 "confidence": 0.0-1.0,
 "rationale": "<paragraph>",
 "synthesis": "<final answer>"}
```
`synthesis` is what the user sees — the judge writes the final, doesn't just pick a side.

---

## 4. Event schema and SSE wire format

### Pydantic envelope

```python
class ReasoningEvent(BaseModel):
    event_id: str          # uuid4
    run_id: str
    type: str              # discriminator
    ts: float              # unix epoch
    payload: dict          # type-specific

class StrategyResult(BaseModel):
    run_id: str
    final_answer: str
    confidence: float
    tokens_used: int
    elapsed_s: float
    trace_summary: dict
```

### Event types

| `type` | Algo | Payload |
|--------|------|---------|
| `RunStarted` | all | `{strategy, model, evaluator_model, knobs}` |
| `RunCompleted` | all | `{result: StrategyResult}` |
| `RunFailed` | all | `{error, partial_result?}` |
| `TokenBudgetExceeded` | all | `{tokens_used, budget}` |
| `ThoughtGenerated` | ToT | `{node_id, parent_id, depth, text}` |
| `BranchScored` | ToT | `{node_id, score, rationale}` |
| `BeamPruned` | ToT | `{depth, kept: [node_id]}` |
| `BranchFailed` | ToT | `{node_id, error}` |
| `SampleGenerated` | SC | `{sample_id, text}` |
| `AnswerExtracted` | SC | `{sample_id, answer, canonical}` |
| `VoteTallied` | SC | `{tally, winner, share}` |
| `SampleFailed` | SC | `{sample_id, error}` |
| `AttemptGenerated` | Reflexion | `{iter, text}` |
| `AttemptJudged` | Reflexion | `{iter, score, issues}` |
| `CritiqueGenerated` | Reflexion | `{iter, text}` |
| `IterationFailed` | Reflexion | `{iter, error}` |
| `TerminatedEarly` | Reflexion | `{reason, score}` |
| `AgentSpoke` | Debate | `{round, agent, text}` |
| `AgentFailed` | Debate | `{round, agent, error}` |
| `JudgeVerdict` | Debate | `{winner, confidence, rationale}` |
| `FinalAnswer` | all | `{text, confidence, ...algo extras}` |

### SSE wire format

`GET /runs/:id/events` → `text/event-stream`:

```
id: <seq>
event: <type>
data: <full JSON envelope (includes event_id uuid + seq integer)>

```

The SSE `id:` line carries the per-run monotonic `seq` (integer) so `Last-Event-ID` replay maps directly to a SQLite range query (`WHERE run_id=? AND seq > ?`). The `event_id` (uuid) stays inside the JSON envelope for client-side dedup across reconnects.

- **Reconnection:** `Last-Event-ID: <seq>` → server replays from SQLite (events persist before fan-out, so no loss).
- **Terminal events:** `RunCompleted` / `RunFailed` close the stream. Clients use these to stop reading.
- **Heartbeat:** comment line `: ping\n\n` every 15s when idle — keeps proxies alive.

---

## 5. SQLite schema

```sql
CREATE TABLE conversations (
    id          TEXT PRIMARY KEY,        -- uuid4
    created_at  REAL NOT NULL,
    title       TEXT,
    metadata    TEXT
);

CREATE TABLE runs (
    id                TEXT PRIMARY KEY,
    conversation_id   TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    created_at        REAL NOT NULL,
    completed_at      REAL,
    status            TEXT NOT NULL,     -- 'running'|'completed'|'failed'|'aborted'
    strategy          TEXT NOT NULL,
    reasoning_model   TEXT NOT NULL,
    evaluator_model   TEXT,
    query             TEXT NOT NULL,
    knobs             TEXT NOT NULL,     -- JSON
    final_answer      TEXT,
    confidence        REAL,
    tokens_used       INTEGER DEFAULT 0,
    elapsed_s         REAL,
    error             TEXT
);

CREATE TABLE events (
    id           TEXT PRIMARY KEY,
    run_id       TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    seq          INTEGER NOT NULL,        -- monotonic per-run, for ordering and SSE replay
    ts           REAL NOT NULL,
    type         TEXT NOT NULL,
    payload      TEXT NOT NULL,           -- JSON
    UNIQUE(run_id, seq)
);

CREATE INDEX idx_runs_conv ON runs(conversation_id, created_at DESC);
CREATE INDEX idx_runs_status ON runs(status);
CREATE INDEX idx_events_run_seq ON events(run_id, seq);
```

**Pragmas (on connection open):**

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA foreign_keys=ON;
PRAGMA busy_timeout=5000;
```

**Write path:** insert `runs` row on `POST /runs` → for each strategy event, EventBus assigns `seq`, INSERTs into `events`, then fans out to SSE subscribers (durability before delivery) → on terminal event, UPDATE `runs` (status, final_answer, confidence, tokens, elapsed, completed_at).

**Read path:** `GET /runs/:id` → row from `runs`. `GET /runs?conversation_id=...` → paged by `created_at DESC`. `GET /runs/:id/events` → if completed, dump rows; if running, dump rows with `seq > Last-Event-ID` then attach to live bus.

**File location:** `./data/reasoning.db` (gitignored). Configurable via `AppConfig.DB_PATH`.

**Migrations:** plain numbered SQL files in `src/storage/migrations/`, applied in order on startup if the migration's row is missing from a `schema_version` table. No Alembic — solo project, overkill.

---

## 6. FastAPI endpoint surface

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/runs` | Start a run. Returns `{run_id, status:"running"}` immediately. |
| `GET`  | `/runs/:id` | Run row (status, final_answer, confidence, tokens, elapsed). |
| `GET`  | `/runs/:id/events` | SSE stream. Replays from SQLite if `Last-Event-ID` set. |
| `DELETE` | `/runs/:id` | Cancel a running run (sets cancel flag; in-flight LLM calls finish). |
| `GET`  | `/runs` | List runs. Filters: `conversation_id`, `status`, `strategy`. Paged. |
| `POST` | `/conversations` | Create conversation. Returns `{id}`. |
| `GET`  | `/conversations` | List conversations. |
| `GET`  | `/models` | Static list of 18 Groq models with capabilities. |
| `GET`  | `/modes` | Static list of 7 strategies with default knobs. |
| `GET`  | `/health` | Liveness + DB ping. |

**`POST /runs` body:**

```json
{
  "conversation_id": "c_abc",
  "query": "...",
  "strategy": "tot",
  "reasoning_model": "llama-3.3-70b-versatile",
  "evaluator_model": "llama-3.1-8b-instant",
  "knobs": {"branching_factor": 3, "max_depth": 3},
  "token_budget": 50000
}
```

`conversation_id`, `evaluator_model`, `knobs`, `token_budget` all optional. Strategy defaults fill missing knobs. Evaluator model defaults to a fast JSON-capable model (`llama-3.1-8b-instant`).

**Errors:** plain HTTP status + `{"error": "...", "code": "..."}`. Codes: `INVALID_STRATEGY`, `INVALID_MODEL`, `RATE_LIMITED`, `BUDGET_EXCEEDED`, `RUN_NOT_FOUND`. No RFC 7807 — overkill for project scope.

**Auth:** none in Spec 1. Localhost-only by default (`127.0.0.1` bind). API key middleware lands in Spec 1.5 alongside Next.js.

**Layout:**

```
src/api/
├── server.py        FastAPI app + lifespan (open DB, start EventBus)
├── routes/
│   ├── runs.py
│   ├── conversations.py
│   └── meta.py      /models, /modes, /health
└── schemas.py       Pydantic request/response models
```

---

## 7. Concurrency and error handling

### Two distinct global limits

| Limit | Default | Bounds |
|-------|---------|--------|
| `RATE_LIMIT_REQUESTS` (token bucket) | 50/60s | calls/sec to Groq |
| `LLM_CONCURRENCY` (asyncio.Semaphore) | 8 | simultaneous in-flight LLM calls |

Wired into `GroqClient.acall()`:

```python
async def acall(self, ...):
    self.rate_limiter.acquire()
    async with self.sem:
        return await self._raw_acall(...)
```

Strategies fire `asyncio.gather(...)` freely — semaphore throttles transparently.

### Token budget

Per-run hard cap (default 50k, override via `POST /runs.token_budget`). Each LLM call returns `usage.total_tokens`; Reasoner accumulates into `run.tokens_used`. Before each new call: `if tokens_used + estimated_max > budget: raise BudgetExceeded`. Strategy catches → emits `TokenBudgetExceeded` → returns best-so-far as partial result, status `completed` with confidence flagged.

### Error taxonomy

| Where | Error | Behavior |
|-------|-------|----------|
| Single LLM call | network/timeout | retry 3× with exp backoff (existing `handle_groq_errors` decorator) |
| Single LLM call | 429 from Groq | retry honoring `Retry-After` |
| Single LLM call | other 4xx/5xx | bubble up, kill that call only |
| Branch/sample/agent | call exhausted retries | log + emit `*Failed`, drop unit, continue |
| Whole run | all units failed | abort, status `failed`, error in run row |
| Whole run | budget exceeded | partial result, status `completed` |
| Server | DB write fails | log critical, kill run, status `failed` |

### Cancellation

`DELETE /runs/:id` sets a cancel flag. Strategy checks the flag between awaits; on True, raises `CancelledError`, status `aborted`. In-flight LLM calls finish (Groq doesn't support clean stream cancel).

### Timeouts

| Scope | Default |
|-------|---------|
| Single LLM call | 60s |
| Whole run | 10 min hard cap (same path as cancellation) |

---

## 8. Gradio → FastAPI migration

Gradio becomes a thin client of the FastAPI backend during Spec 1. Spec 1.5 deletes `src/ui/` entirely.

### Adapter

`src/ui/api_client.py`:

```python
class ReasoningAPIClient:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base = base_url
        self.http = httpx.AsyncClient(timeout=600)

    async def start_run(self, query, strategy, model, **knobs) -> str:
        r = await self.http.post(f"{self.base}/runs", json={...})
        return r.json()["run_id"]

    async def stream_events(self, run_id) -> AsyncGenerator[ReasoningEvent, None]:
        async with self.http.stream("GET", f"{self.base}/runs/{run_id}/events") as r:
            async for line in r.aiter_lines():
                if line.startswith("data: "):
                    yield ReasoningEvent.model_validate_json(line[6:])

    async def get_run(self, run_id) -> dict: ...
```

### Handler rewrite

`src/ui/handlers.py.generate_response_handler` currently calls `reasoner.generate_response(...)`. Becomes:

```python
async def generate_response_handler(query, model, strategy, ...):
    run_id = await client.start_run(query, strategy, model, ...)
    accumulated = ""
    async for evt in client.stream_events(run_id):
        if evt.type == "FinalAnswer":
            yield evt.payload["text"]
            return
        if evt.type in ("ThoughtGenerated", "AgentSpoke", "AttemptGenerated"):
            accumulated += render_event_inline(evt)
            yield accumulated
        if evt.type == "RunFailed":
            yield f"❌ {evt.payload['error']}"
            return
```

Live trace shown inline (markdown italics) — a poor man's preview of what Next.js will render properly. Good enough for the transition window.

### Process model

| Mode | Command | When |
|------|---------|------|
| All-in-one | `python main.py` | dev / HF Spaces — Gradio process spawns FastAPI in same event loop via `uvicorn.Config + Server.serve()` as a background task |
| Split | `uvicorn src.api.server:app` then `python main.py --no-backend` | when running Next.js dev server alongside |

`main.py` gains a `--no-backend` flag. Default = all-in-one (preserves current `python main.py` UX, important for HF Spaces deploy).

### Migration order in code

1. Build FastAPI server + strategies + DB. `uvicorn` works standalone, testable via curl.
2. Build `ReasoningAPIClient`.
3. Rewrite `handlers.py` to use client.
4. Wire all-in-one launcher in `main.py`.
5. Remove old `Reasoner.generate_response` direct usage from handlers (Reasoner stays — it's now driven by `/runs`).

Each step ships behind passing tests, no UI break in between.

### Unchanged in `src/ui/`

`app.py` (layout), `components.py`, `styles.py`, conversation export buttons (point export at `GET /runs/:id` instead of in-memory). Theme/css fixes from this branch carry through.

---

## 9. Testing strategy

| Layer | Tool | What it covers | Live LLM? |
|-------|------|----------------|-----------|
| Unit | pytest | Pure logic: vote tally, beam pruning, JSON contract parsing, budget accounting, cache key gen | No |
| Strategy | pytest + fake `GroqClient` | Each strategy's control flow with scripted LLM responses | No |
| API | pytest + httpx | FastAPI endpoints, SSE event ordering, persistence, replay via `Last-Event-ID` | No |
| Smoke | pytest, marked `@live` | One run per strategy against real Groq, asserts non-empty answer + budget respected | Yes — opt-in |

### Fake GroqClient

`tests/fakes/groq.py`:

```python
class FakeGroqClient:
    def __init__(self, scripted: list[str | dict] | Callable):
        self.calls = []
        self.scripted = scripted

    async def acall(self, messages, **kw):
        self.calls.append({"messages": messages, **kw})
        nxt = self.scripted.pop(0) if isinstance(self.scripted, list) else self.scripted(messages)
        if isinstance(nxt, dict):  # JSON-mode call
            return ChatCompletion(content=json.dumps(nxt), usage=Usage(total_tokens=50))
        return ChatCompletion(content=nxt, usage=Usage(total_tokens=100))
```

Scripted lists per test = deterministic, fast, no network.

### Strategy test shape (ToT example)

```python
async def test_tot_prunes_to_beam_width():
    fake = FakeGroqClient([
        "thought-A", "thought-B", "thought-C",
        {"value": 0.9, "why": ""}, {"value": 0.4, "why": ""}, {"value": 0.7, "why": ""},
        # depth 2 expansions from kept beam (A, C — beam_width=2) ...
    ])
    strat = ToTStrategy(client=fake, evaluator=Evaluator(fake))
    events = [e async for e in strat.run(...)]

    pruned = [e for e in events if e.type == "BeamPruned"]
    assert len(pruned[0].payload["kept"]) == 2
```

### API test shape

```python
async def test_sse_replay_from_last_event_id(client, db):
    run_id = await seed_completed_run(db, n_events=5)
    r = await client.get(f"/runs/{run_id}/events", headers={"Last-Event-ID": "2"})
    events = parse_sse(r.text)
    assert [e.seq for e in events] == [3, 4, 5]
```

### Out of scope

- Groq's actual responses (their problem).
- Gradio UI (manual smoke when launching `python main.py`).
- Performance / load (Spec 2 evaluation harness covers throughput).

### Coverage

70% line coverage on `src/core/strategies/`, `src/core/evaluator.py`, `src/api/`, `src/storage/`. No gate elsewhere.

### CI

Single GitHub Actions job: `pytest -m "not live"`. Live tests run manually before each tagged release with `GROQ_API_KEY` from secrets.

---

## 10. Open questions (to revisit before implementation plan)

- Should `evaluator_model` default differ per strategy, or one global default? (Currently: one global default = `llama-3.1-8b-instant`.)
- Cancellation granularity — are we OK letting in-flight LLM calls complete after `DELETE /runs/:id`? Alternative: `httpx` request `cancel()` mid-stream. Decision: accept the simpler path for Spec 1; revisit if smoke testing shows problematic latency.
- HF Spaces deploy path — does the all-in-one mode survive their resource limits with SQLite + uvicorn + Gradio in one process? Verify before merging Spec 1 to `main`.

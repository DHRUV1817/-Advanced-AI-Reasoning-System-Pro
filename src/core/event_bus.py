"""Per-run event bus: persists each event to SQLite, then fans out to
in-memory asyncio.Queue subscribers. Durability before delivery so SSE
reconnect via Last-Event-ID can replay losslessly from the events table.
"""
import asyncio
import json
import sqlite3
from collections import defaultdict
from src.core.events import ReasoningEvent


class EventBus:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._subs: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._next_seq: dict[str, int] = {}
        self._lock = asyncio.Lock()

    def _seq_for(self, run_id: str) -> int:
        if run_id not in self._next_seq:
            row = self.conn.execute(
                "SELECT COALESCE(MAX(seq), 0) FROM events WHERE run_id=?",
                (run_id,),
            ).fetchone()
            self._next_seq[run_id] = (row[0] or 0) + 1
        seq = self._next_seq[run_id]
        self._next_seq[run_id] = seq + 1
        return seq

    async def publish(self, run_id: str, event: ReasoningEvent) -> None:
        async with self._lock:
            seq = self._seq_for(run_id)
            self.conn.execute(
                "INSERT INTO events (id, run_id, seq, ts, type, payload) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (event.event_id, run_id, seq, event.ts, event.type,
                 json.dumps(event.payload)),
            )
            # Stash seq on the event object for SSE writer (transient attribute)
            event.__dict__["seq"] = seq

        for q in list(self._subs.get(run_id, [])):
            q.put_nowait(event)

    def subscribe(self, run_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subs[run_id].append(q)
        return q

    def unsubscribe(self, run_id: str, queue: asyncio.Queue) -> None:
        if run_id in self._subs and queue in self._subs[run_id]:
            self._subs[run_id].remove(queue)
            if not self._subs[run_id]:
                del self._subs[run_id]

    def replay(self, run_id: str, after_seq: int = 0) -> list[dict]:
        """Read persisted events from SQLite for SSE replay."""
        rows = self.conn.execute(
            "SELECT id, seq, ts, type, payload FROM events "
            "WHERE run_id=? AND seq > ? ORDER BY seq",
            (run_id, after_seq),
        ).fetchall()
        out = []
        for r in rows:
            payload = json.loads(r["payload"])
            out.append({
                "event_id": r["id"], "seq": r["seq"], "ts": r["ts"],
                "type": r["type"], "payload": payload, "run_id": run_id,
            })
        return out

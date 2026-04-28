"""
Event handlers for UI interactions
"""
from typing import Tuple, Optional
from pathlib import Path
import gradio as gr
from src.core.reasoner import AdvancedReasoner
from src.config.constants import ReasoningMode
from src.config.settings import AppConfig
from src.utils.logger import logger
from src.ui.components import UIComponents
from src.ui.api_client import ReasoningAPIClient

# ---------------------------------------------------------------------------
# Legacy mode name → new strategy id mapping
# Handles both enum keys (snake_case) and display-string values.
# ReasoningMode enum values:
#   TREE_OF_THOUGHTS  = "Tree of Thoughts (ToT)"
#   CHAIN_OF_THOUGHT  = "Chain of Thought (CoT)"
#   SELF_CONSISTENCY  = "Self-Consistency Sampling"
#   REFLEXION         = "Reflexion + Self-Correction"
#   DEBATE            = "Multi-Agent Debate"
#   ANALOGICAL        = "Analogical Reasoning"
#   SIMPLE            = "Simple (Direct Response)"
# ---------------------------------------------------------------------------
_LEGACY_MODE_TO_STRATEGY: dict[str, str] = {
    # enum name (lower-snake) → strategy
    "tree_of_thoughts": "tot",
    "chain_of_thought": "cot",
    "self_consistency": "sc",
    "reflexion": "reflexion",
    "debate": "debate",
    "multi_agent_debate": "debate",
    "analogical": "analogical",
    "analogical_reasoning": "analogical",
    "simple": "simple",
    # display strings (lower) → strategy
    "tree of thoughts (tot)": "tot",
    "chain of thought (cot)": "cot",
    "self-consistency sampling": "sc",
    "reflexion + self-correction": "reflexion",
    "multi-agent debate": "debate",
    "analogical reasoning": "analogical",
    "simple (direct response)": "simple",
}


def _mode_to_strategy(mode) -> str:
    """Convert a ReasoningMode enum or display string to a strategy id."""
    if isinstance(mode, ReasoningMode):
        # Try enum name first (e.g. TREE_OF_THOUGHTS → tree_of_thoughts)
        key = mode.name.lower()
        if key in _LEGACY_MODE_TO_STRATEGY:
            return _LEGACY_MODE_TO_STRATEGY[key]
        # Fallback to display value
        key = mode.value.lower()
    else:
        key = str(mode).lower()
    return _LEGACY_MODE_TO_STRATEGY.get(key, "simple")


def _render_event_inline(evt: dict) -> str:
    """Return a markdown snippet for intermediate streaming events. Full text
    is shown (not truncated) so users see the complete reasoning trace."""
    t = evt.get("type", "")
    payload = evt.get("payload", {})
    if t == "ThoughtGenerated":
        return f"\n\n> 💭 **Thought (depth {payload.get('depth', '?')}):** {payload.get('text', '')}"
    if t == "BranchScored":
        return f"\n\n> ⭐ **Score {payload.get('score', 0):.2f}** — {payload.get('rationale', '')}"
    if t == "BeamPruned":
        return f"\n\n> ✂️ Pruned to top {len(payload.get('kept', []))} branches at depth {payload.get('depth', '?')}"
    if t == "SampleGenerated":
        return f"\n\n> 🎲 **Sample #{payload.get('sample_id', '?')}:**\n> \n> {payload.get('text', '')}"
    if t == "AnswerExtracted":
        return f"\n\n> 📝 Sample #{payload.get('sample_id', '?')} → `{payload.get('canonical', '')}`"
    if t == "AgentSpoke":
        return (
            f"\n\n---\n\n### 🗣️ {payload.get('agent', '?')} — Round {payload.get('round', '?')}\n\n"
            f"{payload.get('text', '')}"
        )
    if t == "AttemptGenerated":
        return f"\n\n---\n\n### 🔄 Attempt #{payload.get('iter', 0)}\n\n{payload.get('text', '')}"
    if t == "AttemptJudged":
        issues = payload.get('issues') or []
        issues_md = "\n".join(f"  - {i}" for i in issues) if issues else "  - (none)"
        return f"\n\n> 🧑‍⚖️ **Judge score {payload.get('score', 0):.2f}** — issues:\n{issues_md}"
    if t == "CritiqueGenerated":
        return f"\n\n> 🔍 **Critique #{payload.get('iter', 0)}:** {payload.get('text', '')}"
    if t == "TerminatedEarly":
        return f"\n\n> 🏁 Stopped early — {payload.get('reason', '?')} (score {payload.get('score', 0):.2f})"
    if t == "VoteTallied":
        tally = payload.get('tally', {})
        tally_md = ", ".join(f"`{k}`: {v}" for k, v in tally.items())
        return f"\n\n> 🗳 **Vote:** winner = `{payload.get('winner')}` ({payload.get('share', 0):.0%}). Tally: {tally_md}"
    if t == "JudgeVerdict":
        return (
            f"\n\n---\n\n### 🧑‍⚖️ Judge Verdict\n\n"
            f"**Winner:** {payload.get('winner', '?')} (confidence {payload.get('confidence', 0):.0%})\n\n"
            f"**Rationale:** {payload.get('rationale', '')}"
        )
    return ""


class EventHandlers:
    """
    🎯 EVENT HANDLERS FOR UI INTERACTIONS
    """

    def __init__(self, reasoner: AdvancedReasoner):
        self.reasoner = reasoner
        self.components = UIComponents()
        self._api_client: Optional[ReasoningAPIClient] = None

    # ------------------------------------------------------------------
    # API client (lazy, cached)
    # ------------------------------------------------------------------
    def _get_api_client(self) -> ReasoningAPIClient:
        """Lazily create and cache a ReasoningAPIClient."""
        if self._api_client is None:
            base_url = f"http://{AppConfig.API_HOST}:{AppConfig.API_PORT}"
            self._api_client = ReasoningAPIClient(base_url=base_url)
        return self._api_client

    # ------------------------------------------------------------------
    # Main message handler (async generator — Gradio 6.x compatible)
    # ------------------------------------------------------------------
    async def process_message(self, message, history, mode, critique, model_name,
                              temp, tokens, template, cache):
        """
        🔄 PROCESS MESSAGE WITH STREAMING via FastAPI backend.

        Yields (history, metrics_html) tuples as an async generator.
        """
        if not message or not message.strip():
            history = history or []
            history.append({
                "role": "assistant",
                "content": "⚠️ **Input Error:** Please enter a message before submitting.",
            })
            yield history, self.components.get_metrics_html(self.reasoner)
            return

        history = history or []

        # Resolve strategy id
        if isinstance(mode, ReasoningMode):
            mode_enum = mode
        else:
            try:
                mode_enum = ReasoningMode(mode)
            except ValueError:
                mode_enum = mode  # keep raw string; _mode_to_strategy handles it
        strategy = _mode_to_strategy(mode_enum)

        # Add user message
        history.append({"role": "user", "content": message})
        yield history, self.components.get_metrics_html(self.reasoner)

        # Add empty assistant placeholder for streaming
        history.append({"role": "assistant", "content": ""})

        client = self._get_api_client()
        try:
            run_id = await client.start_run(
                query=message,
                strategy=strategy,
                reasoning_model=model_name,
                temperature=temp,
                max_tokens=tokens,
            )
        except Exception as e:
            error_msg = (
                f"❌ **Backend Error (start_run):** {e}\n\n"
                "Ensure the FastAPI backend is running."
            )
            history[-1]["content"] = error_msg
            logger.error(f"start_run failed: {e}", exc_info=True)
            yield history, self.components.get_metrics_html(self.reasoner)
            return

        # Track the prose-answer separately so the trace events stay above it
        # and the legacy bridge gets the clean final text.
        trace_so_far = ""
        final_text = ""
        try:
            async for evt in client.stream_events(run_id):
                evt_type = evt.get("type", "")

                if evt_type == "FinalAnswer":
                    final_text = evt.get("payload", {}).get("text", "") or ""
                    history[-1]["content"] = (
                        trace_so_far
                        + ("\n\n---\n\n### ✅ Final Answer\n\n" if trace_so_far else "")
                        + final_text
                    )
                    yield history, self.components.get_metrics_html(self.reasoner)

                elif evt_type == "RunFailed":
                    err = evt.get("payload", {}).get("error", "Unknown error")
                    history[-1]["content"] += f"\n\n❌ **Run failed:** {err}"
                    yield history, self.components.get_metrics_html(self.reasoner)
                    return

                elif evt_type == "RunCompleted":
                    payload = evt.get("payload", {})
                    self._bridge_to_legacy(
                        user_message=message, assistant_response=final_text or
                                     payload.get("final_answer", ""),
                        model=model_name, mode_value=getattr(mode_enum, "value",
                                                              str(mode_enum)),
                        temperature=temp, max_tokens=tokens,
                        tokens_used=int(payload.get("tokens_used", 0)),
                        elapsed_s=float(payload.get("elapsed_s", 0.0)),
                        confidence=float(payload.get("confidence", 1.0)) * 100.0,
                        critique_enabled=bool(critique),
                    )
                    yield history, self.components.get_metrics_html(self.reasoner)
                    return

                else:
                    # ThoughtGenerated, AgentSpoke, AttemptGenerated,
                    # BranchScored, BeamPruned, VoteTallied, AttemptJudged, etc.
                    snippet = _render_event_inline(evt)
                    if snippet:
                        trace_so_far += snippet
                        history[-1]["content"] = trace_so_far
                        yield history, self.components.get_metrics_html(self.reasoner)

        except Exception as e:
            error_msg = (
                f"❌ **Streaming Error:** {e}\n\nPlease try again or check the logs."
            )
            history[-1]["content"] += f"\n\n{error_msg}"
            logger.error(f"stream_events error: {e}", exc_info=True)
            yield history, self.components.get_metrics_html(self.reasoner)

    def _bridge_to_legacy(self, *, user_message: str, assistant_response: str,
                          model: str, mode_value: str, temperature: float,
                          max_tokens: int, tokens_used: int, elapsed_s: float,
                          confidence: float, critique_enabled: bool) -> None:
        """Mirror a completed FastAPI run into the legacy AdvancedReasoner's
        in-memory store so exports/search/analytics/PDF/history continue to
        work during the Spec 1 → 1.5 transition."""
        try:
            from src.models.entry import ConversationEntry
            entry = ConversationEntry(
                user_message=user_message,
                assistant_response=assistant_response,
                model=model,
                reasoning_mode=mode_value,
                temperature=temperature,
                max_tokens=max_tokens,
                tokens_used=tokens_used,
                inference_time=elapsed_s,
                reasoning_depth=1,
                confidence_score=confidence,
                critique_enabled=critique_enabled,
                cache_hit=False,
            )
            self.reasoner.conversation_manager.add_conversation(entry)
            self.reasoner.metrics.update(
                tokens=tokens_used, time_taken=elapsed_s, depth=1,
                corrections=1 if critique_enabled else 0, confidence=confidence,
            )
        except Exception as e:
            logger.warning(f"legacy bridge skipped: {e}")

    # ------------------------------------------------------------------
    # All other handlers — continue to use self.reasoner (legacy path)
    # ------------------------------------------------------------------

    def reset_chat(self):
        """🗑️ RESET CHAT"""
        self.reasoner.clear_history()
        logger.info("Chat history cleared by user")
        return [], self.components.get_metrics_html(self.reasoner)

    def export_conversation(self, format_type, include_metadata):
        """📤 EXPORT CONVERSATION"""
        try:
            content, filename = self.reasoner.export_conversation(format_type, include_metadata)
            if filename:
                logger.info(f"Conversation exported: {filename}")
                return content, filename
            else:
                return content, None
        except Exception as e:
            logger.error(f"Export error: {e}")
            return f"❌ Export failed: {str(e)}", None

    def download_chat_pdf(self):
        """📄 DOWNLOAD CHAT AS PDF"""
        try:
            pdf_file = self.reasoner.export_current_chat_pdf()
            if pdf_file:
                logger.info(f"PDF ready for download: {pdf_file}")
                return pdf_file
            else:
                logger.warning("No conversations to export")
                return None
        except Exception as e:
            logger.error(f"PDF download error: {e}")
            return None

    def search_conversations(self, keyword):
        """🔍 SEARCH CONVERSATIONS"""
        if not keyword or not keyword.strip():
            return "⚠️ **Search Error:** Please enter a search keyword."

        try:
            results = self.reasoner.search_conversations(keyword)
            if not results:
                return f"🔍 **No Results:** No conversations found containing '{keyword}'."

            output = f"### 🔍 Found {len(results)} result(s) for '{keyword}'\n\n"
            for idx, entry in results[:10]:
                output += f"**{idx + 1}.** 📅 {entry.timestamp} | 🤖 {entry.model}\n"
                preview = entry.user_message[:100].replace('\n', ' ')
                output += f"**👤 User:** {preview}...\n\n"

            if len(results) > 10:
                output += f"\n*Showing first 10 of {len(results)} results*"

            return output
        except Exception as e:
            logger.error(f"Search error: {e}")
            return f"❌ **Search Error:** {str(e)}"

    def refresh_analytics(self):
        """📊 REFRESH ANALYTICS"""
        try:
            analytics = self.reasoner.get_analytics()
            if not analytics:
                return (
                    self.components.get_empty_analytics_html(),
                    "No cache data available yet.",
                    "**Model Usage:** No data",
                    "**Reasoning Mode Usage:** No data",
                )

            analytics_html = f"""<div class="analytics-panel">
            <h3>📊 Session Analytics</h3>
            <p><strong>🔑 Session ID:</strong> {analytics['session_id']}</p>
            <p><strong>💬 Total Conversations:</strong> {analytics['total_conversations']}</p>
            <p><strong>📊 Total Tokens:</strong> {analytics['total_tokens']:,}</p>
            <p><strong>⏱️  Total Time:</strong> {analytics['total_time']:.1f}s</p>
            <p><strong>⚡ Avg Inference Time:</strong> {analytics['avg_inference_time']:.2f}s</p>
            <p><strong>🏔️  Peak Tokens:</strong> {analytics['peak_tokens']}</p>
            <p><strong>🤖 Most Used Model:</strong> {analytics['most_used_model']}</p>
            <p><strong>🧠 Most Used Mode:</strong> {analytics['most_used_mode']}</p>
            <p><strong>⚠️  Errors:</strong> {analytics['error_count']}</p>
            </div>"""

            cache_html = f"""**💾 Cache Performance:**
- ✅ Hits: {analytics['cache_hits']}
- ❌ Misses: {analytics['cache_misses']}
- 📊 Total: {analytics['cache_hits'] + analytics['cache_misses']}
- 📈 Hit Rate: {self.reasoner.cache.get_stats()['hit_rate']}%
            """

            model_dist_html = f"**🤖 Most Used Model:** {analytics['most_used_model']}"
            mode_dist_html = f"**🧠 Most Used Mode:** {analytics['most_used_mode']}"

            return analytics_html, cache_html, model_dist_html, mode_dist_html
        except Exception as e:
            logger.error(f"Analytics refresh error: {e}")
            return (
                self.components.get_empty_analytics_html(),
                "Error loading cache data",
                "No data",
                "No data",
            )

    def update_history_stats(self):
        """📚 UPDATE HISTORY STATS"""
        try:
            count = len(self.reasoner.conversation_history)
            if count == 0:
                return "📚 **No conversations yet.** Start chatting to build your history!"

            return f"""**📊 Conversation Statistics:**

- 💬 Total Conversations: {count}
- 🔑 Session ID: `{self.reasoner.session_id[:8]}...`
- 📅 Session Started: {self.reasoner.metrics.session_start}
- 🤖 Models Used: {len(self.reasoner.model_usage)}
- 🧠 Reasoning Modes Used: {len(self.reasoner.mode_usage)}
            """
        except Exception as e:
            logger.error(f"History stats error: {e}")
            return "Error loading history statistics"

    def clear_cache_action(self):
        """🗑️ CLEAR CACHE"""
        try:
            self.reasoner.cache.clear()
            logger.info("Cache cleared by user")
            return "✅ **Success:** Cache cleared successfully!"
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return f"❌ **Error:** Failed to clear cache: {str(e)}"

    def reset_metrics_action(self):
        """🔄 RESET METRICS"""
        try:
            self.reasoner.metrics.reset()
            logger.info("Metrics reset by user")
            return "✅ **Success:** Metrics reset successfully!"
        except Exception as e:
            logger.error(f"Metrics reset error: {e}")
            return f"❌ **Error:** Failed to reset metrics: {str(e)}"

    def toggle_sidebar(self, sidebar_state):
        """⚙️ TOGGLE SIDEBAR VISIBILITY"""
        new_state = not sidebar_state
        logger.info(f"Sidebar toggled: {'Visible' if new_state else 'Hidden'}")
        return gr.update(visible=new_state), new_state

"""
Event handlers for UI interactions
"""
from typing import Tuple, Optional
from pathlib import Path
import gradio as gr
from src.core.reasoner import AdvancedReasoner
from src.config.constants import ReasoningMode
from src.utils.logger import logger
from src.ui.components import UIComponents


class EventHandlers:
    """
    🎯 EVENT HANDLERS FOR UI INTERACTIONS
    """
    
    def __init__(self, reasoner: AdvancedReasoner):
        self.reasoner = reasoner
        self.components = UIComponents()
    
    def process_message(self, message, history, mode, critique, model_name, 
                       temp, tokens, template, cache):
        """
        🔄 PROCESS MESSAGE WITH STREAMING
        """
        if not message or not message.strip():
            history = history or []
            history.append({
                "role": "assistant", 
                "content": "⚠️ **Input Error:** Please enter a message before submitting."
            })
            return history, self.components.get_metrics_html(self.reasoner)
        
        history = history or []
        mode_enum = ReasoningMode(mode)
        
        # Add user message
        history.append({"role": "user", "content": message})
        yield history, self.components.get_metrics_html(self.reasoner)
        
        # Add empty assistant message for streaming
        history.append({"role": "assistant", "content": ""})
        
        try:
            for response in self.reasoner.generate_response(
                message, history[:-1], model_name, mode_enum, 
                critique, temp, tokens, template, cache
            ):
                history[-1]["content"] = response
                yield history, self.components.get_metrics_html(self.reasoner)
                
        except Exception as e:
            error_msg = f"❌ **Unexpected Error:** {str(e)}\n\nPlease try again or check the logs for details."
            history[-1]["content"] = error_msg
            logger.error(f"Error in process_message: {e}", exc_info=True)
            yield history, self.components.get_metrics_html(self.reasoner)
    
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
                    "**Reasoning Mode Usage:** No data"
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
            return self.components.get_empty_analytics_html(), "Error loading cache data", "No data", "No data"
    
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

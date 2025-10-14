"""
Reusable UI components
"""
from src.config.settings import AppConfig
from src.config.constants import ReasoningMode, ModelConfig
from src.core.reasoner import AdvancedReasoner
from src.core.prompt_engine import PromptEngine
from src.utils.logger import logger


class UIComponents:
    """
    🎨 REUSABLE UI COMPONENTS
    """
    
    @staticmethod
    def get_header_html() -> str:
        """
        📋 GENERATE HEADER HTML
        """
        return """
        <div class="research-header">
            <h1>🧠 Advanced AI Reasoning System Pro</h1>
            <p><strong>Research-Backed Implementation:</strong> Tree of Thoughts + Constitutional AI + Multi-Agent Validation + Performance Optimization</p>
            <div style="margin-top: 1rem;">
                <span class="badge">🌳 Yao et al. 2023 - Tree of Thoughts</span>
                <span class="badge">🛡️ Bai et al. 2022 - Constitutional AI</span>
                <span class="badge">🔬 6 Advanced Reasoning Modes</span>
                <span class="badge">⚡ Cache + Rate Limiting</span>
                <span class="badge">🎛️ Collapsible Sidebar</span>
                <span class="badge">📊 Real-Time Analytics</span>
            </div>
        </div>
        """
    
    @staticmethod
    def get_metrics_html(reasoner: AdvancedReasoner) -> str:
        """
        📊 GENERATE METRICS HTML
        """
        m = reasoner.metrics
        cache_stats = reasoner.cache.get_stats()
        
        if m.tokens_used > 0:
            status = '<span class="status-active">● Active</span>'
        else:
            status = '<span style="color: #64748b;">● Ready</span>'
        
        return f"""<div class="metrics-card">
        <strong>⚡ Inference:</strong> {m.inference_time:.2f}s<br>
        <strong>⏱️  Avg Time:</strong> {m.avg_response_time:.2f}s<br>
        <strong>🚀 Speed:</strong> {m.tokens_per_second:.1f} tok/s<br>
        <strong>🧠 Reasoning:</strong> {m.reasoning_depth} steps<br>
        <strong>🔄 Corrections:</strong> {m.self_corrections}<br>
        <strong>✨ Confidence:</strong> {m.confidence_score:.1f}%<br>
        <strong>💬 Total:</strong> {m.total_conversations}<br>
        <strong>📊 Tokens:</strong> {m.tokens_used:,}<br>
        <strong>🏔️  Peak:</strong> {m.peak_tokens}<br>
        <strong>💾 Cache:</strong> {cache_stats['hit_rate']}% hit rate<br>
        <strong>📡 Status:</strong> {status}<br>
        <strong>🔑 Session:</strong> {reasoner.session_id[:8]}...
        </div>"""
    
    @staticmethod
    def get_empty_analytics_html() -> str:
        """
        📊 GENERATE EMPTY ANALYTICS HTML
        """
        return """<div class="analytics-panel">
        <h3>📊 No Analytics Data Yet</h3>
        <p>Start a conversation to see detailed analytics and insights!</p>
        <p style="margin-top: 1rem; font-size: 0.9em;">Metrics tracked: tokens, speed, reasoning depth, confidence scores, and more.</p>
        </div>"""
    
    @staticmethod
    def get_system_info_html(reasoner: AdvancedReasoner) -> str:
        """
        ℹ️ GENERATE SYSTEM INFO HTML
        """
        return f"""
        **Session ID:** `{reasoner.session_id}`  
        **Environment:** `{AppConfig.ENV}`  
        **Cache Size:** {AppConfig.CACHE_SIZE} entries  
        **Cache TTL:** {AppConfig.CACHE_TTL}s  
        **Rate Limit:** {AppConfig.RATE_LIMIT_REQUESTS} req/{AppConfig.RATE_LIMIT_WINDOW}s  
        **Max History:** {AppConfig.MAX_HISTORY_LENGTH} messages  
        **Available Models:** {len(ModelConfig)} models  
        **Reasoning Modes:** {len(ReasoningMode)} modes
        """
    
    @staticmethod
    def get_settings_table_html() -> str:
        """
        ⚙️ GENERATE SETTINGS TABLE HTML
        """
        return f"""
        | Setting | Value |
        |---------|-------|
        | **Environment** | `{AppConfig.ENV}` |
        | **Debug Mode** | `{AppConfig.DEBUG}` |
        | **Max History Length** | {AppConfig.MAX_HISTORY_LENGTH} messages |
        | **Max Conversation Storage** | {AppConfig.MAX_CONVERSATION_STORAGE} conversations |
        | **Cache Size** | {AppConfig.CACHE_SIZE} entries |
        | **Cache TTL** | {AppConfig.CACHE_TTL} seconds |
        | **Rate Limit** | {AppConfig.RATE_LIMIT_REQUESTS} requests per {AppConfig.RATE_LIMIT_WINDOW}s |
        | **Request Timeout** | {AppConfig.REQUEST_TIMEOUT} seconds |
        | **Max Retries** | {AppConfig.MAX_RETRIES} attempts |
        | **Export Directory** | `{AppConfig.EXPORT_DIR}` |
        | **Backup Directory** | `{AppConfig.BACKUP_DIR}` |
        | **Available Models** | {len(ModelConfig)} models |
        | **Reasoning Modes** | {len(ReasoningMode)} modes |
        """
    
    @staticmethod
    def get_reasoning_mode_choices() -> list:
        """Get reasoning mode choices"""
        return [mode.value for mode in ReasoningMode]
    
    @staticmethod
    def get_prompt_template_choices() -> list:
        """Get prompt template choices"""
        return list(PromptEngine.TEMPLATES.keys())
    
    @staticmethod
    def get_model_choices() -> list:
        """Get model choices"""
        return [m.model_id for m in ModelConfig]

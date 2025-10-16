"""
Modern UI with all features - Compact & High Quality
"""
import gradio as gr
from src.core.reasoner import AdvancedReasoner
from src.config.constants import ReasoningMode, ModelConfig
from src.config.settings import AppConfig
from src.ui.handlers import EventHandlers
from src.ui.components import UIComponents

# Compact Modern CSS
MODERN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root{--primary:#6366f1;--bg:#0f172a;--surface:rgba(255,255,255,0.05);--border:rgba(255,255,255,0.1);--text:#f1f5f9;--glow:0 0 20px rgba(99,102,241,0.3)}
*{font-family:'Inter',sans-serif}
body{background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);color:var(--text)}
.hero-header{background:linear-gradient(135deg,rgba(99,102,241,0.2),rgba(139,92,246,0.2));backdrop-filter:blur(20px);border:1px solid var(--border);border-radius:16px;padding:2rem;margin-bottom:1.5rem;box-shadow:var(--glow);animation:slideIn 0.5s ease}
.hero-header h1{font-size:2rem;font-weight:700;background:linear-gradient(135deg,#f1f5f9,#a5b4fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0 0 0.5rem}
.badges{display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:1rem}
.badge{padding:0.4rem 0.8rem;background:var(--surface);border:1px solid var(--border);border-radius:8px;font-size:0.8rem;transition:all 0.3s}
.badge:hover{background:rgba(99,102,241,0.1);border-color:var(--primary);transform:translateY(-2px)}
.metrics-card{background:linear-gradient(135deg,rgba(16,185,129,0.1),rgba(6,182,212,0.1));backdrop-filter:blur(20px);border:1px solid rgba(16,185,129,0.2);border-radius:12px;padding:1.2rem;margin-top:1rem}
.metric-row{display:flex;justify-content:space-between;padding:0.5rem 0;border-bottom:1px solid var(--border)}
.metric-row:last-child{border-bottom:none}
.metric-label{color:#cbd5e1;font-size:0.85rem}
.metric-value{font-weight:700;font-family:monospace}
.status-active{color:#10b981}
.status-idle{color:#f59e0b}
@keyframes slideIn{from{opacity:0;transform:translateY(-20px)}to{opacity:1;transform:translateY(0)}}
.gradio-button{border-radius:8px;font-weight:600;transition:all 0.3s}
.gradio-button:hover{transform:translateY(-2px)}
</style>
"""

# Compact Header
HEADER = f"""
<div class="hero-header">
<h1>🧠 AI Reasoning System Pro</h1>
<p style="color:#cbd5e1;margin:0">Advanced reasoning with Tree of Thoughts, Constitutional AI & Real-time Analytics</p>
<div class="badges">
<div class="badge">🌳 Tree of Thoughts</div>
<div class="badge">🛡️ Constitutional AI</div>
<div class="badge">🔬 {len(ReasoningMode)} Modes</div>
<div class="badge">⚡ Real-Time</div>
<div class="badge">💾 Smart Cache</div>
<div class="badge">📊 Analytics</div>
</div>
</div>
"""

def create_metrics_html(reasoner):
    """Compact metrics display"""
    m = reasoner.metrics
    cache = reasoner.cache.get_stats()
    status = "status-active" if m.tokens_used > 0 else "status-idle"
    return f"""
    <div class="metrics-card">
    <div class="metric-row"><span class="metric-label">⚡ Inference</span><span class="metric-value">{m.inference_time:.2f}s</span></div>
    <div class="metric-row"><span class="metric-label">🚀 Speed</span><span class="metric-value">{m.tokens_per_second:.1f} tok/s</span></div>
    <div class="metric-row"><span class="metric-label">🧠 Depth</span><span class="metric-value">{m.reasoning_depth} steps</span></div>
    <div class="metric-row"><span class="metric-label">💬 Total</span><span class="metric-value">{m.total_conversations}</span></div>
    <div class="metric-row"><span class="metric-label">📊 Tokens</span><span class="metric-value">{m.tokens_used:,}</span></div>
    <div class="metric-row"><span class="metric-label">💾 Cache</span><span class="metric-value">{cache['hit_rate']}%</span></div>
    <div class="metric-row"><span class="metric-label">📡 Status</span><span class="metric-value {status}">{"Active" if m.tokens_used > 0 else "Ready"}</span></div>
    </div>
    """

def create_modern_ui():
    """Create modern UI with all features"""
    reasoner = AdvancedReasoner()
    components = UIComponents()
    handlers = EventHandlers(reasoner)
    
    with gr.Blocks(
        theme=gr.themes.Soft(
            primary_hue=AppConfig.THEME_PRIMARY,
            secondary_hue=AppConfig.THEME_SECONDARY,
            font=gr.themes.GoogleFont("Inter")
        ),
        css=MODERN_CSS,
        title="🧠 AI Reasoning System Pro"
    ) as demo:
        
        gr.HTML(HEADER)
        
        # Main Tabs
        with gr.Tabs() as tabs:
            
            # TAB 1: Reasoning Workspace
            with gr.Tab("💬 Reasoning Workspace"):
                with gr.Row():
                    with gr.Column(scale=4):
                        chatbot = gr.Chatbot(
                            label="💬 Reasoning Workspace",
                            height=600,
                            show_copy_button=True,
                            type="messages",
                            bubble_full_width=False,
                            avatar_images=(
                                "https://api.dicebear.com/7.x/avataaars/svg?seed=User&backgroundColor=6366f1",
                                "https://api.dicebear.com/7.x/bottts/svg?seed=AI&backgroundColor=8b5cf6"
                            )
                        )
                        
                        msg = gr.Textbox(
                            placeholder="💭 Ask me anything... I'll use advanced reasoning to solve complex problems.",
                            label="Query Input",
                            lines=3,
                            max_lines=10,
                            show_label=False
                        )
                        
                        with gr.Row():
                            submit_btn = gr.Button("🚀 Process", variant="primary", scale=2, size="lg")
                            clear_btn = gr.Button("🗑️ Clear", scale=1, size="lg")
                            pdf_btn = gr.Button("📄 PDF", scale=1, size="lg", variant="secondary")
                            toggle_sidebar_btn = gr.Button("⚙️ Settings", scale=1, size="lg", variant="secondary")
                    
                    # Collapsible Sidebar
                    with gr.Column(scale=1, visible=True) as sidebar:
                        gr.Markdown("### ⚙️ Configuration")
                        
                        reasoning_mode = gr.Radio(
                            choices=components.get_reasoning_mode_choices(),
                            value=ReasoningMode.TREE_OF_THOUGHTS.value,
                            label="🧠 Reasoning Method",
                            info="Select reasoning strategy"
                        )
                        
                        prompt_template = gr.Dropdown(
                            choices=components.get_prompt_template_choices(),
                            value="Custom",
                            label="📝 Prompt Template",
                            info="Pre-built templates"
                        )
                        
                        enable_critique = gr.Checkbox(
                            label="🔍 Enable Self-Critique",
                            value=True,
                            info="Auto validation"
                        )
                        
                        use_cache = gr.Checkbox(
                            label="💾 Use Cache",
                            value=True,
                            info="Faster responses"
                        )
                        
                        model = gr.Dropdown(
                            choices=components.get_model_choices(),
                            value=ModelConfig.LLAMA_70B.model_id,
                            label="🤖 AI Model"
                        )
                        
                        with gr.Accordion("🎛️ Advanced", open=False):
                            temperature = gr.Slider(
                                AppConfig.MIN_TEMPERATURE,
                                AppConfig.MAX_TEMPERATURE,
                                value=AppConfig.DEFAULT_TEMPERATURE,
                                step=0.1,
                                label="🌡️ Temperature"
                            )
                            
                            max_tokens = gr.Slider(
                                AppConfig.MIN_TOKENS,
                                8000,
                                value=AppConfig.DEFAULT_MAX_TOKENS,
                                step=500,
                                label="📊 Max Tokens"
                            )
                        
                        gr.Markdown("### 📊 Live Metrics")
                        metrics_display = gr.HTML(value=create_metrics_html(reasoner))
                        
                        with gr.Accordion("ℹ️ System Info", open=False):
                            gr.HTML(components.get_system_info_html(reasoner))
                
                pdf_file_output = gr.File(label="📥 Download PDF", visible=True, file_types=[".pdf"])
                sidebar_visible_state = gr.State(value=True)
            
            # TAB 2: Export & History
            with gr.Tab("📤 Export & History"):
                gr.Markdown("### 📤 Export Conversations")
                gr.Markdown("Export your conversations in multiple formats with optional metadata.")
                
                with gr.Row():
                    export_format = gr.Radio(
                        choices=["json", "markdown", "txt", "pdf"],
                        value="markdown",
                        label="Export Format"
                    )
                    include_meta = gr.Checkbox(
                        label="Include Metadata",
                        value=True,
                        info="Timestamps, models, metrics"
                    )
                
                export_btn = gr.Button("📥 Export Now", variant="primary", size="lg")
                export_output = gr.Code(label="Preview", language="markdown", lines=15)
                download_file = gr.File(label="📥 Download File", file_types=[".json", ".md", ".txt", ".pdf"])
                
                gr.Markdown("---")
                gr.Markdown("### 🔍 Search Conversations")
                
                with gr.Row():
                    search_input = gr.Textbox(
                        placeholder="Enter keyword to search...",
                        scale=3,
                        label="Search Query",
                        show_label=False
                    )
                    search_btn = gr.Button("🔍 Search", scale=1, size="lg")
                
                search_results = gr.Markdown("💡 **Tip:** Enter a keyword and click Search.")
                
                gr.Markdown("---")
                gr.Markdown("### 📊 Conversation History")
                history_stats = gr.Markdown("Loading statistics...")
            
            # TAB 3: Analytics
            with gr.Tab("📊 Analytics & Insights"):
                gr.Markdown("### 📊 Performance Analytics Dashboard")
                refresh_btn = gr.Button("🔄 Refresh Analytics", variant="primary", size="lg")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### ⚡ Performance Metrics")
                        analytics_display = gr.HTML(components.get_empty_analytics_html())
                    
                    with gr.Column():
                        gr.Markdown("#### 💾 Cache Statistics")
                        cache_display = gr.Markdown("No cache data yet. Start a conversation to see cache performance.")
                
                gr.Markdown("---")
                gr.Markdown("### 📈 Usage Distribution")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 🤖 Model Usage")
                        model_dist = gr.Markdown("No data yet. Models will be tracked as you use them.")
                    
                    with gr.Column():
                        gr.Markdown("#### 🧠 Reasoning Mode Usage")
                        mode_dist = gr.Markdown("No data yet. Reasoning modes will be tracked as you use them.")
            
            # TAB 4: Settings
            with gr.Tab("⚙️ Settings"):
                gr.Markdown("### ⚙️ Application Settings")
                gr.Markdown("Current configuration and system controls.")
                gr.HTML(components.get_settings_table_html())
                
                gr.Markdown("---")
                gr.Markdown("### 🔧 System Actions")
                
                with gr.Row():
                    clear_cache_btn = gr.Button("🗑️ Clear Cache", variant="stop", size="lg")
                    reset_metrics_btn = gr.Button("🔄 Reset Metrics", variant="secondary", size="lg")
                
                cache_status = gr.Markdown("")
        
        # Event Handlers
        def toggle_sidebar(visible):
            return gr.update(visible=not visible), not visible
        
        # Reasoning workspace handlers
        submit_btn.click(
            handlers.process_message,
            [msg, chatbot, reasoning_mode, enable_critique, model, temperature, max_tokens, prompt_template, use_cache],
            [chatbot, metrics_display]
        ).then(lambda: "", None, msg)
        
        msg.submit(
            handlers.process_message,
            [msg, chatbot, reasoning_mode, enable_critique, model, temperature, max_tokens, prompt_template, use_cache],
            [chatbot, metrics_display]
        ).then(lambda: "", None, msg)
        
        clear_btn.click(handlers.reset_chat, None, [chatbot, metrics_display])
        pdf_btn.click(handlers.download_chat_pdf, None, pdf_file_output)
        toggle_sidebar_btn.click(toggle_sidebar, sidebar_visible_state, [sidebar, sidebar_visible_state])
        
        # Export handlers (corrected method name)
        export_btn.click(
            handlers.export_conversation,
            [export_format, include_meta],
            [export_output, download_file]
        )
        
        search_btn.click(
            handlers.search_conversations,
            search_input,
            search_results
        )
        
        # Analytics handlers
        refresh_btn.click(
            handlers.refresh_analytics,
            None,
            [analytics_display, cache_display, model_dist, mode_dist]
        )
        
        # Settings handlers
        clear_cache_btn.click(handlers.clear_cache_action, None, cache_status)
        reset_metrics_btn.click(handlers.reset_metrics_action, None, cache_status)
        
        # Load initial data
        demo.load(handlers.update_history_stats, None, history_stats)
    
    return demo

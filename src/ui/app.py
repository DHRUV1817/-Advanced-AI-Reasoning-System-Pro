"""
Main Gradio application interface
"""
import gradio as gr
from src.core.reasoner import AdvancedReasoner
from src.core.prompt_engine import PromptEngine
from src.config.settings import AppConfig
from src.config.constants import ReasoningMode, ModelConfig
from src.ui.components import UIComponents
from src.ui.handlers import EventHandlers
from src.ui.styles import SIDEBAR_CSS
from src.utils.logger import logger


def create_ui() -> gr.Blocks:
    """
    🎨 CREATE ENHANCED GRADIO INTERFACE
    """
    
    # Initialize reasoner and components
    reasoner = AdvancedReasoner()
    components = UIComponents()
    handlers = EventHandlers(reasoner)
    
    with gr.Blocks(
        theme=gr.themes.Soft(
            primary_hue=AppConfig.THEME_PRIMARY,
            secondary_hue=AppConfig.THEME_SECONDARY,
            font=gr.themes.GoogleFont("Inter")
        ),
        css=SIDEBAR_CSS,
        title="Advanced AI Reasoning System Pro"
    ) as demo:
        
        # Header
        gr.HTML(components.get_header_html())
        
        # Main Tabs
        with gr.Tabs():
            
            # ==================== TAB 1: REASONING WORKSPACE ====================
            with gr.Tab("🧠 Reasoning Workspace"):
                with gr.Row():
                    
                    # Main Chat Area
                    with gr.Column(scale=4):
                        chatbot = gr.Chatbot(
                            label="💬 Reasoning Workspace",
                            height=750,
                            show_copy_button=True,
                            type="messages",
                            avatar_images=(
                                "https://api.dicebear.com/7.x/avataaars/svg?seed=User",
                                "https://api.dicebear.com/7.x/bottts/svg?seed=AI"
                            ),
                            bubble_full_width=False
                        )
                        
                        msg = gr.Textbox(
                            placeholder="💭 Enter your complex problem or research question... (Max 10,000 characters)",
                            label="Query Input",
                            lines=3,
                            max_lines=10,
                            show_label=False
                        )
                        
                        with gr.Row():
                            submit_btn = gr.Button("🚀 Process", variant="primary", scale=2, size="lg")
                            clear_btn = gr.Button("🗑️ Clear", scale=1, size="lg")
                            pdf_btn = gr.Button("📄 Download PDF", scale=1, size="lg", variant="secondary")
                            toggle_sidebar_btn = gr.Button("⚙️ Settings", scale=1, size="lg", variant="secondary")
                    
                    # Collapsible Sidebar
                    with gr.Column(scale=1, visible=True, elem_classes="settings-column") as sidebar:
                        gr.Markdown("### ⚙️ Configuration")
                        
                        reasoning_mode = gr.Radio(
                            choices=components.get_reasoning_mode_choices(),
                            value=ReasoningMode.TREE_OF_THOUGHTS.value,
                            label="🧠 Reasoning Method",
                            info="Select your preferred reasoning strategy"
                        )
                        
                        prompt_template = gr.Dropdown(
                            choices=components.get_prompt_template_choices(),
                            value="Custom",
                            label="📝 Prompt Template",
                            info="Pre-built prompt templates for common tasks"
                        )
                        
                        enable_critique = gr.Checkbox(
                            label="🔍 Enable Self-Critique",
                            value=True,
                            info="Add automatic validation and correction phase"
                        )
                        
                        use_cache = gr.Checkbox(
                            label="💾 Use Response Cache",
                            value=True,
                            info="Cache responses for faster repeated queries"
                        )
                        
                        model = gr.Dropdown(
                            choices=components.get_model_choices(),
                            value=ModelConfig.LLAMA_70B.model_id,
                            label="🤖 AI Model",
                            info="Select the AI model to use"
                        )
                        
                        with gr.Accordion("🎛️ Advanced Settings", open=False):
                            temperature = gr.Slider(
                                AppConfig.MIN_TEMPERATURE, 
                                AppConfig.MAX_TEMPERATURE, 
                                value=AppConfig.DEFAULT_TEMPERATURE, 
                                step=0.1,
                                label="🌡️ Temperature",
                                info="Higher = more creative, Lower = more focused"
                            )
                            
                            max_tokens = gr.Slider(
                                AppConfig.MIN_TOKENS, 
                                8000, 
                                value=AppConfig.DEFAULT_MAX_TOKENS, 
                                step=500,
                                label="📊 Max Tokens",
                                info="Maximum response length"
                            )
                        
                        gr.Markdown("### 📊 Live Metrics")
                        metrics_display = gr.Markdown(value=components.get_metrics_html(reasoner))
                        
                        with gr.Accordion("ℹ️ System Info", open=False):
                            gr.Markdown(components.get_system_info_html(reasoner))
                
                # PDF download output
                pdf_file_output = gr.File(
                    label="📥 Download Your PDF Report", 
                    visible=True,
                    file_types=[".pdf"]
                )
            
            # ==================== TAB 2: EXPORT & HISTORY ====================
            with gr.Tab("📤 Export & History"):
                gr.Markdown("### 📤 Export Conversation History")
                gr.Markdown("Export your conversations in multiple formats with optional metadata.")
                
                with gr.Row():
                    export_format = gr.Radio(
                        choices=["json", "markdown", "txt", "pdf"],
                        value="markdown",
                        label="📄 Export Format",
                        info="Choose your preferred export format"
                    )
                    include_meta = gr.Checkbox(
                        label="📋 Include Metadata",
                        value=True,
                        info="Include timestamps, models, and performance metrics"
                    )
                
                export_btn = gr.Button("📥 Export Now", variant="primary", size="lg")
                export_output = gr.Code(label="Exported Data Preview", language="markdown", lines=20)
                download_file = gr.File(
                    label="📥 Download Export File",
                    file_types=[".json", ".md", ".txt", ".pdf"]
                )
                
                gr.Markdown("---")
                gr.Markdown("### 🔍 Search Conversations")
                gr.Markdown("Search through your conversation history by keywords.")
                
                with gr.Row():
                    search_input = gr.Textbox(
                        placeholder="🔎 Enter keyword to search...", 
                        scale=3,
                        label="Search Query",
                        show_label=False
                    )
                    search_btn = gr.Button("🔍 Search", scale=1, size="lg")
                
                search_results = gr.Markdown("💡 **Tip:** Enter a keyword and click Search to find relevant conversations.")
                
                gr.Markdown("---")
                gr.Markdown("### 📚 Conversation History")
                history_stats = gr.Markdown("Loading statistics...")
            
            # ==================== TAB 3: ANALYTICS & INSIGHTS ====================
            with gr.Tab("📊 Analytics & Insights"):
                gr.Markdown("### 📊 Performance Analytics Dashboard")
                refresh_btn = gr.Button("🔄 Refresh Analytics", variant="primary", size="lg")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 📈 Performance Metrics")
                        analytics_display = gr.Markdown(components.get_empty_analytics_html())
                    
                    with gr.Column():
                        gr.Markdown("#### 💾 Cache Statistics")
                        cache_display = gr.Markdown("No cache data available yet. Start a conversation to see cache performance.")
                
                gr.Markdown("---")
                gr.Markdown("### 📊 Usage Distribution")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 🤖 Model Usage")
                        model_dist = gr.Markdown("**No data yet.** Models will be tracked as you use them.")
                    
                    with gr.Column():
                        gr.Markdown("#### 🧠 Reasoning Mode Usage")
                        mode_dist = gr.Markdown("**No data yet.** Reasoning modes will be tracked as you use them.")
            
            # ==================== TAB 4: SETTINGS ====================
            with gr.Tab("⚙️ Settings"):
                gr.Markdown("### ⚙️ Application Settings")
                gr.Markdown("Current configuration and system controls.")
                
                gr.Markdown(components.get_settings_table_html())
                
                gr.Markdown("---")
                gr.Markdown("### 🛠️ System Actions")
                
                with gr.Row():
                    clear_cache_btn = gr.Button("🗑️ Clear Cache", variant="stop", size="lg")
                    reset_metrics_btn = gr.Button("🔄 Reset Metrics", variant="secondary", size="lg")
                
                cache_status = gr.Markdown("")
        
        # ==================== EVENT HANDLERS ====================
        
        # State management
        sidebar_visible_state = gr.State(value=True)
        
        # Message submission
        submit_btn.click(
            handlers.process_message,
            [msg, chatbot, reasoning_mode, enable_critique, model, 
             temperature, max_tokens, prompt_template, use_cache],
            [chatbot, metrics_display]
        ).then(lambda: "", None, msg)
        
        msg.submit(
            handlers.process_message,
            [msg, chatbot, reasoning_mode, enable_critique, model, 
             temperature, max_tokens, prompt_template, use_cache],
            [chatbot, metrics_display]
        ).then(lambda: "", None, msg)
        
        # Chat controls
        clear_btn.click(handlers.reset_chat, None, [chatbot, metrics_display])
        pdf_btn.click(handlers.download_chat_pdf, None, pdf_file_output)
        
        # Sidebar toggle
        toggle_sidebar_btn.click(
            handlers.toggle_sidebar,
            inputs=[sidebar_visible_state],
            outputs=[sidebar, sidebar_visible_state]
        )
        
        # Export & Search
        export_btn.click(handlers.export_conversation, [export_format, include_meta], [export_output, download_file])
        search_btn.click(handlers.search_conversations, search_input, search_results)
        
        # Analytics
        refresh_btn.click(handlers.refresh_analytics, None, [analytics_display, cache_display, model_dist, mode_dist])
        
        # Settings actions
        clear_cache_btn.click(handlers.clear_cache_action, None, cache_status)
        reset_metrics_btn.click(handlers.reset_metrics_action, None, cache_status)
        
        # Load history stats on page load
        demo.load(handlers.update_history_stats, None, history_stats)
    
    return demo

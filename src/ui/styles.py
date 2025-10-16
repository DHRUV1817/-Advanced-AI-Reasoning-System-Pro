"""
CSS styles for the Gradio interface
"""

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
:root {
    --bg-primary: #0f0f0f;
    --bg-secondary: #1a1a1a;
    --bg-tertiary: #2d2d2d;
    --bg-card: #1e1e1e;
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
    --text-tertiary: #888888;
    --accent-primary: #3b82f6;
    --accent-secondary: #60a5fa;
    --accent-gradient: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
    --border-color: #333333;
    --border-light: #404040;
    --shadow-dark: 0 4px 6px -1px rgba(0, 0, 0, 0.6);
    --shadow-medium: 0 2px 4px rgba(0, 0, 0, 0.4);
    --shadow-light: 0 1px 2px rgba(0, 0, 0, 0.3);
    --border-radius: 12px;
    --border-radius-lg: 16px;
    --transition: all 0.3s ease;
}

/* ==================== GLOBAL STYLES ==================== */

.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    max-width: 1400px !important;
    margin: 0 auto !important;
    padding: 20px !important;
}

* {
    color: var(--text-primary) !important;
}

/* ==================== ENHANCED HEADER ==================== */

.research-header {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    padding: 2.5rem 2rem !important;
    border-radius: var(--border-radius-lg) !important;
    margin-bottom: 2rem !important;
    box-shadow: var(--shadow-dark) !important;
    position: relative;
    overflow: hidden;
}

.research-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--accent-gradient);
}

.research-header h1 {
    font-size: 2.5rem !important;
    font-weight: 700 !important;
    margin-bottom: 1rem !important;
    color: var(--text-primary) !important;
    background: none !important;
    -webkit-text-fill-color: var(--text-primary) !important;
}

.research-header .subtitle {
    font-size: 1.1rem !important;
    color: var(--text-secondary) !important;
    margin-bottom: 1.5rem !important;
    line-height: 1.6 !important;
}

/* ==================== CLEAN BADGES ==================== */

.badge {
    background: var(--bg-tertiary) !important;
    color: var(--text-secondary) !important;
    padding: 0.5rem 1rem !important;
    border-radius: 20px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    margin: 0.3rem !important;
    border: 1px solid var(--border-light) !important;
    transition: var(--transition) !important;
    backdrop-filter: none !important;
}

.badge:hover {
    background: var(--accent-primary) !important;
    color: white !important;
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-medium) !important;
}

/* ==================== HIGH CONTRAST CARDS ==================== */

.metrics-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    padding: 1.5rem !important;
    border-radius: var(--border-radius) !important;
    margin: 1rem 0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    transition: var(--transition) !important;
    box-shadow: var(--shadow-medium) !important;
    position: relative;
}

.metrics-card:hover {
    border-color: var(--accent-primary) !important;
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-dark) !important;
}

.metrics-card * {
    color: var(--text-primary) !important;
    font-weight: 400 !important;
}

.metrics-card strong {
    color: var(--accent-secondary) !important;
    font-weight: 600 !important;
}

.metrics-card p {
    margin: 0.5rem 0 !important;
    line-height: 1.5 !important;
    color: var(--text-primary) !important;
}

/* ==================== ANALYTICS PANEL ==================== */

.analytics-panel {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
    padding: 2rem !important;
    border-radius: var(--border-radius) !important;
    box-shadow: var(--shadow-dark) !important;
    margin: 1rem 0 !important;
}

.analytics-panel * {
    color: var(--text-primary) !important;
}

.analytics-panel h3 {
    margin-bottom: 1.5rem !important;
    font-size: 1.4rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
}

.analytics-panel p {
    line-height: 1.6 !important;
    color: var(--text-secondary) !important;
    margin-bottom: 1rem !important;
}

.analytics-panel strong {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* ==================== STATUS INDICATORS ==================== */

.status-active {
    color: var(--success) !important;
    font-weight: 600 !important;
    padding: 0.2rem 0.5rem !important;
    background: rgba(16, 185, 129, 0.1) !important;
    border-radius: 4px !important;
    border: 1px solid rgba(16, 185, 129, 0.3) !important;
}

/* ==================== BUTTON ENHANCEMENTS ==================== */

.gr-button {
    background: var(--accent-primary) !important;
    color: white !important;
    border: none !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: var(--transition) !important;
    box-shadow: var(--shadow-medium) !important;
}

.gr-button:hover {
    background: var(--accent-secondary) !important;
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-dark) !important;
}

.gr-button:active {
    transform: translateY(0) !important;
}

/* ==================== INPUT ENHANCEMENTS ==================== */

.gr-input, .gr-textbox, .gr-dropdown {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
    padding: 0.75rem 1rem !important;
    transition: var(--transition) !important;
}

.gr-input:focus, .gr-textbox:focus, .gr-dropdown:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    outline: none !important;
}

.gr-input::placeholder, .gr-textbox::placeholder {
    color: var(--text-tertiary) !important;
}

/* ==================== MARKDOWN TEXT FIXES ==================== */

.gr-markdown {
    color: var(--text-primary) !important;
}

.gr-markdown p {
    color: var(--text-primary) !important;
    line-height: 1.6 !important;
}

.gr-markdown strong {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

.gr-markdown .metrics-card {
    color: var(--text-primary) !important;
}

.gr-markdown .metrics-card p {
    color: var(--text-primary) !important;
}

.gr-markdown .metrics-card span {
    color: var(--text-primary) !important;
}

/* ==================== SIDEBAR & LAYOUT ==================== */

.sidebar-hidden {
    display: none !important;
}

.toggle-btn {
    background: var(--accent-primary) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.75rem !important;
    cursor: pointer !important;
    transition: var(--transition) !important;
    box-shadow: var(--shadow-medium) !important;
}

.toggle-btn:hover {
    background: var(--accent-secondary) !important;
    transform: scale(1.05) !important;
}

.settings-column {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--border-radius) !important;
    padding: 1.5rem !important;
}

/* ==================== TABLE STYLES ==================== */

.gr-table {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--border-radius) !important;
    overflow: hidden !important;
}

.gr-table th {
    background: var(--bg-tertiary) !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    padding: 1rem !important;
    border-bottom: 1px solid var(--border-color) !important;
}

.gr-table td {
    padding: 1rem !important;
    border-bottom: 1px solid var(--border-light) !important;
    color: var(--text-primary) !important;
}

.gr-table tr:hover {
    background: var(--bg-tertiary) !important;
}

/* ==================== SCROLLBAR STYLING ==================== */

::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-secondary);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: var(--bg-tertiary);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--accent-primary);
}

/* ==================== LOADING STATES ==================== */

.loading-spinner {
    border: 3px solid var(--bg-tertiary);
    border-top: 3px solid var(--accent-primary);
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin: 20px auto;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* ==================== PROGRESS BARS ==================== */

.gr-progress {
    background: var(--bg-tertiary) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

.gr-progress .inner {
    background: var(--accent-gradient) !important;
}

/* ==================== ALERT STYLES ==================== */

.gr-alert {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--border-radius) !important;
    padding: 1rem 1.5rem !important;
    margin: 1rem 0 !important;
}

.gr-alert.success {
    border-left: 4px solid var(--success) !important;
}

.gr-alert.warning {
    border-left: 4px solid var(--warning) !important;
}

.gr-alert.error {
    border-left: 4px solid var(--error) !important;
}

/* ==================== RESPONSIVE DESIGN ==================== */

@media (max-width: 768px) {
    .gradio-container {
        padding: 1rem !important;
    }
    
    .research-header {
        padding: 2rem 1.5rem !important;
    }
    
    .research-header h1 {
        font-size: 2rem !important;
    }
    
    .badge {
        font-size: 0.8rem !important;
        padding: 0.4rem 0.8rem !important;
    }
    
    .metrics-card {
        padding: 1.25rem !important;
    }
    
    .analytics-panel {
        padding: 1.5rem !important;
    }
}

@media (max-width: 480px) {
    .research-header h1 {
        font-size: 1.75rem !important;
    }
    
    .research-header .subtitle {
        font-size: 1rem !important;
    }
    
    .metrics-card {
        padding: 1rem !important;
        font-size: 0.9rem !important;
    }
}

/* ==================== ACCESSIBILITY ENHANCEMENTS ==================== */

@media (prefers-reduced-motion: reduce) {
    * {
        transition: none !important;
        animation: none !important;
    }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    :root {
        --bg-primary: #000000;
        --bg-secondary: #0a0a0a;
        --bg-card: #111111;
        --text-primary: #ffffff;
        --text-secondary: #e0e0e0;
        --border-color: #555555;
    }
    
    .badge {
        border: 2px solid var(--border-color) !important;
    }
}

/* ==================== FOCUS INDICATORS ==================== */

button:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible {
    outline: 2px solid var(--accent-primary) !important;
    outline-offset: 2px !important;
}

/* ==================== UTILITY CLASSES ==================== */

.text-primary { color: var(--text-primary) !important; }
.text-secondary { color: var(--text-secondary) !important; }
.text-accent { color: var(--accent-primary) !important; }
.bg-card { background: var(--bg-card) !important; }
.bg-secondary { background: var(--bg-secondary) !important; }

.border-light { border-color: var(--border-light) !important; }
.border-medium { border-color: var(--border-color) !important; }

.shadow-medium { box-shadow: var(--shadow-medium) !important; }
.shadow-dark { box-shadow: var(--shadow-dark) !important; }

/* ==================== CODE BLOCKS ==================== */

.gr-code {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
    padding: 1rem !important;
    font-family: 'JetBrains Mono', monospace !important;
    color: var(--text-primary) !important;
}

.gr-code .token.keyword { color: var(--accent-secondary) !important; }
.gr-code .token.string { color: var(--success) !important; }
.gr-code .token.comment { color: var(--text-tertiary) !important; }
.gr-code .token.function { color: var(--accent-primary) !important; }
"""

SIDEBAR_CSS = CUSTOM_CSS
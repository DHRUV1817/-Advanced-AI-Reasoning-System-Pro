"""
CSS styles for the Gradio interface
"""

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
:root {
    --bg-primary: #0a0c0f;
    --bg-secondary: #161b22;
    --bg-tertiary: #21262d;
    --bg-card: #161b22;
    --bg-accent: #1f2426;
    --text-primary: #ffffff;
    --text-secondary: #f0f6fc;
    --text-tertiary: #c9d1d9;
    --text-muted: #8b949e;
    --text-accent: #58a6ff;
    --accent-primary: #8b5cf6;
    --accent-secondary: #6366f1;
    --accent-gradient: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
    --border-color: #cbd5e1;
    --border-light: #e2e8f0;
    --shadow-dark: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-medium: 0 2px 4px rgba(0, 0, 0, 0.08);
    --shadow-light: 0 1px 2px rgba(0, 0, 0, 0.05);
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
    line-height: 1.5 !important;
    font-size: 14px !important;
    font-weight: 400 !important;
}

* {
    color: var(--text-primary) !important;
}

/* ==================== BEAUTIFUL TYPOGRAPHY ==================== */

/* Headlines */
.gr-markdown h1,
h1 {
    font-family: 'Space Grotesk', 'Inter', sans-serif !important;
    font-size: 2.25rem !important;
    font-weight: 700 !important;
    line-height: 1.2 !important;
    letter-spacing: -0.025em !important;
    color: var(--text-primary) !important;
    margin-bottom: 1rem !important;
}

.gr-markdown h2,
h2 {
    font-family: 'Space Grotesk', 'Inter', sans-serif !important;
    font-size: 1.875rem !important;
    font-weight: 600 !important;
    line-height: 1.3 !important;
    letter-spacing: -0.02em !important;
    color: var(--text-primary) !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.75rem !important;
}

.gr-markdown h3,
h3 {
    font-family: 'Space Grotesk', 'Inter', sans-serif !important;
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    line-height: 1.4 !important;
    letter-spacing: -0.015em !important;
    color: var(--text-primary) !important;
    margin-top: 1.25rem !important;
    margin-bottom: 0.75rem !important;
}

.gr-markdown h4,
h4 {
    font-family: 'Inter', sans-serif !important;
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    line-height: 1.4 !important;
    letter-spacing: -0.01em !important;
    color: var(--text-primary) !important;
    margin-bottom: 0.5rem !important;
}

/* Body text */
.gr-markdown p,
p {
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    font-weight: 400 !important;
    line-height: 1.6 !important;
    color: var(--text-secondary) !important;
    margin-bottom: 1rem !important;
}

/* Small text */
.gr-markdown small,
small {
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    line-height: 1.5 !important;
    color: var(--text-tertiary) !important;
}

/* Code and monospace */
.gr-markdown code,
code {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    background: var(--bg-secondary) !important;
    color: var(--text-accent) !important;
    padding: 0.125rem 0.375rem !important;
    border-radius: 4px !important;
    border: 1px solid var(--border-color) !important;
}

.gr-markdown pre code,
pre code {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
}

/* Blockquotes */
.gr-markdown blockquote,
blockquote {
    font-family: 'Inter', sans-serif !important;
    font-size: 16px !important;
    font-weight: 500 !important;
    font-style: italic !important;
    line-height: 1.5 !important;
    color: var(--text-tertiary) !important;
    border-left: 4px solid var(--accent-primary) !important;
    padding-left: 1rem !important;
    margin: 1.5rem 0 !important;
    background: rgba(139, 92, 246, 0.05) !important;
    padding: 1rem 1.5rem !important;
    border-radius: 0 8px 8px 0 !important;
}

/* Lists */
.gr-markdown ul,
.gr-markdown ol,
ul, ol {
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
    color: var(--text-secondary) !important;
}

.gr-markdown li,
li {
    margin-bottom: 0.5rem !important;
}

/* Links */
.gr-markdown a,
a {
    font-family: 'Inter', sans-serif !important;
    color: var(--text-accent) !important;
    font-weight: 500 !important;
    text-decoration: none !important;
    transition: all 0.2s ease !important;
    border-bottom: 1px solid transparent !important;
}

.gr-markdown a:hover,
a:hover {
    color: var(--accent-primary) !important;
    border-bottom-color: var(--accent-primary) !important;
}

/* Emphasized text */
.gr-markdown strong,
.gr-markdown b,
strong, b {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
}

.gr-markdown em,
.gr-markdown i,
em, i {
    font-family: 'Inter', sans-serif !important;
    font-style: italic !important;
    color: var(--text-secondary) !important;
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
    height: 4px;
    background: var(--accent-gradient);
    animation: shimmer 3s infinite;
}

@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}

.header-branding {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    margin-bottom: 2rem !important;
    flex-wrap: wrap !important;
    gap: 1rem !important;
}

.logo-section {
    display: flex !important;
    align-items: center !important;
    gap: 1.5rem !important;
}

.logo-circle {
    width: 3.5rem !important;
    height: 3.5rem !important;
    border-radius: 50% !important;
    background: var(--accent-gradient) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 1.5rem !important;
    box-shadow: var(--shadow-dark) !important;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

.brand-text h1 {
    font-family: 'Space Grotesk', 'Inter', sans-serif !important;
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    margin: 0 !important;
    color: var(--text-primary) !important;
    -webkit-font-smoothing: antialiased !important;
    -moz-osx-font-smoothing: grayscale !important;
    text-rendering: optimizeLegibility !important;
    letter-spacing: -0.01em !important;
    line-height: 1.1 !important;
    border: 2px solid transparent !important;
    border-image: linear-gradient(135deg, rgba(139, 92, 246, 0.6), rgba(99, 102, 241, 0.6)) 1 !important;
    padding: 0.2rem 0.5rem !important;
    background: rgba(139, 92, 246, 0.08) !important;
    border-radius: 12px !important;
}

.brand-tagline {
    font-size: 0.95rem !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    letter-spacing: 0.5px !important;
}

.status-indicator {
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
    padding: 0.5rem 1rem !important;
    background: rgba(16, 185, 129, 0.1) !important;
    border: 1px solid rgba(16, 185, 129, 0.2) !important;
    border-radius: 20px !important;
}

.status-dot {
    width: 8px !important;
    height: 8px !important;
    background: var(--success) !important;
    border-radius: 50% !important;
    animation: pulse-green 2s infinite;
}

@keyframes pulse-green {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.status-text {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: var(--success) !important;
    letter-spacing: 0.5px !important;
}

.header-subtitle {
    margin-bottom: 2rem !important;
}

.header-subtitle p {
    font-size: 1.1rem !important;
    color: var(--text-secondary) !important;
    line-height: 1.6 !important;
    margin: 0 !important;
}

.header-subtitle strong {
    color: var(--accent-primary) !important;
}

.feature-badges {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 0.75rem !important;
}

.feature-badge {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%) !important;
    border: 1px solid rgba(139, 92, 246, 0.25) !important;
    color: var(--accent-primary) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.6rem 1.2rem !important;
    border-radius: 25px !important;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative !important;
    overflow: hidden !important;
    cursor: pointer !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.3px !important;
    backdrop-filter: blur(10px) !important;
}

.feature-badge::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent) !important;
    transition: left 0.6s !important;
}

.feature-badge:hover::before {
    left: 100% !important;
}

.feature-badge:hover {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(99, 102, 241, 0.15) 100%) !important;
    border-color: rgba(139, 92, 246, 0.4) !important;
    color: var(--accent-secondary) !important;
    transform: translateY(-3px) !important;
    box-shadow:
        0 10px 25px rgba(139, 92, 246, 0.2),
        0 0 20px rgba(139, 92, 246, 0.1) !important;
    text-shadow: 0 0 8px rgba(139, 92, 246, 0.3) !important;
}

.feature-badge:active {
    transform: translateY(-1px) scale(0.98) !important;
    box-shadow:
        0 5px 15px rgba(139, 92, 246, 0.15),
        0 0 10px rgba(139, 92, 246, 0.1) !important;
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

/* ==================== ENHANCED ANALYTICS WELCOME ==================== */

.analytics-panel-welcome {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--border-radius-lg) !important;
    padding: 3rem !important;
    box-shadow: var(--shadow-dark) !important;
    text-align: center !important;
    position: relative !important;
    overflow: hidden !important;
}

.analytics-panel-welcome::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: var(--accent-gradient);
    animation: shimmer 4s infinite;
}

.analytics-header {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 1rem !important;
    margin-bottom: 2rem !important;
}

.analytics-icon {
    font-size: 3rem !important;
    animation: bounce-in 1s ease-out;
}

@keyframes bounce-in {
    0% { transform: scale(0) rotate(-45deg); opacity: 0; }
    50% { transform: scale(1.1) rotate(-5deg); opacity: 0.7; }
    100% { transform: scale(1) rotate(0deg); opacity: 1; }
}

.analytics-text h3 {
    font-size: 2rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    background: var(--accent-gradient);
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
}

.analytics-subtitle {
    font-size: 1.1rem !important;
    color: var(--text-secondary) !important;
    margin: 0.5rem 0 0 0 !important;
    font-weight: 500 !important;
}

.analytics-placeholder {
    max-width: 600px !important;
    margin: 0 auto !important;
}

.placeholder-icon {
    font-size: 4rem !important;
    margin-bottom: 1.5rem !important;
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
}

.analytics-placeholder h4 {
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    margin-bottom: 1rem !important;
}

.analytics-placeholder p {
    font-size: 1.1rem !important;
    line-height: 1.6 !important;
    color: var(--text-secondary) !important;
    margin-bottom: 2rem !important;
}

.metrics-preview {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)) !important;
    gap: 1rem !important;
    margin: 2.5rem 0 !important;
}

.metric-item {
    display: flex !important;
    align-items: center !important;
    gap: 0.75rem !important;
    padding: 1rem !important;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%) !important;
    border: 1px solid rgba(139, 92, 246, 0.1) !important;
    border-radius: var(--border-radius) !important;
    transition: all 0.3s ease !important;
}

.metric-item:hover {
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-medium) !important;
    border-color: rgba(139, 92, 246, 0.3) !important;
}

.metric-emoji {
    font-size: 1.5rem !important;
}

.metric-label {
    font-weight: 500 !important;
    color: var(--text-primary) !important;
}

.get-started {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0.75rem !important;
    margin-top: 2rem !important;
    padding: 1rem !important;
    background: rgba(16, 185, 129, 0.1) !important;
    border: 1px solid rgba(16, 185, 129, 0.2) !important;
    border-radius: var(--border-radius) !important;
}

.arrow-icon {
    font-size: 1.5rem !important;
    animation: bounce 2s infinite;
}

@keyframes bounce {
    0%, 20%, 53%, 80%, 100% { transform: translate3d(0,0,0); }
    40%, 43% { transform: translate3d(0,-8px,0); }
    70% { transform: translate3d(0,-4px,0); }
    90% { transform: translate3d(0,-2px,0); }
}

.get-started span {
    font-weight: 600 !important;
    color: var(--success) !important;
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

/* ==================== ENHANCED TABS ==================== */

.gr-tabs {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--border-radius-lg) !important;
    box-shadow: var(--shadow-medium) !important;
    margin-bottom: 2rem !important;
    overflow: hidden !important;
}

.gr-tabs .tab-nav {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%) !important;
    border-bottom: 1px solid var(--border-color) !important;
    padding: 0 !important;
}

.gr-tabs .tab-nav button {
    background: transparent !important;
    border: none !important;
    padding: 1.25rem 1.5rem !important;
    margin: 0 !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    position: relative !important;
    transition: all 0.3s ease !important;
    border-radius: 0 !important;
    font-family: 'Inter', sans-serif !important;
    min-width: 180px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0.5rem !important;
}

.gr-tabs .tab-nav button:hover {
    background: rgba(139, 92, 246, 0.1) !important;
    color: var(--accent-primary) !important;
}

.gr-tabs .tab-nav button.selected {
    background: var(--accent-gradient) !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
}

.gr-tabs .tab-nav button.selected::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 20%;
    right: 20%;
    height: 3px;
    background: currentColor;
    border-radius: 2px;
}

.gr-tabs .tab-content {
    padding: 2rem !important;
    background: var(--bg-card) !important;
}

/* Tab-specific styling for better visual hierarchy */
.tab-content .gr-markdown h2,
.tab-content .gr-markdown h3 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    margin-top: 2rem !important;
    margin-bottom: 1rem !important;
}

.tab-content .gr-markdown h2 {
    font-size: 1.4rem !important;
}

.tab-content .gr-markdown h3 {
    font-size: 1.2rem !important;
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

    .brand-text h1 {
        font-size: 2.2rem !important;
    }

    .header-branding {
        flex-direction: column !important;
        text-align: center !important;
        gap: 1.5rem !important;
    }

    .logo-section {
        justify-content: center !important;
    }

    .status-indicator {
        margin: 0 auto !important;
    }

    .feature-badges {
        justify-content: center !important;
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
    .research-header {
        padding: 1.5rem 1rem !important;
    }

    .brand-text h1 {
        font-size: 1.8rem !important;
        line-height: 1.2 !important;
    }

    .brand-tagline {
        font-size: 0.9rem !important;
    }

    .header-subtitle p {
        font-size: 1rem !important;
    }

    .logo-circle {
        width: 3rem !important;
        height: 3rem !important;
    }

    .feature-badges {
        gap: 0.5rem !important;
    }

    .feature-badge {
        font-size: 0.8rem !important;
        padding: 0.5rem 1rem !important;
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

/* ==================== FINAL POLISH ==================== */

.gr-chatbot .message {
    border-radius: var(--border-radius) !important;
    box-shadow: var(--shadow-light) !important;
    border: 1px solid var(--border-light) !important;
    margin: 0.75rem 0 !important;
}

.gr-chatbot .message.user {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.03) 0%, rgba(99, 102, 241, 0.03) 100%) !important;
    border-color: rgba(139, 92, 246, 0.15) !important;
}

.gr-chatbot .message.bot {
    background: var(--bg-card) !important;
    border-color: var(--border-color) !important;
}

/* Enhanced spacing and typography */
.gr-column {
    margin-bottom: 1rem !important;
}

/* Subtle background pattern for empty states */
.analytics-panel-welcome::after {
    content: '';
    position: absolute;
    top: 20%;
    right: 10%;
    width: 60px;
    height: 60px;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.1) 0%, transparent 70%);
    border-radius: 50%;
    z-index: -1;
}

.analytics-panel-welcome::before {
    background: var(--accent-gradient) !important;
}

/* Professional logo background pattern */
.research-header::after {
    content: '';
    position: absolute;
    top: 50%;
    right: 5%;
    width: 150px;
    height: 150px;
    background: radial-gradient(ellipse, rgba(139, 92, 246, 0.05) 0%, transparent 70%);
    transform: translateY(-50%);
    border-radius: 50%;
    z-index: -1;
}
"""

SIDEBAR_CSS = CUSTOM_CSS

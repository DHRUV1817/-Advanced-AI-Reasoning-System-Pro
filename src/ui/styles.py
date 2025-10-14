"""
CSS styles for the Gradio interface
"""

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    --shadow-lg: 0 10px 40px rgba(0,0,0,0.15);
    --border-radius: 16px;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ==================== HEADER ==================== */

.research-header {
    background: var(--primary-gradient);
    padding: 3rem 2.5rem;
    border-radius: var(--border-radius);
    color: white;
    margin-bottom: 2rem;
    box-shadow: var(--shadow-lg);
    animation: slideDown 0.6s ease-out;
}

.research-header h1 { 
    font-size: 2.5rem; 
    font-weight: 800; 
    margin-bottom: 1rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.badge {
    background: rgba(255,255,255,0.25);
    backdrop-filter: blur(10px);
    color: white;
    padding: 0.5rem 1.2rem;
    border-radius: 25px;
    font-size: 0.9rem;
    margin: 0.3rem;
    display: inline-block;
    transition: var(--transition);
    border: 1px solid rgba(255,255,255,0.2);
}

.badge:hover {
    transform: translateY(-2px);
    background: rgba(255,255,255,0.35);
}

/* ==================== METRICS CARD ==================== */

.metrics-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    border-left: 5px solid #667eea;
    padding: 1.8rem;
    border-radius: var(--border-radius);
    margin: 1rem 0;
    font-family: 'JetBrains Mono', monospace;
    transition: var(--transition);
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    color: #2c3e50 !important;
}

.metrics-card * {
    color: #2c3e50 !important;
}

.metrics-card strong {
    color: #1a202c !important;
    font-weight: 700 !important;
}

.metrics-card:hover {
    transform: translateX(5px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}

/* ==================== ANALYTICS PANEL ==================== */

.analytics-panel {
    background: var(--success-gradient);
    color: white;
    padding: 2rem;
    border-radius: var(--border-radius);
    animation: fadeIn 0.5s ease-out;
    box-shadow: var(--shadow-lg);
}

.analytics-panel * {
    color: white !important;
}

.analytics-panel h3 {
    margin-bottom: 1rem;
    font-size: 1.5rem;
}

.analytics-panel p {
    line-height: 1.6;
}

.analytics-panel strong {
    font-weight: 600;
}

/* ==================== STATUS INDICATORS ==================== */

.status-active { 
    color: #10b981 !important; 
    font-weight: bold; 
    animation: pulse 2s infinite;
    text-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
}

/* ==================== ANIMATIONS ==================== */

@keyframes slideDown {
    from { opacity: 0; transform: translateY(-30px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeIn {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

/* ==================== GLOBAL STYLES ==================== */

.gradio-container { 
    font-family: 'Inter', sans-serif !important;
    max-width: 1600px !important;
}

.gr-button { 
    transition: var(--transition) !important; 
}

.gr-button:hover { 
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
}

/* ==================== MARKDOWN TEXT FIX ==================== */

.gr-markdown .metrics-card {
    color: #2c3e50 !important;
}

.gr-markdown .metrics-card p {
    color: #2c3e50 !important;
    margin: 0.25rem 0 !important;
}

.gr-markdown .metrics-card span {
    color: #2c3e50 !important;
}

/* ==================== SIDEBAR TOGGLE ==================== */

.sidebar-hidden {
    display: none !important;
}

.toggle-btn {
    position: fixed;
    right: 20px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 1000;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    transition: all 0.3s ease;
    font-size: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.toggle-btn:hover {
    transform: translateY(-50%) scale(1.1);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.settings-column {
    transition: all 0.3s ease-in-out;
}

.fullscreen-chat .gradio-container {
    max-width: 98% !important;
}

/* ==================== RESPONSIVE DESIGN ==================== */

@media (max-width: 768px) {
    .research-header h1 {
        font-size: 1.8rem;
    }
    
    .badge {
        font-size: 0.75rem;
        padding: 0.4rem 0.8rem;
    }
    
    .toggle-btn {
        width: 40px;
        height: 40px;
        font-size: 16px;
        right: 10px;
    }
    
    .metrics-card {
        padding: 1.2rem;
        font-size: 0.9rem;
    }
}

/* ==================== DARK MODE SUPPORT ==================== */

@media (prefers-color-scheme: dark) {
    .metrics-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: #e2e8f0 !important;
    }
    
    .metrics-card * {
        color: #e2e8f0 !important;
    }
    
    .metrics-card strong {
        color: #f1f5f9 !important;
    }
}

/* ==================== LOADING SPINNER ==================== */

.loading-spinner {
    border: 3px solid #f3f3f3;
    border-top: 3px solid #667eea;
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
"""

SIDEBAR_CSS = CUSTOM_CSS

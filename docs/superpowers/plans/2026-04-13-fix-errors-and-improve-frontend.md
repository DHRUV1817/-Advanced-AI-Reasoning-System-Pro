# Fix Errors & Improve Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all runtime errors preventing the app from starting, then improve the frontend color scheme and visual polish while keeping the same layout.

**Architecture:** The app is a Gradio-based Python project using Groq API for LLM reasoning. The UI is defined in `src/ui/app.py` with CSS in `src/ui/styles.py`. The main runtime issues are: (1) `requirements.txt` pins `gradio==5.6.0` but `6.2.0` is installed, (2) the `handle_groq_errors` retry decorator doesn't work with generator functions (streaming), (3) the `main.py` launch call passes CSS via a `css=` kwarg but the `create_ui()` function already wraps everything in `gr.Blocks`. Frontend improvements focus on a refined color palette with better contrast and more modern accents.

**Tech Stack:** Python 3.9+, Gradio 6.2.0, Groq SDK, ReportLab (PDF)

**Branch:** All work on `fix-and-improve-ui` branch (not main)

---

### Task 1: Create feature branch

**Files:**
- None (git operation only)

- [ ] **Step 1: Create and switch to new branch**

```bash
git checkout -b fix-and-improve-ui
```

- [ ] **Step 2: Verify branch**

```bash
git branch --show-current
```

Expected: `fix-and-improve-ui`

---

### Task 2: Fix requirements.txt Gradio version mismatch

The installed Gradio is 6.2.0, but `requirements.txt` pins `gradio==5.6.0`. This causes deployment failures.

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Update requirements.txt**

Change line 2 from:
```
gradio==5.6.0
```
to:
```
gradio>=5.6.0
```

This allows both 5.x and 6.x to satisfy the requirement, which is important since the code is already compatible with 6.x and the local install is 6.2.0. HF Spaces can pick the version it supports.

- [ ] **Step 2: Verify no import errors**

Run: `cd "D:/-Advanced-AI-Reasoning-System-Pro" && python -c "import gradio; print(gradio.__version__)"`
Expected: `6.2.0` (no errors)

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "fix: allow flexible gradio version in requirements"
```

---

### Task 3: Fix handle_groq_errors decorator for generator functions

The `handle_groq_errors` decorator in `src/utils/decorators.py` uses `return func(*args, **kwargs)` which returns the generator object without executing it. The retry logic never fires because exceptions are raised during iteration, not during the call. The `_call_groq_api` method in `reasoner.py` is a generator (uses `yield`), so the decorator must handle generators properly.

**Files:**
- Modify: `src/utils/decorators.py:11-56`

- [ ] **Step 1: Update the decorator to handle generators**

Replace the `handle_groq_errors` function with a version that detects generators and wraps iteration:

```python
import inspect

def handle_groq_errors(max_retries: int = 3, retry_delay: float = 1.0) -> Callable:
    """
    Groq API error handler with exponential backoff.
    Supports both regular functions and generator functions.
    """
    def decorator(func: Callable) -> Callable:
        if inspect.isgeneratorfunction(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_retries):
                    try:
                        yield from func(*args, **kwargs)
                        return
                    except groq.RateLimitError as e:
                        last_exception = e
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit. Waiting {wait_time:.1f}s... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    except groq.APIConnectionError as e:
                        last_exception = e
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"Connection error. Retrying in {wait_time:.1f}s... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    except groq.AuthenticationError as e:
                        logger.error(f"Authentication failed: {e}")
                        raise ValueError("Invalid GROQ_API_KEY. Please check your API key.") from e
                    except groq.BadRequestError as e:
                        logger.error(f"Invalid request: {e}")
                        raise ValueError(f"Invalid request parameters: {str(e)}") from e
                    except Exception as e:
                        last_exception = e
                        logger.error(f"Unexpected error: {e}", exc_info=True)
                        if attempt == max_retries - 1:
                            break
                        time.sleep(retry_delay * (2 ** attempt))
                error_msg = f"Failed after {max_retries} attempts: {str(last_exception)}"
                logger.error(error_msg)
                raise Exception(error_msg) from last_exception
        else:
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except groq.RateLimitError as e:
                        last_exception = e
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit. Waiting {wait_time:.1f}s... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    except groq.APIConnectionError as e:
                        last_exception = e
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"Connection error. Retrying in {wait_time:.1f}s... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    except groq.AuthenticationError as e:
                        logger.error(f"Authentication failed: {e}")
                        raise ValueError("Invalid GROQ_API_KEY. Please check your API key.") from e
                    except groq.BadRequestError as e:
                        logger.error(f"Invalid request: {e}")
                        raise ValueError(f"Invalid request parameters: {str(e)}") from e
                    except Exception as e:
                        last_exception = e
                        logger.error(f"Unexpected error: {e}", exc_info=True)
                        if attempt == max_retries - 1:
                            break
                        time.sleep(retry_delay * (2 ** attempt))
                error_msg = f"Failed after {max_retries} attempts: {str(last_exception)}"
                logger.error(error_msg)
                raise Exception(error_msg) from last_exception
        return wrapper
    return decorator
```

Also add `import inspect` at the top of the file (line 4).

- [ ] **Step 2: Verify the decorator works with a generator**

Run: `cd "D:/-Advanced-AI-Reasoning-System-Pro" && python -c "
from src.utils.decorators import handle_groq_errors
@handle_groq_errors(max_retries=1)
def gen():
    yield 'hello'
    yield 'world'
print(list(gen()))
"`

Expected: `['hello', 'world']`

- [ ] **Step 3: Commit**

```bash
git add src/utils/decorators.py
git commit -m "fix: handle_groq_errors now supports generator functions for streaming"
```

---

### Task 4: Fix main.py launch to not pass duplicate CSS/theme

The `main.py` creates a `gr.Blocks()` in `create_ui()` and then calls `demo.launch()` with `theme=` and `css=` kwargs. In Gradio 6.x, the theme and css should be set on `gr.Blocks()`, not on `launch()`. The `launch()` method in Gradio 6.x does not accept `css` or `theme` parameters.

**Files:**
- Modify: `main.py:25-47`
- Modify: `src/ui/app.py:25-27`

- [ ] **Step 1: Move theme and CSS into gr.Blocks() in app.py**

In `src/ui/app.py`, change the `gr.Blocks()` constructor (line 25-27) from:

```python
    with gr.Blocks(
        title="Advanced AI Reasoning System Pro"
    ) as demo:
```

to:

```python
    import gradio as gr
    
    theme = gr.themes.Soft(
        primary_hue="purple",
        secondary_hue="blue",
        font=gr.themes.GoogleFont("Inter")
    )
    
    with gr.Blocks(
        title="Advanced AI Reasoning System Pro",
        theme=theme,
        css=SIDEBAR_CSS
    ) as demo:
```

- [ ] **Step 2: Simplify main.py launch call**

In `main.py`, replace the `demo.launch(...)` block (lines 34-47) with:

```python
        demo.launch(
            share=False,
            server_name="127.0.0.1",
            server_port=7860,
            show_error=True,
            max_threads=AppConfig.MAX_WORKERS
        )
```

Also remove the unused import `from src.ui.styles import SIDEBAR_CSS` (line 33).

- [ ] **Step 3: Verify the app starts without errors**

Run: `cd "D:/-Advanced-AI-Reasoning-System-Pro" && timeout 10 python main.py 2>&1 || true`

Expected: Gradio server starts on 127.0.0.1:7860 (may fail with API key error but should not crash on launch params)

- [ ] **Step 4: Commit**

```bash
git add main.py src/ui/app.py
git commit -m "fix: move theme and CSS to gr.Blocks constructor for Gradio 6.x"
```

---

### Task 5: Improve CSS color scheme and visual polish

Enhance the dark theme color palette for a more modern, attractive look. Keep the same layout and structure. Focus on:
- Richer gradient accents (teal/cyan highlights alongside purple)
- Better contrast between card backgrounds and the page
- More refined border colors
- Improved button styling with gradient backgrounds
- Better chatbot message styling

**Files:**
- Modify: `src/ui/styles.py:1-30` (CSS variables)
- Modify: `src/ui/styles.py` (button, chatbot, card sections)

- [ ] **Step 1: Update CSS variables for improved color palette**

Replace the `:root` CSS variables block (lines 8-32 of CUSTOM_CSS) with:

```css
:root {
    --bg-primary: #0b0d12;
    --bg-secondary: #131720;
    --bg-tertiary: #1a1f2e;
    --bg-card: #151a27;
    --bg-accent: #1c2235;
    --text-primary: #f0f2f5;
    --text-secondary: #d1d5db;
    --text-tertiary: #9ca3af;
    --text-muted: #6b7280;
    --text-accent: #67e8f9;
    --accent-primary: #a78bfa;
    --accent-secondary: #818cf8;
    --accent-tertiary: #22d3ee;
    --accent-gradient: linear-gradient(135deg, #a78bfa 0%, #818cf8 50%, #22d3ee 100%);
    --accent-gradient-hover: linear-gradient(135deg, #c4b5fd 0%, #a5b4fc 50%, #67e8f9 100%);
    --success: #34d399;
    --warning: #fbbf24;
    --error: #f87171;
    --border-color: rgba(148, 163, 184, 0.15);
    --border-light: rgba(148, 163, 184, 0.08);
    --border-accent: rgba(167, 139, 250, 0.3);
    --shadow-dark: 0 4px 24px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(148, 163, 184, 0.05);
    --shadow-medium: 0 2px 12px rgba(0, 0, 0, 0.2);
    --shadow-light: 0 1px 4px rgba(0, 0, 0, 0.1);
    --shadow-glow: 0 0 20px rgba(167, 139, 250, 0.15);
    --border-radius: 12px;
    --border-radius-lg: 16px;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

- [ ] **Step 2: Update header styling for gradient accent bar**

Replace the `.research-header` rule to use the new accent gradient. Replace the `background` property:

```css
.research-header {
    background: linear-gradient(180deg, var(--bg-card) 0%, var(--bg-secondary) 100%) !important;
    border: 1px solid var(--border-color) !important;
    padding: 2.5rem 2rem !important;
    border-radius: var(--border-radius-lg) !important;
    margin-bottom: 2rem !important;
    box-shadow: var(--shadow-dark) !important;
    position: relative;
    overflow: hidden;
}
```

- [ ] **Step 3: Update button styling with gradient backgrounds**

Replace the `.gr-button` rules with:

```css
.gr-button {
    background: var(--accent-gradient) !important;
    color: white !important;
    border: none !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: var(--transition) !important;
    box-shadow: var(--shadow-medium) !important;
    letter-spacing: 0.3px !important;
}

.gr-button:hover {
    background: var(--accent-gradient-hover) !important;
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-glow), var(--shadow-dark) !important;
}

.gr-button:active {
    transform: translateY(0) !important;
    box-shadow: var(--shadow-medium) !important;
}
```

- [ ] **Step 4: Update chatbot message styling**

Replace the `.gr-chatbot .message` rules at the bottom with:

```css
.gr-chatbot .message {
    border-radius: var(--border-radius) !important;
    box-shadow: var(--shadow-light) !important;
    border: 1px solid var(--border-color) !important;
    margin: 0.75rem 0 !important;
    padding: 1rem 1.25rem !important;
}

.gr-chatbot .message.user {
    background: linear-gradient(135deg, rgba(167, 139, 250, 0.08) 0%, rgba(129, 140, 248, 0.05) 100%) !important;
    border-color: rgba(167, 139, 250, 0.2) !important;
    border-left: 3px solid var(--accent-primary) !important;
}

.gr-chatbot .message.bot {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%) !important;
    border-color: var(--border-color) !important;
    border-left: 3px solid var(--accent-tertiary) !important;
}
```

- [ ] **Step 5: Update tab styling with refined appearance**

Replace the `.gr-tabs .tab-nav button.selected` rule with:

```css
.gr-tabs .tab-nav button.selected {
    background: var(--accent-gradient) !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(167, 139, 250, 0.3) !important;
}
```

- [ ] **Step 6: Update feature badge styling**

Replace `.feature-badge` background to use the new tertiary accent color:

In the `.feature-badge` rule, change:
```css
    color: var(--accent-primary) !important;
```

And in `.feature-badge:hover`, update the box-shadow to use the new colors:
```css
.feature-badge:hover {
    background: linear-gradient(135deg, rgba(167, 139, 250, 0.15) 0%, rgba(34, 211, 238, 0.1) 100%) !important;
    border-color: rgba(167, 139, 250, 0.4) !important;
    color: var(--accent-tertiary) !important;
    transform: translateY(-3px) !important;
    box-shadow:
        0 10px 25px rgba(167, 139, 250, 0.2),
        0 0 20px rgba(34, 211, 238, 0.1) !important;
}
```

- [ ] **Step 7: Update metrics card with glow on hover**

Replace `.metrics-card:hover`:
```css
.metrics-card:hover {
    border-color: var(--accent-primary) !important;
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-glow), var(--shadow-dark) !important;
}
```

- [ ] **Step 8: Update input field styling**

Replace `.gr-input:focus, .gr-textbox:focus, .gr-dropdown:focus`:
```css
.gr-input:focus, .gr-textbox:focus, .gr-dropdown:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 2px rgba(167, 139, 250, 0.2), var(--shadow-glow) !important;
    outline: none !important;
}
```

- [ ] **Step 9: Run the app and verify visually**

Run: `cd "D:/-Advanced-AI-Reasoning-System-Pro" && timeout 15 python main.py 2>&1 || true`

Open http://127.0.0.1:7860 in browser. Verify:
- Header gradient bar displays correctly
- Feature badges have purple-to-cyan gradient on hover
- Buttons show gradient styling
- Chat messages have left border accents
- Tabs have gradient when selected
- Cards glow on hover
- Overall dark theme looks cohesive with improved contrast

- [ ] **Step 10: Commit**

```bash
git add src/ui/styles.py
git commit -m "feat: improve dark theme with refined color palette and gradient accents"
```

---

### Task 6: Update header HTML component colors

Update the components HTML to reference the new accent colors in inline styles.

**Files:**
- Modify: `src/ui/components.py:59-60`

- [ ] **Step 1: Update metrics status active color**

In `src/ui/components.py`, line 59, the status active indicator uses a hardcoded color. Change:

```python
            status = '<span class="status-active">● Active</span>'
```

This is already using a CSS class, so no change needed here. The CSS class `.status-active` uses `var(--success)` which is now `#34d399`. This is fine.

Verify the component HTML doesn't use any hardcoded colors that conflict. (It doesn't - all colors come from CSS classes.)

- [ ] **Step 2: Commit (skip if no changes)**

No changes needed - components already use CSS classes properly.

---

### Task 7: Final verification and test

**Files:** None (verification only)

- [ ] **Step 1: Run a full import check**

Run: `cd "D:/-Advanced-AI-Reasoning-System-Pro" && python -c "from src.ui.app import create_ui; print('UI imports OK')"`

Expected: `UI imports OK`

- [ ] **Step 2: Run the app**

Run: `cd "D:/-Advanced-AI-Reasoning-System-Pro" && python main.py`

Open http://127.0.0.1:7860 in browser. Verify the app loads with the improved styling.

- [ ] **Step 3: Test chat interaction**

Type a question in the chat box and click "Process". Verify:
- Message appears in chatbot with correct styling
- Streaming response works
- Metrics update in sidebar
- No console errors

If the GROQ_API_KEY is invalid, the app should show a clear error message in the chat (not crash).

- [ ] **Step 4: Final commit if needed**

```bash
git status
# If there are any remaining changes:
git add -A
git commit -m "chore: final cleanup"
```

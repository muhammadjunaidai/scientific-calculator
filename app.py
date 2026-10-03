import html

import streamlit as st

st.set_page_config(page_title="Scientific Calculator", page_icon="🧮", layout="centered")

# =========================================================
# 1. BUTTON LAYOUT
# =========================================================

SCIENTIFIC = [
    "sin", "cos", "tan", "cot",
    "sec", "csc", "sinh", "cosh",
    "tanh", "sin⁻¹", "cos⁻¹", "tan⁻¹",
    "log", "ln", "log₂", "10ˣ",
    "eˣ", "√", "∛", "x²",
    "x³", "xʸ", "1/x", "n!",
    "|x|", "EXP", "Ans", "mod",
]

KEYBOARD = [
    "AC", "⌫", "(", ")",
    "7", "8", "9", "÷",
    "4", "5", "6", "×",
    "1", "2", "3", "−",
    "0", ".", "π", "+",
    "±", "%", "e", "00",
]

OPERATORS = {"÷", "×", "−", "+", "%", "mod", "xʸ"}
TRIG = {"sin", "cos", "tan", "cot", "sec", "csc", "sinh", "cosh", "tanh",
        "sin⁻¹", "cos⁻¹", "tan⁻¹"}


def category(label):
    """Button type -> decides its look (see CSS section)."""
    if label == "AC":
        return "clr"
    if label == "⌫":
        return "bk"
    if label == "=":
        return "eq"
    if label in OPERATORS:
        return "op"
    if label.isdigit() or label == ".":
        return "num"
    if label in TRIG:
        return "tr"
    return "fn"


# =========================================================
# 2. DUMMY DISPLAY VALUES
# =========================================================

DUMMY_EXPRESSION = "tan(45) ="
DUMMY_RESULT = "1"


# =========================================================
# 3. STYLES
# =========================================================

CSS = """
<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap");

:root {
    --ink: #0f172a;
    --muted: #64748b;
    --accent: #2563eb;
    --accent-dark: #1d4ed8;
    --ui-font: Inter, "Segoe UI", system-ui, -apple-system, Roboto, sans-serif;
    --mono-font: "JetBrains Mono", "SF Mono", Consolas, "Courier New", monospace;
}

/* ---------- page ---------- */
.stApp {
    background:
        radial-gradient(900px 420px at 50% -8%, rgba(59, 130, 246, 0.16), transparent 62%),
        linear-gradient(180deg, #eef2f8 0%, #e1e7f0 100%);
    background-attachment: fixed;
    color: var(--ink);
    color-scheme: light;
    font-family: var(--ui-font);
}
.stApp p, .stApp button, .stApp label { font-family: var(--ui-font); }
header[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stDecoration"], #MainMenu, footer { display: none !important; }
.block-container { max-width: 960px; padding: 2.4rem 1rem 2.4rem; }

/* ---------- header ---------- */
.app-header { text-align: center; margin-bottom: 1.5rem; }
.app-logo {
    width: 54px; height: 54px; margin: 0 auto 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; border-radius: 16px;
    background: linear-gradient(145deg, #ffffff, #e8efff);
    box-shadow: 0 1px 0 #fff inset, 0 10px 22px -6px rgba(37, 99, 235, 0.35), 0 0 0 1px rgba(37, 99, 235, 0.10);
}
.app-title {
    display: inline-block;
    font-size: 30px; font-weight: 700; letter-spacing: -0.6px; line-height: 1.15;
    background: linear-gradient(90deg, #0f172a 20%, #2563eb 100%);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent; color: transparent;
}
.app-subtitle {
    margin-top: 8px; font-size: 11.5px; font-weight: 500; color: var(--muted);
    text-transform: uppercase; letter-spacing: 2.2px;
}

/* ---------- display ---------- */
.calc-wrap { max-width: 1000px; margin: 0 auto; }
.calc-display {
    position: relative; box-sizing: border-box; overflow: hidden;
    height: 132px; padding: 14px 24px 14px;
    border-radius: 22px;
    background: linear-gradient(145deg, #0b1220 0%, #16213a 100%);
    border: 1px solid rgba(255, 255, 255, 0.06);
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.10),
        0 28px 44px -18px rgba(11, 18, 32, 0.60),
        0 4px 10px rgba(11, 18, 32, 0.18);
    display: flex; flex-direction: column; justify-content: space-between;
}
.calc-display::before {          /* glass sheen */
    content: ""; position: absolute; inset: 0; pointer-events: none;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.07), transparent 42%);
}
.calc-display::after {           /* soft accent glow */
    content: ""; position: absolute; inset: 0; pointer-events: none;
    background: radial-gradient(420px 160px at 100% 110%, rgba(59, 130, 246, 0.26), transparent 70%);
}
.calc-top, .calc-main { position: relative; z-index: 1; }
.calc-top { display: flex; align-items: center; justify-content: space-between; height: 24px; }
.calc-mode {
    font-size: 10.5px; font-weight: 600; letter-spacing: 1.4px;
    color: #bfdbfe; background: rgba(59, 130, 246, 0.20);
    border: 1px solid rgba(147, 197, 253, 0.25);
    padding: 3px 10px; border-radius: 999px;
}
.calc-expr {
    flex: 1; margin-left: 14px; overflow: hidden; white-space: nowrap;
    display: flex; justify-content: flex-end;
    font-family: var(--mono-font); font-size: 15px; color: #8fa0bd;
}
.calc-main {
    height: 62px; overflow: hidden; white-space: nowrap;
    display: flex; align-items: center; justify-content: flex-end;
    font-family: var(--mono-font); font-size: 42px; font-weight: 600; letter-spacing: -1px;
    color: #f8fafc; text-shadow: 0 0 22px rgba(96, 165, 250, 0.35);
}
.calc-main.md { font-size: 33px; }
.calc-main.sm { font-size: 25px; }

/* ---------- DEG / RAD switch ---------- */
.st-key-mode_switch { display: flex; justify-content: center; margin: 6px 0 10px; }
.st-key-mode_switch [role="radiogroup"] {
    background: rgba(15, 23, 42, 0.07); padding: 4px; border-radius: 999px;
    box-shadow: inset 0 1px 3px rgba(15, 23, 42, 0.12);
    gap: 2px !important; flex-wrap: nowrap !important;
}
.st-key-mode_switch label {
    margin: 0 !important; padding: 6px 26px; border-radius: 999px;
    cursor: pointer; transition: background 0.18s, box-shadow 0.18s;
}
.st-key-mode_switch label > div:not([data-testid="stMarkdownContainer"]):not(:has(p)) {
    display: none;   /* hides the round radio dot */
}
.st-key-mode_switch label p {
    margin: 0; font-size: 12.5px; font-weight: 600; letter-spacing: 1.2px; color: #64748b;
}
.st-key-mode_switch label:has(input:checked) {
    background: #ffffff;
    box-shadow: 0 1px 0 #fff inset, 0 3px 8px rgba(15, 23, 42, 0.16);
}
.st-key-mode_switch label:has(input:checked) p { color: var(--accent-dark); }

/* ---------- cards ---------- */
.st-key-card_sci, .st-key-card_key {
    background: linear-gradient(180deg, #ffffff 0%, #fafbfd 100%);
    border: 1px solid rgba(15, 23, 42, 0.06);
    border-radius: 24px;
    padding: 18px 16px 20px;
    box-shadow:
        inset 0 1px 0 #ffffff,
        0 22px 40px -16px rgba(15, 23, 42, 0.20),
        0 2px 6px rgba(15, 23, 42, 0.05);
}
.st-key-card_sci, .st-key-card_key,
.st-key-card_sci [data-testid="stVerticalBlock"],
.st-key-card_key [data-testid="stVerticalBlock"] { gap: 10px !important; }

.st-key-card_sci [data-testid="stHorizontalBlock"],
.st-key-card_key [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 9px !important; }
.st-key-card_sci [data-testid="stColumn"], .st-key-card_key [data-testid="stColumn"],
.st-key-card_sci [data-testid="column"],   .st-key-card_key [data-testid="column"] {
    min-width: 0 !important; width: auto !important; flex: 1 1 0 !important;
}

.card-title {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    font-size: 11.5px; font-weight: 700; color: var(--muted);
    text-transform: uppercase; letter-spacing: 2px;
    padding-bottom: 12px; margin-bottom: 2px;
    border-bottom: 1px solid #edf0f5;
}
.card-title .dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--accent); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}

/* ---------- buttons: keycap look (colours come from variables) ---------- */
[class*="st-key-btn_"] button {
    width: 100%; height: 44px; min-height: 44px; padding: 0;
    border-radius: 12px;
    background: linear-gradient(180deg, var(--k-top), var(--k-bot)) !important;
    color: var(--k-text) !important;
    border: 1px solid var(--k-border) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75), 0 2px 0 var(--k-edge), 0 7px 12px -4px rgba(15, 23, 42, 0.14);
    transition: transform 0.08s ease, box-shadow 0.12s ease, filter 0.12s ease;
}
[class*="st-key-btn_"] button p {
    margin: 0; font-size: 13px; font-weight: 500; letter-spacing: 0.1px; color: inherit !important;
}
[class*="st-key-btn_"] button:hover { transform: translateY(-1px); filter: brightness(0.975); }
[class*="st-key-btn_"] button:active {
    transform: translateY(2px); filter: brightness(0.95);
    box-shadow: inset 0 2px 4px rgba(15, 23, 42, 0.16), 0 0 0 var(--k-edge);
}
[class*="st-key-btn_"] button:focus:not(:active) {
    outline: none;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75), 0 2px 0 var(--k-edge), 0 0 0 3px rgba(37, 99, 235, 0.25);
}

/* functions (log, √, x², ...) */
[class*="st-key-btn_fn__"]  { --k-top:#ffffff; --k-bot:#f0f3f8; --k-edge:#d5dbe6; --k-border:#e1e6ee; --k-text:#3a4558; }
/* trigonometry group - tinted so it is easy to find */
[class*="st-key-btn_tr__"]  { --k-top:#f7f9ff; --k-bot:#e8eefc; --k-edge:#c8d4f2; --k-border:#d6dff6; --k-text:#35488a; }
/* digits */
[class*="st-key-btn_num__"] { --k-top:#ffffff; --k-bot:#f6f8fb; --k-edge:#cfd6e1; --k-border:#dfe4ec; --k-text:#0f172a; }
[class*="st-key-btn_num__"] button p { font-size: 17px; font-weight: 600; }
/* operators */
[class*="st-key-btn_op__"]  { --k-top:#f0f5ff; --k-bot:#dbe6ff; --k-edge:#b7ccf8; --k-border:#c5d6fb; --k-text:#1d4ed8; }
[class*="st-key-btn_op__"] button p { font-size: 17px; font-weight: 600; }
/* AC */
[class*="st-key-btn_clr__"] { --k-top:#fff3f3; --k-bot:#fddcdc; --k-edge:#efb3b3; --k-border:#f5c8c8; --k-text:#c62828; }
[class*="st-key-btn_clr__"] button p { font-size: 15px; font-weight: 700; }
/* backspace */
[class*="st-key-btn_bk__"]  { --k-top:#f3f5f8; --k-bot:#e3e7ee; --k-edge:#c8cfda; --k-border:#d4dae3; --k-text:#475569; }
[class*="st-key-btn_bk__"] button p { font-size: 17px; font-weight: 600; }
/* equals: the main action */
[class*="st-key-btn_eq__"]  { --k-top:#3b82f6; --k-bot:#1d4ed8; --k-edge:#1e3a8a; --k-border:#1d4ed8; --k-text:#ffffff; }
[class*="st-key-btn_eq__"] button {
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35), 0 2px 0 var(--k-edge), 0 12px 22px -6px rgba(37, 99, 235, 0.55);
}
[class*="st-key-btn_eq__"] button p { font-size: 21px; font-weight: 700; }

/* ---------- small screens ---------- */
@media (max-width: 640px) {
    .block-container { padding: 1.2rem 0.6rem 1.5rem; }
    .app-title { font-size: 25px; }
    .calc-display { height: 116px; padding: 12px 18px; }
    .calc-main { font-size: 34px; height: 52px; }
    .calc-main.md { font-size: 27px; }
    .calc-main.sm { font-size: 21px; }
    [class*="st-key-btn_"] button { height: 42px; min-height: 42px; }
    [class*="st-key-btn_"] button p { font-size: 12px; }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# =========================================================
# 4. UI COMPONENTS
# =========================================================

def render_header():
    st.markdown(
        '<div class="app-header">'
        '<div class="app-logo">🧮</div>'
        '<div class="app-title">Scientific Calculator</div>'
        '<div class="app-subtitle">Standard &amp; Scientific Mathematics</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_display(mode):
    size = "sm" if len(DUMMY_RESULT) >= 19 else "md" if len(DUMMY_RESULT) >= 12 else ""
    st.markdown(
        '<div class="calc-wrap"><div class="calc-display">'
        f'<div class="calc-top"><span class="calc-mode">{mode}</span>'
        f'<div class="calc-expr"><span>{html.escape(DUMMY_EXPRESSION)}</span></div></div>'
        f'<div class="calc-main {size}"><span>{html.escape(DUMMY_RESULT)}</span></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )


def render_mode_switch():
    with st.container(key="mode_switch"):
        return st.radio("Angle mode", ["DEG", "RAD"], key="mode",
                        horizontal=True, label_visibility="collapsed")


def render_buttons(labels, ncols, prefix):
    for start in range(0, len(labels), ncols):
        cols = st.columns(ncols)
        for offset, label in enumerate(labels[start:start + ncols]):
            index = start + offset
            cols[offset].button(
                label,
                key=f"btn_{category(label)}__{prefix}{index}",
                use_container_width=True,
            )


def render_card(key, title, labels, prefix, with_equals=False):
    with st.container(key=key):
        st.markdown(
            f'<div class="card-title"><span class="dot"></span>{title}</div>',
            unsafe_allow_html=True,
        )
        render_buttons(labels, 4, prefix)
        if with_equals:
            st.button("=", key="btn_eq__main", use_container_width=True)


# =========================================================
# 5. PAGE
# =========================================================

render_header()
display_slot = st.container()        # display sits above the mode switch
selected_mode = render_mode_switch()
with display_slot:
    render_display(selected_mode)

left, right = st.columns(2, gap="medium")
with left:
    render_card("card_sci", "Scientific", SCIENTIFIC, "s")
with right:
    render_card("card_key", "Keyboard", KEYBOARD, "k", with_equals=True)
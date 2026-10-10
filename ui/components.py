# ! Streamlit layout: the keypad updates session state, and the display is escaped HTML.

from __future__ import annotations

import re
from html import escape

import streamlit as st

from ui.keyboard import read_keyboard_events
from ui.model import ANGLES, TABS, Calculator
from ui.styles import inject_css

_TRIG = {
    (False, False): (("sin", "sin"), ("cos", "cos"), ("tan", "tan"), ("csc", "csc"), ("sec", "sec"), ("cot", "cot")),
    (True, False): (("asin", "sin⁻¹"), ("acos", "cos⁻¹"), ("atan", "tan⁻¹"), ("acsc", "csc⁻¹"), ("asec", "sec⁻¹"), ("acot", "cot⁻¹")),
    (False, True): (("sinh", "sinh"), ("cosh", "cosh"), ("tanh", "tanh"), ("csch", "csch"), ("sech", "sech"), ("coth", "coth")),
    (True, True): (("asinh", "sinh⁻¹"), ("acosh", "cosh⁻¹"), ("atanh", "tanh⁻¹"), ("acsch", "csch⁻¹"), ("asech", "sech⁻¹"), ("acoth", "coth⁻¹")),
}
_SCI_REST = (
    ("log", "log"), ("ln", "ln"), ("log2", "log₂"), ("pow10", "10ˣ"), ("powe", "eˣ"), ("pow2", "2ˣ"),
    ("sq", "x²"), ("cube", "x³"), ("pow", "xʸ"), ("sqrt", "√"), ("cbrt", "∛"), ("recip", "1/x"),
    ("pi", "π"), ("e", "e"), ("phi", "φ"), ("sqrt2", "√2"), ("sqrt3", "√3"), ("abs", "|x|"), ("subscript", "xₙ"),
)
_ADV = (
    ("diff", "d/dx"), ("diff2", "d²/dx²"), ("integ", "∫"), ("definite", "∫ₐᵇ"), ("lim", "lim"), ("limp", "lim⁺"),
    ("limm", "lim⁻"), ("sum", "Σ"), ("yroot", "ʸ√"), ("floor", "floor"), ("ceil", "ceil"), ("round", "round"),
    ("sgn", "sgn"), ("gcd", "gcd"), ("lcm", "lcm"), ("prime", "prime"), ("factor", "factor"), ("mod", "mod"),
)
_ALGEBRA = (
    ("pow", "aᵇ"), ("sqrt", "√"), ("lt", "<"),
    ("div", "a/b"), ("abs", "|x|"), ("le", "≤"),
    ("log", "log"), ("fact", "n!"), ("gt", ">"),
    ("imag", "i"), ("pct", "%"), ("ge", "≥"),
    ("varx", "x"), ("vary", "y"), ("eqn", "="),
)
_MATRIX = (
    ("lb", "[["), ("rb", "]]"), ("comma", ","), ("det", "det"), ("inv", "A⁻¹"), ("transpose", "Aᵀ"),
    ("rank", "rank"), ("trace", "tr"), ("eig", "eig"), ("evec", "vecs"), ("eye", "I"), ("mul", "×"),
)
_STATS = (
    ("mean", "mean"), ("median", "med"), ("datamode", "mode"), ("variance", "var"), ("stdev", "sd"), ("total", "Σx"),
    ("dmin", "min"), ("dmax", "max"), ("drange", "rng"), ("count", "n"), ("pctile", "%ile"), ("iqr", "IQR"),
    ("q1", "Q1"), ("q3", "Q3"), ("fact", "n!"), ("ncr", "nCr"), ("npr", "nPr"), ("ans", "Ans"),
    ("comma", ","), ("of", "% of"), ("rand", "rand"),
)
_MEMORY = (("mc", "MC"), ("mr", "MR"), ("mplus", "M+"), ("mminus", "M−"), ("pct", "%"), ("sign", "(−)"))
_TAB_LABELS = {"sci": "Sci", "adv": "Adv", "alg": "Alg", "mat": "Mat", "stat": "Stat"}
_PAD = (
    ("ac", "AC", "clr"), ("lparen", "(", "paren"), ("rparen", ")", "paren"), ("div", "÷", "op"),
    ("d7", "7", "num"), ("d8", "8", "num"), ("d9", "9", "num"), ("mul", "×", "op"),
    ("d4", "4", "num"), ("d5", "5", "num"), ("d6", "6", "num"), ("sub", "−", "op"),
    ("d1", "1", "num"), ("d2", "2", "num"), ("d3", "3", "num"), ("add", "+", "op"),
    ("d0", "0", "num"), ("dot", ".", "num"), ("bs", "⌫", "del"), ("eq", "=", "eq"),
)


def _compact(html: str) -> str:
    return re.sub(r">\s+<", "><", re.sub(r"\n\s*", "", html)).strip()


def get_state() -> Calculator:
    """Create the calculator once per browser session."""
    if "calc" not in st.session_state:
        st.session_state.calc = Calculator()
    return st.session_state.calc


def _press(action: str) -> None:
    state = get_state()
    state.press(action)
    if action == "copy":
        st.toast("Copied to clipboard")


def _load(index: int) -> None:
    get_state().load_history(index)


def _flag(active: bool) -> str:
    return "on" if active else "off"


def _functions(state: Calculator) -> tuple[tuple[str, str], ...]:
    tab = TABS[state.active_tab]
    if tab == "adv":
        return _ADV
    if tab == "alg":
        return _ALGEBRA
    if tab == "mat":
        return _MATRIX
    if tab == "stat":
        return _STATS
    return _TRIG[(state.second, state.hyp)] + _SCI_REST


def display_html(state: Calculator) -> str:
    chips = "".join(
        f'<span class="px-chip{" on" if on else ""}">{name}</span>'
        for name, on in ((state.mode, True), ("2ND", state.second), ("HYP", state.hyp), ("M", state.memory_on))
    )
    math = state.math_html()
    result = escape(state.result_line)
    err = " err" if state.is_error else ""
    size = " xxs" if len(state.result_line) > 28 else " xs" if len(state.result_line) > 16 else " sm" if len(state.result_line) > 10 else ""
    return _compact(f"""
    <div class="px-screen" role="status" aria-live="polite" aria-label="Calculator display">
      <div class="px-chips">{chips}</div>
      <div class="px-readout">
        <div class="px-math{err}">{math}</div>
        <div class="px-value{size}{err}">{result}</div>
      </div>
    </div>""")


def _md_plain(text: str) -> str:
    """Keep a history label as text inside a Streamlit button."""
    return text.replace("\\", "\\\\").replace("*", "\\*").replace("_", "\\_").replace("`", "\\`")


def footer_html() -> str:
    return _compact("""
    <div class="px-foot">
      <div class="px-keys">↑↓←→ move in the expression · Enter calculate · Esc clear · ⌫ delete</div>
      <div class="px-credit">Designed by Muhammad Junaid 03041659294</div>
    </div>""")


def render() -> None:
    """Draw the whole page. Call once from ``app.py``."""
    state = get_state()
    inject_css(state.theme, state.history_open)
    with st.container(key="kb_listener"):
        state.handle_keys(read_keyboard_events(state.copy_text, state.copy_nonce))
    with st.container(key="shell"):
        with st.container(key="workspace"):
            _render_calc(state)
            _render_history(state)
        st.markdown(footer_html(), unsafe_allow_html=True)


def _render_calc(state: Calculator) -> None:
    brand = _compact("""
    <div class="px-brand">
      <div class="px-logo" aria-hidden="true">Σ</div>
      <div class="px-brand-text">
        <div class="px-name">Precision</div>
        <div class="px-tag">Scientific Calculator</div>
      </div>
    </div>""")
    with st.container(key="calc"):
        with st.container(key="topbar"):
            st.markdown(brand, unsafe_allow_html=True)
            with st.container(key="angles"):
                for mode in ANGLES:
                    st.button(
                        mode,
                        key=f"angle_{mode}__{_flag(state.mode == mode)}",
                        on_click=_press,
                        args=(f"angle_{mode.lower()}",),
                    )
            moon = state.theme == "light"
            st.button("☾" if moon else "☀", key=f"theme__{_flag(not moon)}", on_click=_press, args=("theme",))
        st.markdown(display_html(state), unsafe_allow_html=True)
        with st.container(key="tabrow"):
            with st.container(key="tabs"):
                for index, tab in enumerate(TABS):
                    label = _TAB_LABELS[tab]
                    st.button(
                        label,
                        key=f"panel_{tab}__{_flag(state.active_tab == index)}",
                        on_click=_press,
                        args=(f"panel_{tab}",),
                    )
            with st.container(key="shifts"):
                st.button("2ND", key=f"mode_2nd__{_flag(state.second)}", on_click=_press, args=("mode_2nd",))
                st.button("HYP", key=f"mode_hyp__{_flag(state.hyp)}", on_click=_press, args=("mode_hyp",))
                st.button("Hist", key=f"hist__{_flag(state.history_open)}", on_click=_press, args=("hist",))
        func_key = "funcs3" if TABS[state.active_tab] == "alg" else "funcs"
        with st.container(key=func_key):
            tab = TABS[state.active_tab]
            for action, label in _functions(state):
                st.button(label, key=f"fn_{tab}_{action}", on_click=_press, args=(action,))
        with st.container(key="mem"):
            for action, label in _MEMORY:
                st.button(label, key=f"mem_{action}", on_click=_press, args=(action,))
        with st.container(key="pad"):
            for action, label, kind in _PAD:
                st.button(label, key=f"{kind}_{action}", on_click=_press, args=(action,))


def _render_history(state: Calculator) -> None:
    from engine.formatter import format_display, format_history

    with st.container(key="history"):
        with st.container(key="histhead"):
            st.markdown('<div class="px-htitle">History</div>', unsafe_allow_html=True)
            with st.container(key="histtools"):
                st.button("Copy", key="copy_result", on_click=_press, args=("copy",))
                st.button("Clear", key="hist_clear", on_click=_press, args=("hist_clear",))
        if not state.history:
            st.markdown('<div class="px-empty">No calculations yet</div>', unsafe_allow_html=True)
            return
        with st.container(key="hlist"):
            for index, item in enumerate(state.history):
                shown = item.detail or format_display(item.result)
                st.button(
                    _md_plain(format_history(item.expression, shown)),
                    key=f"hopen_{index}",
                    on_click=_load,
                    args=(index,),
                )

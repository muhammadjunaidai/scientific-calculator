# ! Calculator session: expression, memory, history, and the live result. No Streamlit import, so tests can run it directly.

from __future__ import annotations

import random
import re
import string
import subprocess
from dataclasses import dataclass, field

from engine.evaluator import try_evaluate
from engine.formatter import format_raw
from ui.mathdoc import Editor

ANGLES = ("DEG", "RAD", "GRAD")
TABS = ("sci", "adv", "alg", "mat", "stat")
HISTORY_LIMIT = 50

# ! Keys the page listener may forward to the keypad.
KEYMAP = {
    **{str(i): f"d{i}" for i in range(10)},
    ".": "dot", ",": "comma",
    "+": "add", "-": "sub", "*": "mul", "/": "div",
    "^": "pow", "_": "subscript", "!": "fact", "%": "pct",
    "(": "lparen", ")": "rparen",
    "Enter": "eq", "=": "eq",
    "Backspace": "bs", "Delete": "del", "Escape": "ac",
    "ArrowLeft": "left", "ArrowRight": "right", "ArrowUp": "up", "ArrowDown": "down",
    "Undo": "undo",
    "[": "lbrack", "]": "rbrack", "{": "lbrace", "}": "rbrace",
    "x": "varx", "y": "vary", "i": "imag",
    "<": "lt", ">": "gt",
    **{ch: f"k_{ch}" for ch in string.ascii_letters if ch not in "xyi"},
}


# ! One saved calculation: the expression, its number, and any symbolic result text.
@dataclass
class HistoryEntry:
    expression: str
    result: float
    detail: str = ""


# ! Everything one calculator session remembers, updated by keypad and keyboard actions.
@dataclass
class Calculator:
    expr: str = ""
    last_valid: float = 0.0
    ans: float = 0.0
    memory: float = 0.0
    mode: str = "DEG"
    second: bool = False
    hyp: bool = False
    active_tab: int = 0
    history: list[HistoryEntry] = field(default_factory=list)
    done: bool = False
    theme: str = "light"
    history_open: bool = False
    live_kind: str = "empty"
    preview: float = 0.0
    copy_text: str = ""
    copy_nonce: int = 0
    last_key_seq: int = 0
    result_text: str = ""
    editor: Editor = field(default_factory=Editor)

    @property
    def expression_line(self) -> str:
        if not self.expr:
            return ""
        return f"{self.expr} =" if self.done else self.expr

    @property
    def result_line(self) -> str:
        if self.is_error:
            if self.result_text:
                return self.result_text
            return "Math error" if self.live_kind == "math" else "Invalid expression"
        if not self.expr.strip():
            return "0"
        if self.result_text and self.live_kind == "ok":
            return self.result_text
        if self.done:
            return self._grouped(self.ans)
        if self.live_kind == "ok":
            return self._grouped(self.preview)
        return self._grouped(self.last_valid)

    @property
    def is_error(self) -> bool:
        return self.live_kind in ("math", "invalid")

    @property
    def show_caret(self) -> bool:
        return not self.done and not self.is_error

    @property
    def memory_on(self) -> bool:
        return self.memory != 0

    def _grouped(self, value: float) -> str:
        from engine.formatter import format_display
        return format_display(value)

    def press(self, action: str) -> None:
        """Apply one keypad or keyboard action."""
        if action in _NAV:
            _NAV[action](self)
            return
        if action == "ac":
            self._clear()
            return
        if action in ("left", "right", "up", "down"):
            self._pull()
            if not self.done and not self.is_error:
                self.editor.move(action)
            return
        if action == "undo":
            self._pull()
            if self.editor.undo_once():
                self._push()
            return
        if action == "bs":
            self._pull()
            self.done = False
            self.editor.checkpoint()
            self.editor.backspace()
            self._push()
            return
        if action == "del":
            self._pull()
            self.done = False
            self.editor.checkpoint()
            self.editor.delete()
            self._push()
            return
        if action == "eq":
            self._equals()
            return
        if action in _MEMORY:
            _MEMORY[action](self)
            return
        if action == "copy":
            self._copy()
            return
        if action == "hist":
            self.history_open = not self.history_open
            return
        if action == "rand":
            self._insert_number(format_raw(random.random()))
            return
        if action == "sign":
            self._sign()
            return
        if action == "pct" and _PERCENT_TAIL.search(self.expr):
            self._edit(True, lambda ed: ed.insert_text("%"))
            return
        if action in _WRAPS and (self.done or self.live_kind == "ok"):
            self._wrap(*_WRAPS[action])
            self.editor.loaded = None
            return
        if action in _WRAPS:
            self._edit(False, lambda ed, name=action: ed.apply_tail(name))
            return
        if action.startswith("k_") and len(action) == 3:
            self._edit(False, lambda ed, char=action[2]: ed.insert_text(char))
            return
        if action in _SPECIAL:
            self._edit(False, _SPECIAL[action])
            return
        text, continues = _INSERTS.get(action, ("", False))
        if not text:
            return
        if action == "dot" and (self.done or not self.expr):
            text = "0."
        self._edit(
            continues,
            lambda ed, chunk=text, name=action: _dispatch(ed, name, chunk),
            fresh=action in _FRESH or (len(action) == 2 and action[0] == "d" and action[1].isdigit()),
        )

    def load_history(self, index: int) -> None:
        if index < 0 or index >= len(self.history):
            return
        item = self.history[index]
        self.expr = item.expression
        self.editor.loaded = None
        self.ans = item.result
        self.preview = item.result
        self.last_valid = item.result
        self.result_text = item.detail
        self.done = True
        self.live_kind = "ok"

    def clear_history(self) -> None:
        self.history.clear()

    def handle_keys(self, events: list) -> None:
        if not isinstance(events, list):
            return
        for event in events:
            if not isinstance(event, dict):
                continue
            seq = int(event.get("seq") or 0)
            if seq <= self.last_key_seq:
                continue
            self.last_key_seq = seq
            if str(event.get("key", "")) == "click":
                self._pull()
                self.done = False
                self.editor.seek(str(event.get("path") or ""), int(event.get("at") or 0))
                continue
            action = KEYMAP.get(str(event.get("key", "")))
            if action:
                self.press(action)

    def math_html(self) -> str:
        """Textbook rendering of the current expression, with the editing caret."""
        self._pull()
        return self.editor.render(self.show_caret)

    def _clear(self) -> None:
        self.expr = ""
        self.editor.load("")
        self.editor.loaded = ""
        self.done = False
        self.live_kind = "empty"
        self.preview = 0.0
        self.last_valid = 0.0
        self.result_text = ""

    def _pull(self) -> None:
        """Rebuild the document when the expression was set from outside the editor."""
        if self.editor.loaded == self.expr:
            return
        self.editor.load(self.expr)
        self.editor.loaded = self.expr

    def _push(self) -> None:
        """Store the document as the expression the engines evaluate."""
        self.expr = self.editor.serialize()
        self.editor.loaded = self.expr
        self.done = False
        if not self.expr:
            self._refresh()
            return
        if self.editor.has_holes():
            self.result_text = ""
            self.live_kind = "incomplete"
            return
        self._refresh()
        if self.live_kind == "invalid" and _PARTIAL_NAME.match(self.expr):
            self.live_kind = "incomplete"
            self.result_text = ""

    def _prepare(self, continues: bool, fresh: bool = False) -> None:
        self._pull()
        if self.live_kind in ("math", "invalid") and fresh:
            self.editor.load("")
            self.done = False
            return
        if self.done:
            self.editor.load(format_raw(self.ans) if continues else "")
            self.done = False

    def _edit(self, continues: bool, change, fresh: bool = False) -> None:
        self._prepare(continues, fresh)
        self.editor.checkpoint()
        change(self.editor)
        self._push()

    def _equals(self) -> None:
        if self.done or not self.expr.strip():
            return
        from engine.symbolic import is_symbolic, try_solve

        if is_symbolic(self.expr):
            solved = try_solve(self.expr, self.mode)
            kind, text = solved
            if kind == "ok" and text:
                self.result_text = text
                self.done = True
                self.live_kind = "ok"
                self.history.insert(0, HistoryEntry(self.expr, self.ans, text))
                del self.history[HISTORY_LIMIT:]
                return
            self.done = False
            self.result_text = solved.message or "Invalid expression"
            self.live_kind = "math" if kind == "math" else "invalid"
            return
        self.result_text = ""
        outcome = try_evaluate(self.expr, self.mode, self.ans)
        kind, value = outcome
        if kind == "ok" and value is not None:
            self.ans = value
            self.preview = value
            self.last_valid = value
            self.done = True
            self.live_kind = "ok"
            self.history.insert(0, HistoryEntry(self.expr, value))
            del self.history[HISTORY_LIMIT:]
            return
        self.done = False
        self.result_text = outcome.message or "Invalid expression"
        self.live_kind = "math" if kind == "math" else "invalid"

    def _refresh(self) -> None:
        self.result_text = ""
        if not self.expr.strip():
            self.expr = ""
            self.live_kind = "empty"
            self.preview = 0.0
            self.last_valid = 0.0
            self.done = False
            return
        from engine.symbolic import is_symbolic, try_solve

        if is_symbolic(self.expr):
            solved = try_solve(self.expr, self.mode)
            kind, text = solved
            self.live_kind = kind
            if kind == "ok" and text:
                self.result_text = text
            elif kind in ("math", "invalid"):
                self.result_text = solved.message or "Invalid expression"
            return
        outcome = try_evaluate(self.expr, self.mode, self.ans)
        kind, value = outcome
        self.live_kind = kind
        if kind in ("math", "invalid"):
            self.result_text = outcome.message or "Invalid expression"
        if kind == "ok" and value is not None:
            self.preview = value
            self.last_valid = value

    def _wrap(self, template: str, _tail: str, _fresh: str) -> None:
        inner = format_raw(self.ans) if self.done else self.expr
        self.expr = template.format(x=inner)
        self.done = False
        self._refresh()

    def _insert_number(self, text: str) -> None:
        self._prepare(False, True)
        self.editor.checkpoint()
        if self.editor.ends_value():
            self.editor.insert_text("×")
        self.editor.insert_text(text)
        self._push()

    def _sign(self) -> None:
        if self.done:
            self.ans = float(format_raw(-self.ans))
            self.expr = format_raw(self.ans)
            self.preview = self.ans
            self.last_valid = self.ans
            self.live_kind = "ok"
            self.editor.loaded = None
            return
        if self.live_kind == "ok" and self.expr:
            if self.expr.startswith("−(") and self.expr.endswith(")"):
                self.expr = self.expr[2:-1]
            else:
                self.expr = f"−({self.expr})"
            self.editor.loaded = None
            self._refresh()
            return
        self._edit(True, lambda ed: ed.insert_text("−"))

    def _current(self) -> float | None:
        if self.done:
            return self.ans
        if self.live_kind == "ok":
            return self.preview
        if self.expr and self.live_kind == "incomplete":
            return self.last_valid
        if not self.expr:
            return self.ans
        return None

    def _remember(self, value: float) -> None:
        self.memory = 0.0 if abs(value) < 1e-13 else float(format_raw(value))

    def _memory_add(self, sign: float) -> None:
        current = self._current()
        if current is None:
            return
        self._remember(self.memory + sign * current)

    def _memory_clear(self) -> None:
        self.memory = 0.0

    def _memory_recall(self) -> None:
        self._insert_number(format_raw(self.memory))

    def _copy(self) -> None:
        if self.result_text and self.live_kind == "ok":
            text = self.result_text
        else:
            current = self._current()
            text = format_raw(0.0 if current is None else current)
        self.copy_text = text
        self.copy_nonce += 1
        try:
            subprocess.run(["clip"], input=text, text=True, check=False, timeout=2)
        except (OSError, subprocess.SubprocessError):
            pass

    def _set_mode(self, mode: str) -> None:
        self.mode = mode
        if not self.done:
            self._refresh()

    def _set_tab(self, index: int) -> None:
        self.active_tab = index

    def _toggle(self, name: str) -> None:
        setattr(self, name, not getattr(self, name))

    def _toggle_theme(self) -> None:
        self.theme = "dark" if self.theme == "light" else "light"


_PERCENT_TAIL = re.compile(r"[+\-−][0-9.]+$")
_PARTIAL_NAME = re.compile(r"[A-Za-z][A-Za-z0-9⁻¹₀₁₂₃₄₅₆₇₈₉]*")
_FRESH = {
    "dot", "add", "sub", "mul", "div", "pow", "pi", "e", "phi", "ans",
    "sqrt2", "sqrt3", "varx", "vary", "imag", "pct", "fact",
}


def _dispatch(editor: Editor, action: str, text: str) -> None:
    """Turn a keypad action into a structured edit at the cursor."""
    if action == "div":
        editor.insert_fraction()
    elif action == "pow":
        editor.insert_power()
    elif action == "lparen":
        editor._open_paren()
    elif action == "rparen":
        editor.close_group(")")
    elif action == "lb":
        editor.insert_matrix()
    elif action == "rb":
        editor.close_group("]")
        editor.close_group("]")
    elif action == "yroot":
        editor.insert_nth_root()
    elif action == "definite":
        editor.insert_integral(True)
    elif action == "lim":
        editor.insert_limit("")
    elif action == "limp":
        editor.insert_limit("+")
    elif action == "limm":
        editor.insert_limit("-")
    elif action == "sum":
        editor.insert_sum()
    else:
        editor.insert_text(text)


_SPECIAL = {
    "subscript": lambda ed: ed.insert_subscript(),
    "lbrack": lambda ed: ed.insert_group("[", "]"),
    "rbrack": lambda ed: ed.close_group("]"),
    "lbrace": lambda ed: ed.insert_group("{", "}"),
    "rbrace": lambda ed: ed.close_group("}"),
}


# text, continues-from-result
_INSERTS: dict[str, tuple[str, bool]] = {
    **{f"d{i}": (str(i), False) for i in range(10)},
    "dot": (".", False),
    "add": ("+", True), "sub": ("−", True), "mul": ("×", True), "div": ("÷", True),
    "pow": ("^", True),
    "lparen": ("(", False), "rparen": (")", False), "comma": (",", True),
    "sin": ("sin(", False), "cos": ("cos(", False), "tan": ("tan(", False),
    "csc": ("csc(", False), "sec": ("sec(", False), "cot": ("cot(", False),
    "asin": ("sin⁻¹(", False), "acos": ("cos⁻¹(", False), "atan": ("tan⁻¹(", False),
    "acsc": ("csc⁻¹(", False), "asec": ("sec⁻¹(", False), "acot": ("cot⁻¹(", False),
    "sinh": ("sinh(", False), "cosh": ("cosh(", False), "tanh": ("tanh(", False),
    "csch": ("csch(", False), "sech": ("sech(", False), "coth": ("coth(", False),
    "asinh": ("sinh⁻¹(", False), "acosh": ("cosh⁻¹(", False), "atanh": ("tanh⁻¹(", False),
    "acsch": ("csch⁻¹(", False), "asech": ("sech⁻¹(", False), "acoth": ("coth⁻¹(", False),
    "log": ("log(", False), "ln": ("ln(", False), "log2": ("log₂(", False),
    "mod": (" mod ", True), "ncr": (" nCr ", True), "npr": (" nPr ", True),
    "of": (" of ", True), "yroot": ("ʸ√", True),
    "pi": ("π", False), "e": ("e", False), "phi": ("φ", False), "ans": ("Ans", False),
    "sqrt2": ("√2", False), "sqrt3": ("√3", False),
    "abs": ("abs(", False),
    "varx": ("x", False), "vary": ("y", False), "imag": ("i", False),
    "lt": ("<", False), "gt": (">", False), "le": ("≤", False), "ge": ("≥", False),
    "eqn": ("=", False),
    "lim": ("limit(", False), "limp": ("limit+(", False), "limm": ("limit-(", False),
    "sum": ("sum(", False), "definite": ("definite(", False),
    "floor": ("floor(", False), "ceil": ("ceil(", False), "round": ("round(", False),
    "sgn": ("sign(", False), "gcd": ("gcd(", False), "lcm": ("lcm(", False),
    "prime": ("isprime(", False), "factor": ("factor(", False),
    "lb": ("[[", False), "rb": ("]]", False),
    "det": ("det(", False), "inv": ("inv(", False), "transpose": ("transpose(", False),
    "rank": ("rank(", False), "trace": ("trace(", False),
    "eig": ("eigenvalues(", False), "evec": ("eigenvectors(", False), "eye": ("eye(", False),
    "mean": ("mean(", False), "median": ("median(", False), "datamode": ("mode(", False),
    "variance": ("variance(", False), "stdev": ("stdev(", False),
    "dmin": ("min(", False), "dmax": ("max(", False), "drange": ("range(", False),
    "total": ("total(", False), "count": ("count(", False),
    "pctile": ("pctile(", False), "q1": ("q1(", False), "q3": ("q3(", False), "iqr": ("iqr(", False),
}

# template, tail-if-incomplete, fresh-if-empty
_WRAPS: dict[str, tuple[str, str, str]] = {
    "sq": ("({x})^2", "^2", "^2"),
    "cube": ("({x})^3", "^3", "^3"),
    "recip": ("1/({x})", "^(-1)", "^(-1)"),
    "pow10": ("10^({x})", "×10^(", "10^("),
    "powe": ("exp({x})", "×exp(", "exp("),
    "pow2": ("2^({x})", "×2^(", "2^("),
    "sqrt": ("√({x})", "√(", "√("),
    "cbrt": ("∛({x})", "∛(", "∛("),
    "fact": ("({x})!", "!", "!"),
    "pct": ("({x})%", "%", "%"),
    "diff": ("diff({x},x)", "diff(", "diff("),
    "diff2": ("diff2({x})", "diff2(", "diff2("),
    "integ": ("integrate({x},x)", "integrate(", "integrate("),
}

_NAV = {
    "angle_deg": lambda calc: calc._set_mode("DEG"),
    "angle_rad": lambda calc: calc._set_mode("RAD"),
    "angle_grad": lambda calc: calc._set_mode("GRAD"),
    "panel_sci": lambda calc: calc._set_tab(0),
    "panel_adv": lambda calc: calc._set_tab(1),
    "panel_alg": lambda calc: calc._set_tab(2),
    "panel_mat": lambda calc: calc._set_tab(3),
    "panel_stat": lambda calc: calc._set_tab(4),
    "mode_2nd": lambda calc: calc._toggle("second"),
    "mode_hyp": lambda calc: calc._toggle("hyp"),
    "theme": lambda calc: calc._toggle_theme(),
    "hist_clear": lambda calc: calc.clear_history(),
}

_MEMORY = {
    "mc": lambda calc: calc._memory_clear(),
    "mr": lambda calc: calc._memory_recall(),
    "mplus": lambda calc: calc._memory_add(1),
    "mminus": lambda calc: calc._memory_add(-1),
}

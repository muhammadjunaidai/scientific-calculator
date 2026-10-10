# ! Editable expression. Slots keep powers, roots, and fractions, then serialize to the engine syntax.

from __future__ import annotations

import copy
from html import escape

from engine.functions import FUNCTIONS

# ! Each node is a small list: txt, op, pow, frac, root, fn, group, abs, diff, int, lim, or sum.

_NAME = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ₀₁₂₃₄₅₆₇₈₉⁻¹πφ")
_CALLS = set(FUNCTIONS) | {
    "diff", "diff2", "integrate", "definite", "limit", "limit+", "limit-", "sum",
    "det", "inv", "transpose", "rank", "trace", "eigenvalues", "eigenvectors",
    "factor", "eye", "sqrt", "cbrt", "abs", "exp",
}
_WORDS = tuple(sorted(
    _CALLS | {"of", "mod", "nCr", "nPr", "C", "P", "pi", "PI", "phi", "Phi", "Ans", "ans", "ANS", "e"},
    key=len,
    reverse=True,
))
_ADD = {"+", "-", "−", "=", "<", ">", "≤", "≥", ",", ";"}
_MUL = {"*", "×", "·", "/", "÷"}
_POST = {"!", "%"}


# ! One expression, the cursor path inside it, and a small undo stack.
class Editor:

    def __init__(self) -> None:
        self.root: list = []
        self.path: tuple[tuple[int, str], ...] = ()
        self.offset = 0
        self.undo: list = []
        self.loaded: str | None = None

    def load(self, text: str) -> None:
        self.root = parse(text)
        self.path = ()
        self.offset = len(self.root)
        self.undo.clear()

    def serialize(self) -> str:
        return _ser_row(self.root)

    def has_holes(self) -> bool:
        return _holes(self.root)

    def checkpoint(self) -> None:
        self.undo.append(copy.deepcopy((self.root, self.path, self.offset)))
        if len(self.undo) > 50:
            del self.undo[:-50]

    def undo_once(self) -> bool:
        if not self.undo:
            return False
        self.root, self.path, self.offset = self.undo.pop()
        return True

    def current(self) -> list:
        return self._row(self.path)

    def move(self, direction: str) -> None:
        if direction == "left":
            self._left()
        elif direction == "right":
            self._right()
        elif direction == "up":
            self._up()
        elif direction == "down":
            self._down()

    def _row(self, path: tuple) -> list:
        row = self.root
        for index, slot in path:
            row = _slot(row[index], slot)
        return row

    def _container(self):
        if not self.path:
            return None, None
        index, slot = self.path[-1]
        return self._row(self.path[:-1])[index], slot

    def _enter(self, index: int, slot: str, offset: int) -> None:
        self.path = self.path + ((index, slot),)
        self.offset = offset

    def _exit_after(self) -> None:
        if not self.path:
            self.offset = len(self.root)
            return
        index, _slot = self.path[-1]
        self.path = self.path[:-1]
        self.offset = index + 1

    def _exit_before(self) -> None:
        if not self.path:
            self.offset = 0
            return
        index, _slot = self.path[-1]
        self.path = self.path[:-1]
        self.offset = index

    def _set_slot(self, slot: str, at_end: bool) -> None:
        index, _slot = self.path[-1]
        self.path = self.path[:-1] + ((index, slot),)
        self.offset = len(self.current()) if at_end else 0

    def _left(self) -> None:
        row = self.current()
        if self.offset > 0:
            node = row[self.offset - 1]
            seq = _slots(node)
            if seq:
                slot = seq[-1]
                self._enter(self.offset - 1, slot, len(_slot(node, slot)))
                return
            self.offset -= 1
            return
        if not self.path:
            return
        node, slot = self._container()
        seq = _slots(node)
        if slot in seq and seq.index(slot) > 0:
            prev = seq[seq.index(slot) - 1]
            self._set_slot(prev, True)
            return
        self._exit_before()

    def _right(self) -> None:
        row = self.current()
        if self.offset < len(row):
            node = row[self.offset]
            seq = _slots(node)
            if seq:
                self._enter(self.offset, seq[0], 0)
                return
            self.offset += 1
            return
        if not self.path:
            return
        node, slot = self._container()
        seq = _slots(node)
        if slot in seq and seq.index(slot) + 1 < len(seq):
            nxt = seq[seq.index(slot) + 1]
            self._set_slot(nxt, False)
            return
        self._exit_after()

    def _up(self) -> None:
        node, slot = self._container()
        if node is not None:
            kind = node[0]
            if kind == "frac" and slot == "den":
                self._set_slot("num", True)
                return
            if kind == "pow" and slot == "base":
                self._set_slot("exp", True)
                return
            if kind == "sub" and slot == "idx":
                self._set_slot("base", True)
                return
            if kind == "root" and slot == "rad" and node[1] is not None:
                self._set_slot("deg", True)
                return
            if kind == "int" and slot == "body" and node[2] is not None:
                self._set_slot("hi", True)
                return
            if kind == "int" and slot == "lo":
                self._set_slot("body", True)
                return
            if kind == "diff" and slot == "body":
                self._set_slot("order", True)
                return
            if kind == "sum" and slot == "body":
                self._set_slot("hi", True)
                return
            if kind == "sum" and slot == "lo":
                self._set_slot("body", True)
                return
            if kind == "lim" and slot == "body":
                self._set_slot("to", True)
                return
            if kind == "lim" and slot == "to":
                self._set_slot("var", True)
                return
            if kind == "pow" and slot == "exp" and len(self.path) >= 2:
                self._exit_after()
                self._up()
                return
        row = self.current()
        if self.offset > 0 and row[self.offset - 1][0] == "pow":
            node = row[self.offset - 1]
            self._enter(self.offset - 1, "exp", len(node[2]))
            return
        if self.offset > 0 and row[self.offset - 1][0] == "sub":
            node = row[self.offset - 1]
            self._enter(self.offset - 1, "base", len(node[1]))
            return
        if self.offset < len(row) and row[self.offset][0] == "frac":
            node = row[self.offset]
            self._enter(self.offset, "num", len(node[1]))

    def _down(self) -> None:
        node, slot = self._container()
        if node is None:
            row = self.current()
            if self.offset > 0 and row[self.offset - 1][0] == "sub":
                node = row[self.offset - 1]
                self._enter(self.offset - 1, "idx", len(node[2]))
            return
        kind = node[0]
        if kind == "pow" and slot == "exp":
            self._exit_after()
            return
        if kind == "sub" and slot == "base":
            self._set_slot("idx", True)
            return
        if kind == "sub" and slot == "idx":
            self._exit_after()
            return
        if kind == "frac" and slot == "num":
            self._set_slot("den", True)
            return
        if kind == "frac" and slot == "den":
            self._exit_after()
            return
        if kind == "root" and slot == "deg":
            self._set_slot("rad", True)
            return
        if kind == "root" and slot == "rad":
            self._exit_after()
            return
        if kind == "int" and slot == "hi":
            self._set_slot("body", True)
            return
        if kind == "int" and slot == "body" and node[1] is not None:
            self._set_slot("lo", True)
            return
        if kind == "int" and slot == "lo":
            self._exit_after()
            return
        if kind == "diff" and slot == "order":
            self._set_slot("body", True)
            return
        if kind == "sum" and slot == "hi":
            self._set_slot("body", True)
            return
        if kind == "sum" and slot == "body":
            self._set_slot("lo", True)
            return
        if kind == "sum" and slot == "lo":
            self._exit_after()
            return
        if kind == "lim" and slot == "var":
            self._set_slot("to", True)
            return
        if kind == "lim" and slot == "to":
            self._set_slot("body", True)
            return
        if kind == "lim" and slot == "body":
            self._exit_after()

    def backspace(self) -> None:
        row = self.current()
        if self.offset > 0:
            prev = row[self.offset - 1]
            if prev[0] in ("pow", "sub"):
                self._unwrap_at(self.offset - 1, prev[1])
                return
            if prev[0] == "frac":
                self._enter(self.offset - 1, "den", len(prev[2]))
                self.backspace()
                return
            del row[self.offset - 1]
            self.offset -= 1
            return
        node, slot = self._container()
        if node is None:
            return
        if node[0] in ("pow", "sub") and slot in ("exp", "idx") and not node[2]:
            self._unwrap_current(node[1])
            return
        if node[0] == "frac" and slot == "den" and not node[2]:
            self._unwrap_current(node[1])
            return
        if node[0] == "root" and slot == "rad" and not node[2]:
            self._exit_before()
            del self.current()[self.offset]
            return
        self._left()

    def _unwrap_at(self, index: int, kept: list) -> None:
        row = self.current()
        del row[index]
        for shift, item in enumerate(kept):
            row.insert(index + shift, item)
        self.offset = index + len(kept)

    def _unwrap_current(self, kept: list) -> None:
        index, _slot = self.path[-1]
        self.path = self.path[:-1]
        self._unwrap_at(index, kept)

    def delete(self) -> None:
        row = self.current()
        if self.offset < len(row):
            del row[self.offset]

    def insert_text(self, text: str) -> None:
        for char in text:
            self._char(char)

    def _char(self, char: str) -> None:
        if char.isspace():
            return
        if char == "^":
            self.insert_power()
            return
        if char == "_":
            self.insert_subscript()
            return
        if char in "/÷":
            self.insert_fraction()
            return
        if char == "(":
            self._open_paren()
            return
        if char == "[":
            self.insert_group("[", "]")
            return
        if char == "{":
            self.insert_group("{", "}")
            return
        if char in ")]}":
            self.close_group(char)
            return
        if char == "√":
            self.insert_sqrt()
            return
        if char == "∛":
            self.insert_cbrt()
            return
        if char == "²":
            self._power_fixed("2")
            return
        if char == "³":
            self._power_fixed("3")
            return
        if char in "+−×*!%,=<>≤≥;·–-":
            symbol = {"*": "×", "·": "×", "-": "−", "–": "−"}.get(char, char)
            self._put(["op", symbol])
            return
        self._put(["txt", char])

    def _put(self, node: list) -> None:
        row = self.current()
        row.insert(self.offset, node)
        self.offset += 1

    def insert_group(self, open_ch: str, close_ch: str) -> None:
        self._put(["group", open_ch, close_ch, []])
        self._enter(self.offset - 1, "body", 0)

    def insert_matrix(self) -> None:
        inner = ["group", "[", "]", []]
        self._put(["group", "[", "]", [inner]])
        index = self.offset - 1
        self.path = self.path + ((index, "body"), (0, "body"))
        self.offset = 0

    def close_group(self, which: str) -> None:
        for _ in range(30):
            node, _slot = self._container()
            if node is None:
                break
            if node[0] == "group" and node[2] == which:
                self._exit_after()
                return
            if which == ")" and node[0] in ("fn", "abs"):
                self._exit_after()
                return
            if which == ")" and node[0] in ("pow", "frac", "root", "diff", "int", "lim", "sum"):
                self._exit_after()
                continue
            break
        self._put(["txt", which])

    def insert_fraction(self) -> None:
        num = self._pop_factor()
        self._put(["frac", num, []])
        self._enter(self.offset - 1, "num", len(num))

    def insert_power(self) -> None:
        base = self._pop_factor()
        self._put(["pow", base, []])
        self._enter(self.offset - 1, "exp", 0)

    def insert_subscript(self) -> None:
        base = self._pop_factor()
        self._put(["sub", base, []])
        self._enter(self.offset - 1, "idx", 0)

    def seek(self, spec: str, at: int) -> None:
        """Move the cursor to a box the user clicked."""
        path: list[tuple[int, str]] = []
        if spec:
            for piece in spec.split("/"):
                if ":" not in piece:
                    return
                index_text, slot = piece.split(":", 1)
                if not index_text.isdigit() or not slot:
                    return
                path.append((int(index_text), slot))
        row = self.root
        for index, slot in path:
            if index < 0 or index >= len(row):
                return
            try:
                row = _slot(row[index], slot)
            except (IndexError, TypeError):
                return
        self.path = tuple(path)
        self.offset = max(0, min(int(at), len(row)))

    def insert_sqrt(self) -> None:
        self._put(["root", None, []])
        self._enter(self.offset - 1, "rad", 0)

    def insert_cbrt(self) -> None:
        self._put(["root", [["txt", "3"]], []])
        self._enter(self.offset - 1, "rad", 0)

    def insert_nth_root(self) -> None:
        degree = self._pop_factor()
        self._put(["root", degree, []])
        slot = "rad" if degree else "deg"
        self._enter(self.offset - 1, slot, len(degree) if degree else 0)

    def insert_abs(self) -> None:
        self._put(["abs", []])
        self._enter(self.offset - 1, "body", 0)

    def insert_function(self, name: str) -> None:
        self._put(["fn", name, []])
        self._enter(self.offset - 1, "arg", 0)

    def insert_diff(self, order: int) -> None:
        exp = [] if order <= 1 else [["txt", str(order)]]
        self._put(["diff", exp, [], "x"])
        self._enter(self.offset - 1, "body", 0)

    def insert_integral(self, definite: bool) -> None:
        if definite:
            self._put(["int", [], [], [], "x"])
        else:
            self._put(["int", None, None, [], "x"])
        self._enter(self.offset - 1, "body", 0)

    def insert_limit(self, side: str) -> None:
        self._put(["lim", side, [["txt", "x"]], [], []])
        self._enter(self.offset - 1, "to", 0)

    def insert_sum(self) -> None:
        self._put(["sum", [], [], []])
        self._enter(self.offset - 1, "body", 0)

    def ends_value(self) -> bool:
        row = self.current()
        if self.offset == 0:
            return False
        node = row[self.offset - 1]
        return not (node[0] == "op" and node[1] not in _POST)

    def apply_tail(self, action: str) -> None:
        """Insert the incomplete form of a keypad wrap, with the cursor in the new slot."""
        if action == "sq":
            self._power_fixed("2")
        elif action == "cube":
            self._power_fixed("3")
        elif action == "recip":
            grouped = ["group", "(", ")", [["op", "−"], ["txt", "1"]]]
            self._put(["pow", [], [grouped]])
        elif action == "pow10":
            self._lead_times()
            self._put(["pow", [["txt", "1"], ["txt", "0"]], []])
            self._enter(self.offset - 1, "exp", 0)
        elif action == "pow2":
            self._lead_times()
            self._put(["pow", [["txt", "2"]], []])
            self._enter(self.offset - 1, "exp", 0)
        elif action == "powe":
            self._lead_times()
            self._put(["pow", [["txt", "e"]], []])
            self._enter(self.offset - 1, "exp", 0)
        elif action == "sqrt":
            self.insert_sqrt()
        elif action == "cbrt":
            self.insert_cbrt()
        elif action == "fact":
            self._put(["op", "!"])
        elif action == "pct":
            self._put(["op", "%"])
        elif action == "diff":
            self.insert_diff(1)
        elif action == "diff2":
            self.insert_diff(2)
        elif action == "integ":
            self.insert_integral(False)

    def _lead_times(self) -> None:
        if self.root:
            self._put(["op", "×"])

    def _power_fixed(self, digits: str) -> None:
        base = self._pop_factor()
        exp = [["txt", char] for char in digits]
        self._put(["pow", base, exp])

    def _open_paren(self) -> None:
        name, start = self._name_before()
        if name in ("C", "P"):
            name = "nCr" if name == "C" else "nPr"
        if not name or name not in _CALLS:
            self.insert_group("(", ")")
            return
        row = self.current()
        del row[start:self.offset]
        self.offset = start
        if name == "sqrt":
            self.insert_sqrt()
        elif name == "cbrt":
            self.insert_cbrt()
        elif name == "abs":
            self.insert_abs()
        elif name == "exp":
            self._put(["pow", [["txt", "e"]], []])
            self._enter(self.offset - 1, "exp", 0)
        elif name == "diff":
            self.insert_diff(1)
        elif name == "diff2":
            self.insert_diff(2)
        elif name == "integrate":
            self.insert_integral(False)
        elif name == "definite":
            self.insert_integral(True)
        elif name == "limit":
            self.insert_limit("")
        elif name == "limit+":
            self.insert_limit("+")
        elif name == "limit-":
            self.insert_limit("-")
        elif name == "sum":
            self.insert_sum()
        else:
            self.insert_function(name)

    def _name_before(self) -> tuple[str, int]:
        row = self.current()
        start = self.offset
        while start > 0 and row[start - 1][0] == "txt" and row[start - 1][1] in _NAME:
            start -= 1
        name = "".join(row[index][1] for index in range(start, self.offset))
        return name, start

    def _pop_factor(self) -> list:
        row = self.current()
        end = self.offset
        index = end
        while index > 0 and row[index - 1][0] == "op" and row[index - 1][1] in _POST:
            index -= 1
        if index == 0:
            return []
        if row[index - 1][0] == "op":
            return []
        if row[index - 1][0] == "txt":
            start = index - 1
            while start > 0 and row[start - 1][0] == "txt" and _same_run(row[start - 1][1], row[start][1]):
                start -= 1
        else:
            start = index - 1
        factor = row[start:end]
        del row[start:end]
        self.offset = start
        return factor

    def render(self, caret: bool) -> str:
        return _draw_row(self.root, self.path, self.offset if caret else None, "")


def _same_run(left: str, right: str) -> bool:
    def kind(char: str) -> str:
        if char.isdigit() or char == ".":
            return "num"
        if char in _NAME or char.isalpha():
            return "name"
        return "other"

    return kind(left) == kind(right) and kind(left) in ("num", "name")


def _slots(node: list) -> tuple[str, ...]:
    kind = node[0]
    if kind == "pow":
        return ("base", "exp")
    if kind == "sub":
        return ("base", "idx")
    if kind == "frac":
        return ("num", "den")
    if kind == "root":
        return ("rad",) if node[1] is None else ("deg", "rad")
    if kind == "fn":
        return ("arg",)
    if kind in ("group", "abs", "diff"):
        return ("body",)
    if kind == "int":
        return ("body",) if node[1] is None else ("hi", "body", "lo")
    if kind == "lim":
        return ("var", "to", "body")
    if kind == "sum":
        return ("hi", "body", "lo")
    return ()


def _slot(node: list, slot: str) -> list:
    kind = node[0]
    if kind in ("pow", "sub"):
        return node[1] if slot == "base" else node[2]
    if kind == "frac":
        return node[1] if slot == "num" else node[2]
    if kind == "root":
        if slot == "deg":
            if node[1] is None:
                node[1] = []
            return node[1]
        return node[2]
    if kind == "fn":
        return node[2]
    if kind == "group":
        return node[3]
    if kind == "abs":
        return node[1]
    if kind == "diff":
        return node[1] if slot == "order" else node[2]
    if kind == "int":
        if slot == "lo":
            return node[1]
        if slot == "hi":
            return node[2]
        return node[3]
    if kind == "lim":
        if slot == "var":
            return node[2]
        if slot == "to":
            return node[3]
        return node[4]
    if kind == "sum":
        if slot == "lo":
            return node[1]
        if slot == "hi":
            return node[2]
        return node[3]
    return node[1]


def _holes(row: list) -> bool:
    for node in row:
        kind = node[0]
        if kind in ("txt", "op"):
            continue
        if kind in ("pow", "sub") and (not node[1] or not node[2] or _holes(node[1]) or _holes(node[2])):
            return True
        if kind == "frac" and (not node[1] or not node[2] or _holes(node[1]) or _holes(node[2])):
            return True
        if kind == "root":
            degree = node[1]
            if (degree is not None and not degree) or not node[2] or _holes(node[2]):
                return True
            if degree is not None and _holes(degree):
                return True
        if kind == "fn" and (not node[2] or _holes(node[2])):
            return True
        if kind == "group" and (not node[3] or _holes(node[3])):
            return True
        if kind == "abs" and (not node[1] or _holes(node[1])):
            return True
        if kind == "diff" and (not node[2] or _holes(node[1]) or _holes(node[2])):
            return True
        if kind == "int":
            if not node[3] or _holes(node[3]):
                return True
            if node[1] is not None and (not node[1] or not node[2] or _holes(node[1]) or _holes(node[2])):
                return True
        if kind == "lim" and (not node[3] or not node[4] or _holes(node[2]) or _holes(node[3]) or _holes(node[4])):
            return True
        if kind == "sum" and (not node[1] or not node[2] or not node[3] or _holes(node[1]) or _holes(node[2]) or _holes(node[3])):
            return True
    return False


_TO_SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
_FROM_SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def _ser_row(row: list) -> str:
    return "".join(_ser(node) for node in row)


def _atom(row: list) -> bool:
    """True when the row can sit next to an operator without extra parentheses."""
    if not row or any(node[0] == "op" for node in row):
        return False
    if all(node[0] == "txt" for node in row):
        return True
    return len(row) == 1 and row[0][0] in ("fn", "group", "abs", "root", "sub")


def _paren(row: list) -> str:
    text = _ser_row(row)
    if _atom(row):
        return text
    return f"({text})"


def _ser(node: list) -> str:
    kind = node[0]
    if kind == "txt":
        return node[1]
    if kind == "op":
        return node[1]
    if kind == "pow":
        exp = _ser_row(node[2])
        if not _atom(node[2]):
            exp = f"({exp})"
        return f"{_paren(node[1])}^{exp}"
    if kind == "sub":
        index = _ser_row(node[2])
        base = _paren(node[1])
        if index.isdigit():
            return base + index.translate(_TO_SUB)
        return f"{base}_{{{index}}}"
    if kind == "frac":
        return f"{_paren(node[1])}/{_paren(node[2])}"
    if kind == "root":
        body = _ser_row(node[2])
        wrapped = body if _atom(node[2]) else f"({body})"
        degree = node[1]
        if degree is None:
            return f"√{wrapped}" if _atom(node[2]) else f"√({body})"
        if _ser_row(degree) == "3":
            return f"∛{wrapped}" if _atom(node[2]) else f"∛({body})"
        deg = _paren(degree)
        return f"{deg}ʸ√({body})"
    if kind == "fn":
        if not node[2]:
            return f"{node[1]}("
        return f"{node[1]}({_ser_row(node[2])})"
    if kind == "group":
        return f"{node[1]}{_ser_row(node[3])}{node[2]}" if node[3] else node[1]
    if kind == "abs":
        if not node[1]:
            return "abs("
        return f"abs({_ser_row(node[1])})"
    if kind == "diff":
        body = _ser_row(node[2])
        order = _ser_row(node[1])
        var = node[3] or "x"
        if not body and not order:
            return "diff("
        if order in ("", "1"):
            return f"diff({body},{var})"
        if order == "2":
            return f"diff2({body})" if var in ("x", "") else f"diff({body},{var},2)"
        return f"diff({body},{var},{order})"
    if kind == "int":
        body = _ser_row(node[3])
        var = node[4] or "x"
        if node[1] is None:
            return "integrate(" if not body else f"integrate({body},{var})"
        lower, upper = _ser_row(node[1]), _ser_row(node[2])
        if not body and not lower and not upper:
            return "definite("
        if var not in ("x", ""):
            return f"definite({body},{var},{lower},{upper})"
        return f"definite({body},{lower},{upper})"
    if kind == "lim":
        side = node[1]
        name = "limit+" if side == "+" else "limit-" if side == "-" else "limit"
        body, var, point = _ser_row(node[4]), _ser_row(node[2]) or "x", _ser_row(node[3])
        if not body and not point:
            return f"{name}("
        return f"{name}({body},{var},{point})"
    if kind == "sum":
        body, lower, upper = _ser_row(node[3]), _ser_row(node[1]), _ser_row(node[2])
        if not body and not lower and not upper:
            return "sum("
        return f"sum({body},{lower},{upper})"
    return ""


def parse(text: str) -> list:
    if not text:
        return []
    try:
        parser = _Parser(_tokenize(text))
        row = parser.parse_expr()
        if not parser.eof():
            raise ValueError
        return row
    except (ValueError, IndexError):
        return [["txt", char] for char in text]


def _tokenize(text: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if text.startswith("ʸ√", index):
            tokens.append(("op", "ʸ√"))
            index += 2
            continue
        if char.isdigit() or (char == "." and index + 1 < length and text[index + 1].isdigit()):
            start = index
            index += 1
            while index < length and (text[index].isdigit() or text[index] == "."):
                index += 1
            tokens.append(("num", text[start:index]))
            continue
        word = next((name for name in _WORDS if text.startswith(name, index)), None)
        if word:
            tokens.append(("word", word))
            index += len(word)
            continue
        if char.isalpha() or char in "πφ":
            tokens.append(("word", char))
            index += 1
            continue
        if char in "()[]{}":
            tokens.append(("br", char))
            index += 1
            continue
        if char in "₀₁₂₃₄₅₆₇₈₉":
            tokens.append(("subd", char.translate(_FROM_SUB)))
            index += 1
            continue
        if char in "+-−–*/×·/÷^_!%,=<>≤≥;√∛²³":
            mapped = {"-": "−", "–": "−", "*": "×", "·": "×"}.get(char, char)
            tokens.append(("op", mapped))
            index += 1
            continue
        raise ValueError(char)
    return tokens


# ! Turns a plain expression string back into editor nodes.
class _Parser:
    def __init__(self, tokens: list[tuple[str, str]]) -> None:
        self.tokens = tokens
        self.pos = 0

    def eof(self) -> bool:
        return self.pos >= len(self.tokens)

    def peek(self) -> tuple[str, str]:
        if self.eof():
            return ("eof", "")
        return self.tokens[self.pos]

    def take(self) -> tuple[str, str]:
        token = self.peek()
        self.pos += 1
        return token

    def parse_expr(self) -> list:
        if self._stop():
            return []
        row = self.parse_term()
        while self.peek()[0] == "op" and self.peek()[1] in _ADD:
            _kind, op = self.take()
            row.append(["op", op])
            if self._stop():
                break
            row.extend(self.parse_term())
        return row

    def parse_term(self) -> list:
        row = self.parse_power()
        while True:
            kind, op = self.peek()
            if kind == "op" and op in _MUL:
                self.take()
                right = self.parse_power()
                if op in ("/", "÷"):
                    row = [["frac", row, right]]
                else:
                    row.append(["op", "×" if op in ("*", "×", "·") else op])
                    row.extend(right)
                continue
            if kind == "word" and op in ("of", "mod", "nCr", "nPr", "C", "P") and self._next_br() != "(":
                self.take()
                shown = {"C": "nCr", "P": "nPr"}.get(op, op)
                row.append(["op", shown])
                row.extend(self.parse_power())
                continue
            if self._primary():
                row.extend(self.parse_power())
                continue
            return row

    def parse_power(self) -> list:
        row = self._attach_sub(_flatten_row(self.parse_unary()))
        if self.peek() == ("op", "^"):
            self.take()
            return [["pow", row, _flatten_row(self.parse_power())]]
        if self.peek() == ("op", "ʸ√"):
            self.take()
            return [["root", row, _flatten_row(self.parse_power())]]
        return row

    def parse_unary(self) -> list:
        if self.peek()[0] == "op" and self.peek()[1] in ("+", "−"):
            _kind, op = self.take()
            return [["op", op], *_flatten_row(self.parse_unary())]
        if self.peek() == ("op", "√"):
            self.take()
            return [["root", None, _flatten_row(self.parse_unary())]]
        if self.peek() == ("op", "∛"):
            self.take()
            return [["root", [["txt", "3"]], _flatten_row(self.parse_unary())]]
        node = self.parse_primary()
        row = node[1] if node[0] == "juxt" else [node]
        while self.peek()[0] == "op" and self.peek()[1] in _POST:
            row.append(["op", self.take()[1]])
        if self.peek() == ("op", "²"):
            self.take()
            row = [["pow", row, [["txt", "2"]]]]
        elif self.peek() == ("op", "³"):
            self.take()
            row = [["pow", row, [["txt", "3"]]]]
        return row

    def parse_primary(self) -> list:
        kind, value = self.peek()
        if kind == "num":
            self.take()
            return self._chars(value)
        if kind == "word":
            self.take()
            if value in ("pi", "PI", "π"):
                return ["txt", "π"]
            if value in ("phi", "Phi", "φ"):
                return ["txt", "φ"]
            if self.peek() == ("br", "(") and (value in _CALLS or value in ("C", "P")):
                name = "nCr" if value == "C" else "nPr" if value == "P" else value
                return self._call(name)
            if value in ("e",):
                return ["txt", "e"]
            return self._chars(value)
        if kind == "br" and value in "([{":
            return self._group(value, {"(": ")", "[": "]", "{": "}"}[value])
        raise ValueError(value)

    def _attach_sub(self, row: list) -> list:
        digits = []
        while self.peek()[0] == "subd":
            digits.append(["txt", self.take()[1]])
        if digits:
            return [["sub", row, digits]]
        if self.peek() == ("op", "_") and self._next_br() == "{":
            self.take()
            self.take()
            body = self.parse_expr()
            if self.peek() == ("br", "}"):
                self.take()
            return [["sub", row, body]]
        return row

    def _chars(self, text: str) -> list:
        return ["juxt", [["txt", char] for char in text]]

    def _group(self, open_ch: str, close_ch: str) -> list:
        self.take()
        if self.peek() == ("br", close_ch):
            self.take()
            return ["group", open_ch, close_ch, []]
        body = self.parse_expr()
        if self.peek() == ("br", close_ch):
            self.take()
        return ["group", open_ch, close_ch, body]

    def _call(self, name: str) -> list:
        self.take()
        if self.peek() == ("br", ")"):
            self.take()
            args: list = []
        else:
            args = self.parse_expr()
            if self.peek() == ("br", ")"):
                self.take()
        return _lift(name, args)

    def _stop(self) -> bool:
        return self.peek()[0] in ("eof",) or self.peek() == ("br", ")") or self.peek()[1] in ("]", "}")

    def _primary(self) -> bool:
        kind, value = self.peek()
        if kind in ("num", "word"):
            return True
        if kind == "br" and value in "([{":
            return True
        return kind == "op" and value in ("√", "∛")

    def _next_br(self) -> str:
        if self.pos + 1 >= len(self.tokens):
            return ""
        return self.tokens[self.pos + 1][1]


def _flatten_row(row: list) -> list:
    flat: list = []
    for node in row:
        flat.extend(node[1] if node[0] == "juxt" else [node])
    return flat


def _lift(name: str, args: list) -> list:
    parts = _split_commas(args)
    if name == "sqrt":
        return ["root", None, parts[0] if parts else []]
    if name == "cbrt":
        return ["root", [["txt", "3"]], parts[0] if parts else []]
    if name == "abs":
        return ["abs", parts[0] if parts else []]
    if name == "exp":
        return ["pow", [["txt", "e"]], parts[0] if parts else []]
    if name in ("diff", "diff2"):
        body = parts[0] if parts else []
        var = _ser_row(parts[1]) if len(parts) > 1 else "x"
        if name == "diff2":
            return ["diff", [["txt", "2"]], body, var or "x"]
        order = parts[2] if len(parts) > 2 else []
        return ["diff", order, body, var or "x"]
    if name == "integrate":
        body = parts[0] if parts else []
        var = _ser_row(parts[1]) if len(parts) > 1 else "x"
        return ["int", None, None, body, var or "x"]
    if name == "definite":
        if len(parts) >= 4:
            return ["int", parts[2], parts[3], parts[0], _ser_row(parts[1]) or "x"]
        lower = parts[1] if len(parts) > 1 else []
        upper = parts[2] if len(parts) > 2 else []
        return ["int", lower, upper, parts[0] if parts else [], "x"]
    if name in ("limit", "limit+", "limit-"):
        side = "+" if name == "limit+" else "-" if name == "limit-" else ""
        body = parts[0] if parts else []
        if len(parts) >= 3:
            return ["lim", side, parts[1], parts[2], body]
        point = parts[1] if len(parts) > 1 else []
        return ["lim", side, [["txt", "x"]], point, body]
    if name == "sum":
        body = parts[0] if parts else []
        lower = parts[1] if len(parts) > 1 else []
        upper = parts[2] if len(parts) > 2 else []
        return ["sum", lower, upper, body]
    return ["fn", name, args]


def _split_commas(row: list) -> list[list]:
    parts: list[list] = [[]]
    for node in row:
        if node[0] == "op" and node[1] == ",":
            parts.append([])
        else:
            parts[-1].append(node)
    return parts


_CARET = '<span class="m-caret"></span>'


def _draw_row(row: list, path: tuple, offset: int | None, address: str, boxed: bool = False) -> str:
    """Draw one slot.

    The main line and ordinary text stay plain. A structured field (exponent,
    radicand, function argument, fraction part, and the other holes) is always
    a dashed box, empty or filled. The caret is drawn only in the active slot.
    """
    live = offset is not None and not path
    parts: list[str] = []
    for index, node in enumerate(row):
        if live and index == offset:
            parts.append(_CARET)
        node_address = f"{address}/{index}" if address else str(index)
        if path and index == path[0][0]:
            html = _draw_node(node, path[0][1], path[1:], offset, node_address)
        else:
            html = _draw_node(node, None, (), None, node_address)
        parts.append(
            f'<span class="m-atom" data-path="{escape(address)}" data-at="{index + 1}">{html}</span>'
        )
    if live and (offset or 0) == len(row):
        parts.append(_CARET)
    cls = "m-row"
    if boxed:
        cls += " m-box"
        if live:
            cls += " m-live"
    return (
        f'<span class="{cls}" data-path="{escape(address)}" data-at="{len(row)}">'
        f'{"".join(parts)}</span>'
    )


def _draw_node(node: list, slot: str | None, path: tuple, offset: int | None, node_address: str) -> str:
    def sub(name: str, child: list, boxed: bool = False) -> str:
        slot_address = f"{node_address}:{name}"
        if slot == name:
            return _draw_row(child, path, offset, slot_address, boxed)
        return _draw_row(child, (), None, slot_address, boxed)

    kind = node[0]
    if kind == "txt":
        text = escape(node[1])
        cls = "m-var" if len(node[1]) == 1 and node[1] in _NAME and not node[1].isdigit() else "m-txt"
        return f'<span class="{cls}">{text}</span>'
    if kind == "op":
        return f'<span class="m-op">{escape(node[1])}</span>'
    if kind == "pow":
        return (
            f'<span class="m-pow"><span class="m-base">{sub("base", node[1])}</span>'
            f'<span class="m-exp">{sub("exp", node[2], True)}</span></span>'
        )
    if kind == "sub":
        return (
            f'<span class="m-sub"><span class="m-base">{sub("base", node[1])}</span>'
            f'<span class="m-idx">{sub("idx", node[2], True)}</span></span>'
        )
    if kind == "frac":
        return (
            f'<span class="m-frac"><span class="m-num">{sub("num", node[1], True)}</span>'
            f'<span class="m-bar"></span><span class="m-den">{sub("den", node[2], True)}</span></span>'
        )
    if kind == "root":
        degree = "" if node[1] is None else f'<span class="m-deg">{sub("deg", node[1], True)}</span>'
        return (
            f'<span class="m-root {"" if node[1] is None else "m-nth"}">{degree}'
            f'<span class="m-surd">√</span><span class="m-rad">{sub("rad", node[2], True)}</span></span>'
        )
    if kind == "fn":
        return (
            f'<span class="m-fn"><span class="m-fname">{escape(node[1])}</span>'
            f'<span class="m-paren">(</span>{sub("arg", node[2], True)}<span class="m-paren">)</span></span>'
        )
    if kind == "group":
        return (
            f'<span class="m-group"><span class="m-paren">{escape(node[1])}</span>'
            f'{sub("body", node[3])}<span class="m-paren">{escape(node[2])}</span></span>'
        )
    if kind == "abs":
        return (
            f'<span class="m-group"><span class="m-paren">|</span>{sub("body", node[1], True)}'
            f'<span class="m-paren">|</span></span>'
        )
    if kind == "diff":
        # ! Box the order when it has a value or the caret is there. The dx copy is not a field.
        order_boxed = bool(node[1]) or slot == "order"
        order = sub("order", node[1], order_boxed)
        quiet = _draw_row(node[1], (), None, f"{node_address}:order", False)
        var = escape(node[3] or "x")
        return (
            '<span class="m-diff"><span class="m-dfrac">'
            f'<span class="m-dtop"><span class="m-d">d</span><span class="m-dord">{order}</span></span>'
            '<span class="m-bar"></span>'
            f'<span class="m-dbot"><span class="m-d">d</span><span class="m-var">{var}</span>'
            f'<span class="m-dord">{quiet}</span></span></span>'
            f'<span class="m-dbody">{sub("body", node[2], True)}</span></span>'
        )
    if kind == "int":
        if node[1] is None:
            limits = '<span class="m-isym">∫</span>'
        else:
            limits = (
                f'<span class="m-icol"><span class="m-limtop">{sub("hi", node[2], True)}</span>'
                f'<span class="m-isym">∫</span><span class="m-limbot">{sub("lo", node[1], True)}</span></span>'
            )
        var = escape(node[4] or "x")
        return (
            f'<span class="m-int">{limits}<span class="m-ibody">{sub("body", node[3], True)}</span>'
            f'<span class="m-dx">d<span class="m-var">{var}</span></span></span>'
        )
    if kind == "lim":
        side = escape(node[1])
        return (
            '<span class="m-limblk"><span class="m-limcol"><span class="m-limword">lim</span>'
            f'<span class="m-limto">{sub("var", node[2], True)}<span class="m-arr">→</span>'
            f'{sub("to", node[3], True)}<span class="m-side">{side}</span></span></span>'
            f'<span class="m-lbody">{sub("body", node[4], True)}</span></span>'
        )
    if kind == "sum":
        return (
            '<span class="m-sumblk"><span class="m-scol">'
            f'<span class="m-hi">{sub("hi", node[2], True)}</span><span class="m-sigma">Σ</span>'
            f'<span class="m-lo">{sub("lo", node[1], True)}</span></span>'
            f'<span class="m-sbody">{sub("body", node[3], True)}</span></span>'
        )
    return ""

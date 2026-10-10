# ! Numeric expression parser. It whitelists tokens and never calls eval or exec.

from __future__ import annotations

import math
import re

from .formatter import snap
from .functions import (
    FUNCTIONS,
    INFIX,
    VARARGS,
    Answer,
    CalcError,
    Incomplete,
    cbrt,
    factorial,
    log,
    log10,
    ncr,
    npr,
    power,
    root,
    round_half,
    sqrt,
    _modulo,
)

_PHI = (1 + math.sqrt(5)) / 2

MAX_EXPRESSION_LENGTH = 500

_CONSTANTS = {
    "π": "pi", "pi": "pi", "PI": "pi", "e": "e",
    "φ": "phi", "phi": "phi", "Phi": "phi",
    "Ans": "Ans", "ANS": "Ans", "ans": "Ans",
}
_ALIASES = {"C": "nCr", "P": "nPr"}
_INFIX_WORDS = {"of"}
_WORDS = sorted([*FUNCTIONS, *_CONSTANTS, *_ALIASES, *_INFIX_WORDS], key=len, reverse=True)
_NUMBER = re.compile(r"(?:\d+\.\d*|\.\d+|\d+)")
_SYMBOLS = {
    "+": "+", "-": "-", "−": "-", "–": "-",
    "*": "*", "×": "*", "·": "*",
    "/": "/", "÷": "/",
    "^": "^", "!": "!", "%": "%", ",": ",",
    "°": "°", "′": "′", "″": "″",
    "√": "√", "∛": "∛", "²": "²", "³": "³",
}

Token = tuple[str, object]


def tokenize(text: str) -> list[Token]:
    """Split ``text`` into tokens. Raises :class:`CalcError` on illegal input."""
    if len(text) > MAX_EXPRESSION_LENGTH:
        raise CalcError("Invalid expression")
    tokens: list[Token] = []
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
        number = _NUMBER.match(text, index)
        if number:
            end = number.end()
            if end < length and text[end] == "E":
                cursor = end + 1
                if cursor < length and text[cursor] in "+-":
                    cursor += 1
                digits = cursor
                while digits < length and text[digits].isdigit():
                    digits += 1
                if digits == cursor:
                    if digits >= length:
                        raise Incomplete()
                    raise CalcError("Invalid expression")
                end = digits
            try:
                value = float(text[index:end])
            except ValueError:
                raise CalcError("Invalid expression") from None
            if math.isinf(value) or math.isnan(value):
                raise CalcError("Math error", "math")
            tokens.append(("num", value))
            index = end
            continue
        word = next((name for name in _WORDS if text.startswith(name, index)), None)
        if word:
            if word in _ALIASES:
                tokens.append(("func", _ALIASES[word]))
            elif word in _INFIX_WORDS:
                tokens.append(("op", word))
            elif word in FUNCTIONS:
                tokens.append(("func", word))
            else:
                tokens.append(("const", _CONSTANTS[word]))
            index += len(word)
            continue
        if char in "πeφ":
            tokens.append(("const", _CONSTANTS[char]))
        elif char == "(":
            tokens.append(("lp", "("))
        elif char == ")":
            tokens.append(("rp", ")"))
        elif char in _SYMBOLS:
            tokens.append(("op", _SYMBOLS[char]))
        else:
            raise CalcError("Invalid expression")
        index += 1
    return tokens


# ! Reads the token list and evaluates one numeric expression.
class _Parser:
    def __init__(self, tokens: list[Token], mode: str, ans: float) -> None:
        self.tokens = tokens
        self.mode = mode
        self.ans = ans
        self.pos = 0

    def peek(self, offset: int = 0) -> Token:
        index = self.pos + offset
        if index >= len(self.tokens):
            return ("eof", None)
        return self.tokens[index]

    def accept(self, kind: str, value: object = None) -> bool:
        token = self.peek()
        if token[0] == kind and (value is None or token[1] == value):
            self.pos += 1
            return True
        return False

    def _starts_value(self) -> bool:
        kind, value = self.peek()
        if kind in ("num", "const", "func", "lp"):
            return True
        return kind == "op" and value in ("√", "∛")

    def parse(self) -> float:
        if not self.tokens:
            raise Incomplete()
        value = self._add()
        if self.pos < len(self.tokens):
            raise CalcError("Invalid expression")
        return value

    def _add(self) -> float:
        value = self._mul()
        while True:
            if self.accept("op", "+"):
                value = self._percent_add(value, 1)
            elif self.accept("op", "-"):
                value = self._percent_add(value, -1)
            else:
                return value

    def _plain_percent(self) -> bool:
        """True when the next term is ``10%`` at the end of this addition."""
        if self.peek()[0] != "num" or self.peek(1) != ("op", "%"):
            return False
        kind, op = self.peek(2)
        return kind == "eof" or (kind == "op" and op in ("+", "-"))

    def _percent_add(self, value: float, sign: float) -> float:
        """``500+10%`` is 550 and ``500-10%`` is 450. A bare ``50%`` stays one half."""
        if not self._plain_percent():
            right = self._mul()
            return value + sign * right
        percent = float(self.peek()[1])
        self.pos += 2
        return value + sign * value * percent / 100

    def _mul(self) -> float:
        value = self._unary()
        while True:
            kind, op = self.peek()
            if kind == "func" and op in INFIX and self.peek(1)[0] != "lp":
                self.pos += 1
                right = self._unary()
                if op == "mod":
                    value = _modulo(value, right)
                elif op == "nCr":
                    value = ncr(value, right)
                else:
                    value = npr(value, right)
            elif kind == "op" and op in ("*", "/", "of"):
                self.pos += 1
                right = self._unary()
                if op == "/":
                    if right == 0:
                        raise CalcError("Cannot divide by zero", "math")
                    value /= right
                else:
                    value *= right
            elif self._starts_value():
                value *= self._power()
            else:
                return value

    def _unary(self) -> float:
        if self.accept("op", "-"):
            return -self._unary()
        if self.accept("op", "+"):
            return self._unary()
        return self._power()

    def _power(self) -> float:
        base = self._postfix()
        if self.accept("op", "^"):
            return power(base, self._unary())
        if self.accept("op", "ʸ√"):
            return root(base, self._unary())
        return base

    def _postfix(self) -> float:
        value = self._primary()
        while True:
            if self.accept("op", "!"):
                value = factorial(value)
            elif self.accept("op", "%"):
                value /= 100
            elif self.accept("op", "²"):
                value = power(value, 2)
            elif self.accept("op", "³"):
                value = power(value, 3)
            else:
                return value

    def _primary(self) -> float:
        if self.peek()[0] == "eof":
            raise Incomplete()
        kind, value = self.tokens[self.pos]
        self.pos += 1
        if kind == "num":
            return self._dms(float(value))
        if kind == "const":
            if value == "pi":
                return math.pi
            if value == "e":
                return math.e
            if value == "phi":
                return _PHI
            return self.ans
        if kind == "lp":
            inner = self._add()
            self._close()
            return inner
        if kind == "func":
            return self._call(str(value))
        if kind == "op" and value == "√":
            return sqrt(self._unary(), self.mode)
        if kind == "op" and value == "∛":
            return cbrt(self._unary(), self.mode)
        raise CalcError("Invalid expression")

    def _close(self) -> None:
        """Consume ``)``. A missing closer at the end of the input is filled in."""
        if self.peek()[0] == "eof":
            return
        if not self.accept("rp"):
            raise CalcError("Invalid expression")

    def _call(self, name: str) -> float:
        arity, func = FUNCTIONS[name]
        if not self.accept("lp"):
            if self.peek()[0] == "eof":
                raise Incomplete()
            raise CalcError("Invalid expression")
        if arity == 0:
            self._close()
            return float(func(self.mode))
        if self.peek()[0] == "eof":
            raise Incomplete()
        if self.peek()[0] == "rp":
            raise CalcError("Invalid expression")
        args = [self._add()]
        while self.accept("op", ","):
            if self.peek()[0] == "eof":
                raise Incomplete()
            if self.peek()[0] == "rp":
                raise CalcError("Invalid expression")
            args.append(self._add())
        self._close()
        if name == "log":
            if len(args) == 1:
                return log10(args[0], self.mode)
            if len(args) == 2:
                return log(args[0], args[1], self.mode)
            raise CalcError("Invalid expression")
        if name == "round":
            if len(args) == 1:
                return round_half(args[0])
            if len(args) == 2:
                return round_half(args[0], args[1])
            raise CalcError("Invalid expression")
        if name in VARARGS:
            return float(FUNCTIONS[name][1](args))
        if len(args) != arity:
            raise CalcError("Invalid expression")
        if arity == 1:
            return float(func(args[0], self.mode))
        return float(func(args[0], args[1], self.mode))

    def _dms(self, degrees: float) -> float:
        if not self.accept("op", "°"):
            return degrees
        total = degrees
        if self.peek()[0] == "num" and self.peek(1) == ("op", "′"):
            total += float(self.peek()[1]) / 60
            self.pos += 2
        if self.peek()[0] == "num" and self.peek(1) == ("op", "″"):
            total += float(self.peek()[1]) / 3600
            self.pos += 2
        return total


def evaluate(expression: str, mode: str = "DEG", ans: float = 0.0) -> float:
    """Evaluate ``expression``. Raises :class:`CalcError` or :class:`Incomplete`."""
    if mode not in ("DEG", "RAD", "GRAD"):
        raise CalcError("Invalid expression")
    try:
        value = _Parser(tokenize(expression), mode, ans).parse()
    except Incomplete:
        raise
    except CalcError:
        raise
    except ZeroDivisionError:
        raise CalcError("Cannot divide by zero", "math") from None
    except (OverflowError, ValueError):
        raise CalcError("Invalid input", "math") from None
    except RecursionError:
        raise CalcError("Invalid expression") from None
    if math.isnan(value) or math.isinf(value):
        raise CalcError("Invalid input", "math")
    return snap(value)


def try_evaluate(expression: str, mode: str = "DEG", ans: float = 0.0) -> Answer:
    """Return ``("ok", value)``, ``("incomplete", None)``, ``("math", None)`` or ``("invalid", None)``.

    The result unpacks as a pair. ``message`` is safe to show when evaluation fails.
    """
    try:
        return Answer("ok", evaluate(expression, mode, ans))
    except Incomplete:
        return Answer("incomplete", None)
    except CalcError as exc:
        kind = exc.kind if exc.kind in ("math", "invalid") else "invalid"
        return Answer(kind, None, str(exc))

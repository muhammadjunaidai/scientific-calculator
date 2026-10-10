# ! Symbolic algebra and calculus. Runs only for variables, equations, calculus, and matrices.

from __future__ import annotations

import re

from engine.functions import Answer, CalcError, Incomplete

_MARKERS = (
    "=", "<", ">", "≤", "≥", "∞", "[",
    "diff(", "diff2(", "integrate(", "definite(", "limit(", "limit+(", "limit-(", "sum(",
    "det(", "inv(", "transpose(", "rank(", "trace(", "eigenvalues(", "eigenvectors(",
    "factor(", "eye(",
)
_BARE = re.compile(r"(?<![A-Za-z_])(x|y|n|k|i|t)(?![A-Za-z0-9_])")

_FUNCS = (
    "eigenvectors", "eigenvalues", "transpose", "definite", "integrate", "diff2",
    "limit+", "limit-", "isprime", "factor", "limit", "floor", "round", "diff", "sign",
    "ceil", "sqrt", "cbrt", "eye", "det", "inv", "rank", "trace", "sum", "gcd", "lcm",
    "sin⁻¹", "cos⁻¹", "tan⁻¹", "csc⁻¹", "sec⁻¹", "cot⁻¹",
    "sinh⁻¹", "cosh⁻¹", "tanh⁻¹", "csch⁻¹", "sech⁻¹", "coth⁻¹",
    "arcsin", "arccos", "arctan",
    "nCr", "nPr", "mod", "phi", "Phi",
    "sqrt", "cbrt", "abs", "log₂", "log2", "log10", "log", "ln",
    "sinh", "cosh", "tanh", "csch", "sech", "coth",
    "sin", "cos", "tan", "csc", "sec", "cot",
    "exp", "pi", "Ans", "ans", "ANS", "of", "C", "P",
)
_WORDS = sorted(_FUNCS, key=len, reverse=True)
_LETTERS = set("xykntabcdf")
_RELATIONS = {"=", "<", ">", "≤", "≥", "<=", ">="}


def is_symbolic(text: str) -> bool:
    """True when the expression needs algebra instead of a plain number."""
    if any(marker in text for marker in _MARKERS):
        return True
    return _BARE.search(text) is not None


def try_solve(expression: str, mode: str = "DEG") -> Answer:
    """Return ``("ok", text)``, ``("incomplete", None)``, ``("math", None)`` or ``("invalid", None)``."""
    try:
        return Answer("ok", solve_text(expression, mode))
    except Incomplete:
        return Answer("incomplete", None)
    except CalcError as exc:
        kind = exc.kind if exc.kind in ("math", "invalid") else "invalid"
        return Answer(kind, None, str(exc))
    except (ValueError, ZeroDivisionError, OverflowError):
        return Answer("math", None, "Invalid matrix")
    except Exception:
        return Answer("math", None, "Math error")


def solve_text(expression: str, mode: str = "DEG") -> str:
    """Solve or simplify one expression. Raises :class:`CalcError`."""
    import sympy as sp

    pieces = _split_top(expression, ";")
    if not pieces:
        raise Incomplete()
    parsed = [_Parser(tokenize(piece), mode).parse() for piece in pieces]
    if len(parsed) > 1:
        return _system(sp, parsed)
    return _one(sp, parsed[0])


def tokenize(text: str) -> list[tuple[str, str]]:
    """Split a symbolic expression into ``(kind, text)`` tokens."""
    if len(text) > 800:
        raise CalcError("Invalid expression")
    tokens: list[tuple[str, str]] = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if char.isdigit() or (char == "." and index + 1 < length and text[index + 1].isdigit()):
            start = index
            index += 1
            while index < length and (text[index].isdigit() or text[index] == "."):
                index += 1
            if index < length and text[index] in "eE" and index + 1 < length and text[index + 1].isdigit():
                index += 2
                while index < length and text[index].isdigit():
                    index += 1
            tokens.append(("num", text[start:index]))
            continue
        word = next((name for name in _WORDS if text.startswith(name, index)), None)
        if word:
            if word == "of":
                tokens.append(("op", "of"))
            elif word in ("C", "P"):
                tokens.append(("func", "nCr" if word == "C" else "nPr"))
            elif word in ("phi", "Phi"):
                tokens.append(("const", "phi"))
            else:
                kind = "const" if word in ("pi", "Ans", "ans", "ANS") else "func"
                tokens.append((kind, "pi" if word == "pi" else "Ans" if word.lower() == "ans" else word))
            index += len(word)
            continue
        pair = text[index:index + 2]
        if pair in ("<=", ">=", "−∞"):
            tokens.append(("op", pair))
            index += 2
            continue
        if char in _LETTERS or char == "i":
            start = index
            index += 1
            while index < length and text[index] in "₀₁₂₃₄₅₆₇₈₉":
                index += 1
            if text.startswith("_{", index):
                end = text.find("}", index + 2)
                if end < 0:
                    raise CalcError("Invalid expression")
                index = end + 1
            tokens.append(("name", text[start:index]))
            continue
        if text.startswith("_{", index):
            end = text.find("}", index + 2)
            if end < 0:
                raise CalcError("Invalid expression")
            tokens.append(("name", text[index:end + 1]))
            index = end + 1
            continue
        mapped = {
            "π": ("const", "pi"), "e": ("const", "e"), "φ": ("const", "phi"), "∞": ("const", "oo"),
            "(": ("lp", "("), ")": ("rp", ")"),
            "[": ("lb", "["), "]": ("rb", "]"),
            "+": ("op", "+"), "-": ("op", "-"), "−": ("op", "-"), "–": ("op", "-"),
            "*": ("op", "*"), "×": ("op", "*"), "·": ("op", "*"),
            "/": ("op", "/"), "÷": ("op", "/"),
            "^": ("op", "^"), "!": ("op", "!"), "%": ("op", "%"),
            ",": ("op", ","), ";": ("op", ";"),
            "=": ("op", "="), "<": ("op", "<"), ">": ("op", ">"),
            "≤": ("op", "≤"), "≥": ("op", "≥"),
            "√": ("op", "√"), "∛": ("op", "∛"),
            "²": ("op", "²"), "³": ("op", "³"), "°": ("op", "°"),
        }.get(char)
        if mapped is None:
            raise CalcError("Invalid expression")
        tokens.append(mapped)
        index += 1
    return tokens


def _split_top(text: str, separator: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    for char in text:
        if char in "([":
            depth += 1
        elif char in ")]":
            depth = max(0, depth - 1)
        if char == separator and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(char)
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


# ! Reads the token list and builds the SymPy form of one symbolic expression.
class _Parser:
    def __init__(self, tokens: list[tuple[str, str]], mode: str) -> None:
        self.tokens = tokens
        self.mode = mode
        self.pos = 0

    def parse(self):
        if not self.tokens:
            raise Incomplete()
        value = self._rel()
        if self.pos < len(self.tokens):
            raise CalcError("Invalid expression")
        return value

    def peek(self, offset: int = 0) -> tuple[str, str]:
        index = self.pos + offset
        if index >= len(self.tokens):
            return ("eof", "")
        return self.tokens[index]

    def accept(self, kind: str, value: str | None = None) -> bool:
        got, text = self.peek()
        if got != kind or (value is not None and text != value):
            return False
        self.pos += 1
        return True

    def _rel(self):
        left = self._add()
        op = self.peek()[1]
        if self.peek()[0] == "op" and op in _RELATIONS:
            self.pos += 1
            if self.peek()[0] == "eof":
                raise Incomplete()
            right = self._add()
            return ("rel", op, left, right)
        return left

    def _add(self):
        import sympy as sp

        value = self._mul()
        while True:
            if self.accept("op", "+"):
                value = self._percent_add(sp, value, 1)
            elif self.accept("op", "-"):
                value = self._percent_add(sp, value, -1)
            else:
                return value

    def _percent_add(self, sp, value, sign: int):
        """``x+10%`` grows by 10 percent. A trailing percent on its own stays a fraction."""
        if self.peek()[0] != "num" or self.peek(1) != ("op", "%"):
            right = self._mul()
            return value + sign * right
        kind, op = self.peek(2)
        if not (kind == "eof" or (kind == "op" and op in ("+", "-"))):
            right = self._mul()
            return value + sign * right
        raw = str(self.peek()[1])
        self.pos += 2
        percent = sp.Integer(raw) if raw.isdigit() else sp.Float(raw)
        return value + sign * value * percent / 100

    def _mul(self):
        value = self._unary()
        while True:
            kind, op = self.peek()
            if kind == "func" and op in ("mod", "nCr", "nPr") and self.peek(1)[0] != "lp":
                self.pos += 1
                right = self._unary()
                value = _apply(op, [value, right], self.mode)
            elif kind == "op" and op in ("*", "/", "of"):
                self.pos += 1
                right = self._unary()
                value = value / right if op == "/" else value * right
            elif _starts(kind, op):
                value *= self._power()
            else:
                return value

    def _unary(self):
        if self.accept("op", "-"):
            return -self._unary()
        if self.accept("op", "+"):
            return self._unary()
        return self._power()

    def _power(self):
        base = self._postfix()
        if self.accept("op", "^"):
            if self.peek()[0] == "eof":
                raise Incomplete()
            return base ** self._unary()
        return base

    def _postfix(self):
        import sympy as sp

        value = self._primary()
        while True:
            if self.accept("op", "!"):
                value = sp.factorial(value)
            elif self.accept("op", "%"):
                value = value / 100
            elif self.accept("op", "²"):
                value = value ** 2
            elif self.accept("op", "³"):
                value = value ** 3
            elif self.accept("op", "°"):
                value = value * sp.pi / 180
            else:
                return value

    def _primary(self):
        import sympy as sp

        kind, text = self.peek()
        if kind == "eof":
            raise Incomplete()
        if kind == "num":
            self.pos += 1
            if "." in text:
                number = sp.Float(text)
            elif text.isdigit():
                number = sp.Integer(text)
            else:
                raise CalcError("Invalid expression")
            return number
        if kind == "const":
            self.pos += 1
            if text == "pi":
                return sp.pi
            if text == "e":
                return sp.E
            if text == "phi":
                return (1 + sp.sqrt(5)) / 2
            if text == "oo":
                return sp.oo
            return sp.Symbol("Ans")
        if kind == "name":
            self.pos += 1
            if text == "i":
                return sp.I
            return sp.Symbol(text, real=True)
        if self.accept("lp"):
            inner = self._rel()
            self._close("rp")
            return inner
        if kind == "func":
            self.pos += 1
            return self._call(text)
        if self.accept("op", "√"):
            return sp.sqrt(self._unary())
        if self.accept("op", "∛"):
            return sp.cbrt(self._unary())
        if self.accept("lb"):
            return self._bracket()
        raise CalcError("Invalid expression")

    def _close(self, kind: str) -> None:
        if self.peek()[0] == "eof":
            if kind == "rp":
                return
            raise Incomplete()
        if not self.accept(kind):
            raise CalcError("Invalid expression")

    def _call(self, name: str):
        if not self.accept("lp"):
            if self.peek()[0] == "eof":
                raise Incomplete()
            raise CalcError("Invalid expression")
        if self.peek()[0] == "eof":
            raise Incomplete()
        args = [self._rel()]
        while self.accept("op", ","):
            if self.peek()[0] in ("eof", "rp"):
                raise Incomplete() if self.peek()[0] == "eof" else CalcError("Invalid expression")
            args.append(self._rel())
        self._close("rp")
        return _apply(name, args, self.mode)

    def _bracket(self):
        import sympy as sp

        if self.accept("lb"):
            rows = [self._row_body()]
            while self.accept("op", ","):
                if not self.accept("lb"):
                    raise CalcError("Invalid expression")
                rows.append(self._row_body())
            self._close("rb")
            width = len(rows[0])
            if any(len(row) != width for row in rows):
                raise CalcError("Invalid expression")
            return sp.Matrix(rows)
        items = [self._rel()]
        while self.accept("op", ","):
            if self.peek()[0] == "eof":
                raise Incomplete()
            items.append(self._rel())
        self._close("rb")
        return sp.Matrix([items])

    def _row_body(self) -> list:
        items = [self._rel()]
        while self.accept("op", ","):
            items.append(self._rel())
        self._close("rb")
        return items


def _starts(kind: str, op: str) -> bool:
    if kind in ("num", "const", "name", "func", "lp", "lb"):
        return True
    return kind == "op" and op in ("√", "∛")


def _apply(name: str, args: list, mode: str):
    import sympy as sp

    trig = {
        "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
        "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
        "arcsin": sp.asin, "arccos": sp.acos, "arctan": sp.atan,
        "sin⁻¹": sp.asin, "cos⁻¹": sp.acos, "tan⁻¹": sp.atan,
        "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
        "asinh": sp.asinh, "acosh": sp.acosh, "atanh": sp.atanh,
        "sinh⁻¹": sp.asinh, "cosh⁻¹": sp.acosh, "tanh⁻¹": sp.atanh,
    }
    reciprocal = {"csc": sp.sin, "sec": sp.cos, "cot": sp.tan, "csch": sp.sinh, "sech": sp.cosh, "coth": sp.tanh}
    inverse_reciprocal = {
        "acsc": sp.asin, "asec": sp.acos, "acot": sp.atan,
        "csc⁻¹": sp.asin, "sec⁻¹": sp.acos, "cot⁻¹": sp.atan,
        "acsch": sp.asinh, "asech": sp.acosh, "acoth": sp.atanh,
        "csch⁻¹": sp.asinh, "sech⁻¹": sp.acosh, "coth⁻¹": sp.atanh,
    }
    if name in trig or name in reciprocal or name in inverse_reciprocal:
        if len(args) != 1:
            raise CalcError("Invalid expression")
        arg = args[0]
        inverse = name in inverse_reciprocal or name in ("asin", "acos", "atan", "arcsin", "arccos", "arctan", "sin⁻¹", "cos⁻¹", "tan⁻¹", "asinh", "acosh", "atanh", "sinh⁻¹", "cosh⁻¹", "tanh⁻¹")
        if name in reciprocal:
            value = 1 / trig_angle(reciprocal[name], arg, mode, inverse=False)
        elif name in inverse_reciprocal:
            value = trig_angle(inverse_reciprocal[name], 1 / arg, mode, inverse=True)
        else:
            value = trig_angle(trig[name], arg, mode, inverse=inverse)
        return value
    if name in ("log", "log10"):
        if len(args) == 1:
            return sp.log(args[0], 10)
        if len(args) == 2:
            return sp.log(args[0], args[1])
        raise CalcError("Invalid expression")
    if name in ("log2", "log₂"):
        if len(args) != 1:
            raise CalcError("Invalid expression")
        return sp.log(args[0], 2)
    if name == "ln":
        if len(args) != 1:
            raise CalcError("Invalid expression")
        return sp.log(args[0])
    if name == "sqrt":
        return sp.sqrt(args[0])
    if name == "cbrt":
        return sp.cbrt(args[0])
    if name == "abs":
        return sp.Abs(args[0])
    if name == "exp":
        return sp.exp(args[0])
    if name == "nCr":
        return sp.binomial(args[0], args[1])
    if name == "nPr":
        return sp.factorial(args[0]) / sp.factorial(args[0] - args[1])
    if name == "mod":
        return sp.Mod(args[0], args[1])
    if name in ("floor", "ceil", "sign"):
        if len(args) != 1:
            raise CalcError("Invalid expression")
        funcs = {"floor": sp.floor, "ceil": sp.ceiling, "sign": sp.sign}
        return funcs[name](args[0])
    if name == "round":
        if len(args) != 1:
            raise CalcError("Invalid expression")
        return sp.floor(args[0] + sp.Rational(1, 2))
    if name in ("gcd", "lcm"):
        if len(args) < 2:
            raise CalcError("Invalid expression")
        reduce = sp.gcd if name == "gcd" else sp.ilcm
        value = args[0]
        for arg in args[1:]:
            value = reduce(value, arg)
        return value
    if name in ("diff", "diff2"):
        order = 2 if name == "diff2" else 1
        if name == "diff" and len(args) == 3:
            target, var, order = args
        elif len(args) == 2 and name == "diff":
            target, var = args
        elif len(args) == 1:
            target, var = args[0], _default_var(args[0])
        elif len(args) == 2 and name == "diff2":
            target, var = args
        else:
            raise CalcError("Invalid expression")
        try:
            order_n = int(order)
        except (TypeError, ValueError):
            raise CalcError("Invalid expression") from None
        if order_n < 1 or order_n > 6:
            raise CalcError("Invalid expression")
        if order_n == 1:
            return sp.Derivative(target, var)
        return sp.Derivative(target, var, order_n)
    if name == "integrate":
        target, var = _expr_var(args, 1)
        return sp.Integral(target, var)
    if name == "definite":
        if len(args) == 3:
            target, lower, upper = args
            var = _default_var(target)
        elif len(args) == 4:
            target, var, lower, upper = args
        else:
            raise CalcError("Invalid expression")
        return sp.Integral(target, (var, lower, upper))
    if name in ("limit", "limit+", "limit-"):
        direction = "+" if name == "limit+" else "-" if name == "limit-" else "+-"
        if len(args) == 2:
            target, point = args
            var = _default_var(target)
        elif len(args) == 3:
            target, var, point = args
        else:
            raise CalcError("Invalid expression")
        return sp.Limit(target, var, point, dir=direction)
    if name == "sum":
        if len(args) == 3:
            target, start, end = args
            var = _default_var(target)
        elif len(args) == 4:
            target, var, start, end = args
        else:
            raise CalcError("Invalid expression")
        return sp.Sum(target, (var, start, end))
    if name == "factor":
        if len(args) != 1:
            raise CalcError("Invalid expression")
        if getattr(args[0], "free_symbols", None):
            return ("text", pretty(sp.factor(args[0])))
        return ("text", _factor_text(args[0]))
    if name == "eye":
        if len(args) != 1:
            raise CalcError("Invalid expression")
        size = args[0]
        if not getattr(size, "is_integer", False) or int(size) < 1 or int(size) > 6:
            raise CalcError("Invalid expression")
        return sp.eye(int(size))
    matrix_name = name
    if matrix_name in ("det", "inv", "transpose", "rank", "trace", "eigenvalues", "eigenvectors"):
        if len(args) != 1:
            raise CalcError("Invalid expression")
        matrix = _as_matrix(args[0])
        if matrix_name == "det":
            return matrix.det()
        if matrix_name == "inv":
            try:
                return sp.simplify(matrix.inv())
            except ValueError as exc:
                raise CalcError("Invalid input", "math") from exc
        if matrix_name == "transpose":
            return matrix.T
        if matrix_name == "rank":
            return sp.Integer(matrix.rank())
        if matrix_name == "trace":
            return matrix.trace()
        if matrix_name == "eigenvalues":
            values = []
            for value, mult in matrix.eigenvals().items():
                values.extend([sp.simplify(value)] * int(mult))
            return sp.Matrix(values)
        return ("text", _eigenvector_text(sp, matrix))
    raise CalcError("Invalid expression")


def trig_angle(func, arg, mode: str, inverse: bool):
    """Use degrees for plain numbers. Symbolic angles stay in radians so identities hold."""
    import sympy as sp

    if inverse:
        value = func(arg)
        if mode == "DEG" and not arg.free_symbols:
            value = value * 180 / sp.pi
        elif mode == "GRAD" and not arg.free_symbols:
            value = value * 200 / sp.pi
        return value
    if mode == "DEG" and not getattr(arg, "free_symbols", True):
        arg = arg * sp.pi / 180
    elif mode == "GRAD" and not getattr(arg, "free_symbols", True):
        arg = arg * sp.pi / 200
    return func(arg)


def _default_var(expr):
    import sympy as sp

    names = [str(symbol) for symbol in expr.free_symbols]
    for preferred in ("x", "y", "n", "k", "t"):
        if preferred in names:
            return sp.Symbol(preferred, real=True)
    if names:
        return sp.Symbol(sorted(names)[0], real=True)
    return sp.Symbol("x", real=True)


def _expr_var(args: list, minimum: int):
    if len(args) == minimum:
        return args[0], _default_var(args[0])
    if len(args) == minimum + 1:
        return args[0], args[1]
    raise CalcError("Invalid expression")


def _as_matrix(expr):
    import sympy as sp

    if isinstance(expr, sp.MatrixBase):
        return expr
    raise CalcError("Invalid expression")


def _factor_text(expr) -> str:
    import sympy as sp

    try:
        number = int(expr)
    except (TypeError, ValueError):
        raise CalcError("Invalid expression") from None
    if number == 0:
        return "0"
    sign = "−" if number < 0 else ""
    factors = sp.factorint(abs(number))
    if not factors:
        return f"{sign}1"
    parts = []
    supers = "²³⁴⁵⁶⁷⁸⁹"
    for prime, exp in factors.items():
        if exp == 1:
            parts.append(str(prime))
        elif 2 <= exp <= 9:
            parts.append(f"{prime}{supers[exp - 2]}")
        else:
            parts.append(f"{prime}^{exp}")
    return f"{sign}{'×'.join(parts)}"


def _eigenvector_text(sp, matrix) -> str:
    parts = []
    for value, _mult, vectors in matrix.eigenvects():
        shown = ", ".join(pretty(sp.simplify(vector)) for vector in vectors)
        parts.append(f"{pretty(sp.simplify(value))}: {shown}")
    if not parts:
        raise CalcError("Invalid input", "math")
    return "; ".join(parts)


def _one(sp, expr) -> str:
    if isinstance(expr, tuple) and expr and expr[0] == "text":
        return str(expr[1])
    if isinstance(expr, tuple) and expr and expr[0] == "rel":
        _, op, left, right = expr
        if op in ("=",):
            return _equation(sp, sp.Eq(left, right))
        relation = {">": sp.StrictGreaterThan, "<": sp.StrictLessThan, "≥": sp.GreaterThan, ">=": sp.GreaterThan, "≤": sp.LessThan, "<=": sp.LessThan}[op]
        return _inequality(sp, relation(left, right))
    if isinstance(expr, sp.MatrixBase):
        return pretty(sp.simplify(expr))
    worked = _finish(sp, expr)
    if isinstance(expr, sp.Integral) and _indefinite(expr):
        return f"{pretty(worked)} + C"
    return pretty(worked)


def _finish(sp, expr):
    if isinstance(expr, (sp.Derivative, sp.Integral, sp.Limit, sp.Sum)):
        try:
            done = expr.doit()
        except Exception as exc:
            raise CalcError("Math error", "math") from exc
        done = sp.simplify(done)
        if isinstance(expr, (sp.Derivative, sp.Integral)):
            done = sp.expand(done)
        return done
    if expr.has(sp.Derivative, sp.Integral, sp.Limit, sp.Sum):
        expr = expr.doit()
    if expr.has(sp.I):
        return sp.expand(expr)
    trig = sp.trigsimp(expr)
    if trig != expr and sp.count_ops(trig) <= sp.count_ops(expr):
        return sp.simplify(trig)
    if _product_of_sums(expr):
        return sp.expand(expr)
    if isinstance(expr, sp.Add):
        combined = sp.together(expr)
        simplified = sp.simplify(combined)
        return simplified if sp.count_ops(simplified) <= sp.count_ops(combined) else combined
    return sp.simplify(sp.expand(expr))


def _product_of_sums(expr) -> bool:
    import sympy as sp

    return isinstance(expr, sp.Mul) and any(isinstance(arg, sp.Add) for arg in expr.args)


def _indefinite(expr) -> bool:
    return all(len(limit) == 1 for limit in expr.limits)


def _equation(sp, eq) -> str:
    symbols = _order_symbols(eq.free_symbols)
    if not symbols:
        if sp.simplify(eq.lhs - eq.rhs) == 0:
            return "True"
        return "No solution"
    var = symbols[0]
    try:
        solutions = sp.solve(eq, var)
    except NotImplementedError:
        solution_set = sp.solveset(eq, var, domain=sp.S.Reals)
        solutions = list(solution_set) if isinstance(solution_set, sp.FiniteSet) else []
        if not solutions and not isinstance(solution_set, sp.FiniteSet):
            raise CalcError("Math error", "math")
    except Exception as exc:
        raise CalcError("Math error", "math") from exc
    kept = []
    for solution in solutions:
        solution = sp.simplify(solution)
        if solution.has(sp.I) and solution.is_real is False:
            continue
        if _satisfies(sp, eq, var, solution):
            kept.append(solution)
    if not kept and solutions:
        kept = [sp.simplify(solution) for solution in solutions]
    return _format_many(var, _sort_values(sp, kept))


def _satisfies(sp, eq, var, solution) -> bool:
    try:
        delta = sp.simplify((eq.lhs - eq.rhs).subs(var, solution))
    except Exception:
        return False
    if delta == 0:
        return True
    try:
        return abs(complex(sp.N(delta))) < 1e-8
    except Exception:
        return False


def _inequality(sp, relation) -> str:
    symbols = _order_symbols(relation.free_symbols)
    if not symbols:
        return "True" if bool(relation) else "No solution"
    try:
        reduced = sp.reduce_inequalities(relation, [symbols[0]])
    except Exception as exc:
        raise CalcError("Math error", "math") from exc
    return _pretty_condition(reduced)


def _system(sp, parts: list) -> str:
    equations = []
    for part in parts:
        if not (isinstance(part, tuple) and part[0] == "rel" and part[1] == "="):
            raise CalcError("Invalid expression")
        equations.append(sp.Eq(part[2], part[3]))
    symbols = _order_symbols(set().union(*(eq.free_symbols for eq in equations)))
    try:
        found = sp.solve(equations, symbols, dict=True)
    except Exception as exc:
        raise CalcError("Math error", "math") from exc
    if not found:
        return "No solution"
    lines = []
    for item in found:
        ordered = [symbol for symbol in symbols if symbol in item]
        lines.append(", ".join(f"{pretty(symbol)} = {pretty(sp.simplify(item[symbol]))}" for symbol in ordered))
    return " or ".join(lines)


def _order_symbols(symbols) -> list:
    rank = {name: index for index, name in enumerate(("x", "y", "z", "n", "k", "t"))}

    def key(symbol):
        name = str(symbol)
        return (rank.get(name, 50), name)

    return sorted(symbols, key=key)


def _sort_values(sp, values: list) -> list:
    def key(value):
        try:
            return (0, float(sp.N(value)))
        except Exception:
            return (1, str(value))

    return sorted(values, key=key)


def _format_many(var, values: list) -> str:
    if not values:
        return "No solution"
    return " or ".join(f"{pretty(var)} = {pretty(value)}" for value in values)


def _pretty_condition(expr) -> str:
    import sympy as sp

    if isinstance(expr, sp.And):
        parts = []
        for arg in expr.args:
            text = _pretty_condition(arg)
            if text and "∞" not in text:
                parts.append(text)
        return " and ".join(parts) if parts else pretty(expr)
    if isinstance(expr, sp.Or):
        return " or ".join(_pretty_condition(arg) for arg in expr.args)
    return pretty(expr)


def pretty(expr) -> str:
    """One-line calculator text for a SymPy object."""
    import sympy as sp

    if isinstance(expr, sp.Add) and _numeric_denominators(expr):
        expr = sp.together(expr)
    if isinstance(expr, sp.Equality):
        return f"{pretty(expr.lhs)} = {pretty(expr.rhs)}"
    if isinstance(expr, sp.StrictLessThan):
        return f"{pretty(expr.lhs)} < {pretty(expr.rhs)}"
    if isinstance(expr, sp.LessThan):
        return f"{pretty(expr.lhs)} ≤ {pretty(expr.rhs)}"
    if isinstance(expr, sp.StrictGreaterThan):
        return f"{pretty(expr.lhs)} > {pretty(expr.rhs)}"
    if isinstance(expr, sp.GreaterThan):
        return f"{pretty(expr.lhs)} ≥ {pretty(expr.rhs)}"
    if isinstance(expr, sp.MatrixBase):
        if expr.rows == 1 or expr.cols == 1:
            return f"[{', '.join(pretty(value) for value in expr)}]"
        rows = [
            f"[{', '.join(pretty(expr[index, column]) for column in range(expr.cols))}]"
            for index in range(expr.rows)
        ]
        return f"[{', '.join(rows)}]"
    if isinstance(expr, sp.Add):
        return _pretty_add(expr)
    if isinstance(expr, sp.Mul):
        return _pretty_mul(expr)
    if isinstance(expr, sp.Pow):
        return _pretty_pow(expr.base, expr.exp)
    if expr == sp.pi:
        return "π"
    if expr == sp.E:
        return "e"
    if expr == sp.I:
        return "i"
    if expr == sp.oo:
        return "∞"
    if expr == -sp.oo:
        return "−∞"
    if isinstance(expr, sp.Rational):
        return _signed(expr.p, expr.q)
    if isinstance(expr, sp.Integer):
        return _signed(int(expr), 1)
    if isinstance(expr, sp.Float):
        return _signed_text(f"{float(expr):.12g}")
    if isinstance(expr, sp.Symbol):
        return str(expr)
    if isinstance(expr, sp.Abs):
        return f"|{pretty(expr.args[0])}|"
    if isinstance(expr, sp.Function):
        label = _FUNC_LABEL.get(expr.func, expr.func.__name__)
        inside = ", ".join(pretty(arg) for arg in expr.args)
        return f"{label}({inside})"
    text = str(expr).replace("**", "^")
    return text.replace("-", "−")


_FUNC_LABEL = {}


def _init_labels() -> None:
    import sympy as sp

    names = {
        sp.sin: "sin", sp.cos: "cos", sp.tan: "tan", sp.asin: "sin⁻¹", sp.acos: "cos⁻¹", sp.atan: "tan⁻¹",
        sp.sinh: "sinh", sp.cosh: "cosh", sp.tanh: "tanh", sp.log: "log", sp.exp: "exp",
        sp.sqrt: "√", sp.cbrt: "∛", sp.factorial: "!",
    }
    _FUNC_LABEL.update(names)


def _numeric_denominators(expr) -> bool:
    """True when every term shares one numeric denominator, so it can be one fraction."""
    import sympy as sp

    denoms = []
    for term in sp.Add.make_args(expr):
        _numer, denom = sp.fraction(sp.together(term))
        if denom.free_symbols:
            return False
        denoms.append(sp.Integer(denom) if denom.is_integer else denom)
    return bool(denoms) and all(denom == denoms[0] and denom != 1 for denom in denoms)


def _degree(term) -> int:
    """Polynomial degree in the term's variables. Plain numbers count as degree 0."""
    import sympy as sp

    symbols = list(getattr(term, "free_symbols", ()))
    if not symbols:
        return 0
    try:
        return int(sum(sp.degree(term, symbol) for symbol in symbols))
    except Exception:
        return 0


def _pretty_add(expr) -> str:
    import sympy as sp

    terms = list(sp.Add.make_args(expr))
    functions = any(term.has(sp.Function) for term in terms)

    def sort_key(term):
        negative = term.could_extract_minus_sign()
        if functions:
            return (negative, -_degree(term))
        return (-_degree(term), negative)

    terms.sort(key=sort_key)
    parts: list[str] = []
    for index, term in enumerate(terms):
        text = pretty(term)
        if index == 0:
            parts.append(text)
        elif text.startswith("−"):
            parts.append(f" − {text[1:]}")
        else:
            parts.append(f" + {text}")
    return "".join(parts)


def _pretty_mul(expr) -> str:
    import sympy as sp

    numer, denom = sp.fraction(expr)
    if denom != 1:
        return f"{_pretty_piece(numer, wrap_mul=False)}/{_pretty_piece(denom, wrap_mul=True)}"
    return _pretty_product(expr)


def _pretty_piece(expr, wrap_mul: bool = True) -> str:
    import sympy as sp

    text = pretty(expr)
    if isinstance(expr, sp.Add) or (wrap_mul and isinstance(expr, sp.Mul)):
        return f"({text})"
    return text


def _pretty_product(expr) -> str:
    import sympy as sp

    if not isinstance(expr, sp.Mul):
        return pretty(expr)
    coeff, factors = expr.as_coeff_mul()
    if not factors:
        return pretty(coeff)
    sign = ""
    if coeff < 0:
        sign = "−"
        coeff = -coeff
    body = "".join(_pretty_factor(factor) for factor in factors)
    if body.startswith("·"):
        body = body[1:]
    if coeff == 1:
        return f"{sign}{body}"
    return f"{sign}{pretty(coeff)}{body}"


def _pretty_factor(factor) -> str:
    import sympy as sp

    if isinstance(factor, sp.Add):
        return f"({pretty(factor)})"
    text = pretty(factor)
    if isinstance(factor, sp.Function):
        return text if text.startswith("√") else f"·{text}"
    if isinstance(factor, (sp.Symbol, sp.Pow)) or factor in (sp.I, sp.pi, sp.E):
        return text
    if isinstance(factor, sp.Mul):
        return f"({text})"
    return text


def _pretty_pow(base, exp) -> str:
    import sympy as sp

    if exp == sp.Rational(1, 2):
        inner = pretty(base)
        if isinstance(base, (sp.Add, sp.Mul, sp.Pow)):
            return f"√({inner})"
        return f"√{inner}" if isinstance(base, (sp.Integer, sp.Symbol)) else f"√({inner})"
    base_text = pretty(base)
    if isinstance(base, (sp.Add, sp.Mul, sp.Pow)):
        base_text = f"({base_text})"
    if exp == 2 and not isinstance(base, (sp.Add, sp.Mul, sp.Pow)):
        return f"{base_text}²"
    if exp == 3 and not isinstance(base, (sp.Add, sp.Mul, sp.Pow)):
        return f"{base_text}³"
    if exp == -1:
        return f"1/{base_text}"
    exp_text = pretty(exp)
    if isinstance(exp, (sp.Add, sp.Mul, sp.Pow)):
        exp_text = f"({exp_text})"
    return f"{base_text}^{exp_text}"


def _signed(numerator: int, denominator: int) -> str:
    sign = "−" if numerator < 0 else ""
    numerator = abs(int(numerator))
    if denominator == 1:
        return f"{sign}{numerator}"
    return f"{sign}{numerator}/{denominator}"


def _signed_text(text: str) -> str:
    return text.replace("-", "−")


_init_labels()

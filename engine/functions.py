# ! Function registry and angle-mode conversions. Exact combinations use SymPy; factorial uses gamma.

from __future__ import annotations

import math
import random
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable

from .formatter import snap

_RADIANS = {"DEG": math.pi / 180, "RAD": 1.0, "GRAD": math.pi / 200}


# ! A calculator failure that is safe to show. kind is math, invalid, or incomplete.
class CalcError(Exception):

    def __init__(self, message: str, kind: str = "invalid") -> None:
        super().__init__(message)
        self.kind = kind


# ! The expression is still being typed, so the calculator waits instead of reporting an error.
class Incomplete(CalcError):

    def __init__(self) -> None:
        super().__init__("Incomplete", "incomplete")


def _math(message: str = "Invalid input") -> CalcError:
    return CalcError(message, "math")


# ! A result pair (kind, value) plus a message that can be shown on screen.
class Answer(tuple):

    message: str

    def __new__(cls, kind: str, value, message: str = ""):
        item = super().__new__(cls, (kind, value))
        item.message = message
        return item


def to_radians(value: float, mode: str) -> float:
    try:
        return value * _RADIANS[mode]
    except KeyError:
        raise CalcError("Invalid expression") from None


def from_radians(value: float, mode: str) -> float:
    return snap(value / _RADIANS[mode])


def _trig(value: float) -> float:
    value = snap(value)
    return 0.0 if value == 0 else value


def _require(ok: bool) -> None:
    if not ok:
        raise _math()


def _integer(value: float) -> int:
    if abs(value - round(value)) > 1e-9:
        raise _math()
    return int(round(value))


def sin(value: float, mode: str) -> float:
    return _trig(math.sin(to_radians(value, mode)))


def cos(value: float, mode: str) -> float:
    return _trig(math.cos(to_radians(value, mode)))


def tan(value: float, mode: str) -> float:
    radians = to_radians(value, mode)
    adjacent = math.cos(radians)
    if abs(adjacent) < 1e-12:
        raise _math()
    return _trig(math.sin(radians) / adjacent)


def csc(value: float, mode: str) -> float:
    result = sin(value, mode)
    if result == 0:
        raise _math()
    return _trig(1 / result)


def sec(value: float, mode: str) -> float:
    result = cos(value, mode)
    if result == 0:
        raise _math()
    return _trig(1 / result)


def cot(value: float, mode: str) -> float:
    result = tan(value, mode)
    if result == 0:
        raise _math()
    return _trig(1 / result)


def asin(value: float, mode: str) -> float:
    _require(-1 <= value <= 1)
    return from_radians(math.asin(value), mode)


def acos(value: float, mode: str) -> float:
    _require(-1 <= value <= 1)
    return from_radians(math.acos(value), mode)


def atan(value: float, mode: str) -> float:
    return from_radians(math.atan(value), mode)


def acsc(value: float, mode: str) -> float:
    _require(abs(value) >= 1)
    return from_radians(math.asin(1 / value), mode)


def asec(value: float, mode: str) -> float:
    _require(abs(value) >= 1)
    return from_radians(math.acos(1 / value), mode)


def acot(value: float, mode: str) -> float:
    if value == 0:
        return from_radians(math.pi / 2, mode)
    return from_radians(math.atan(1 / value), mode)


def sinh(value: float, _mode: str) -> float:
    return snap(math.sinh(value))


def cosh(value: float, _mode: str) -> float:
    return snap(math.cosh(value))


def tanh(value: float, _mode: str) -> float:
    return snap(math.tanh(value))


def csch(value: float, _mode: str) -> float:
    _require(value != 0)
    return snap(1 / math.sinh(value))


def sech(value: float, _mode: str) -> float:
    return snap(1 / math.cosh(value))


def coth(value: float, _mode: str) -> float:
    _require(value != 0)
    return snap(1 / math.tanh(value))


def asinh(value: float, _mode: str) -> float:
    return snap(math.asinh(value))


def acosh(value: float, _mode: str) -> float:
    _require(value >= 1)
    return snap(math.acosh(value))


def atanh(value: float, _mode: str) -> float:
    _require(-1 < value < 1)
    return snap(math.atanh(value))


def acsch(value: float, _mode: str) -> float:
    _require(value != 0)
    return snap(math.asinh(1 / value))


def asech(value: float, _mode: str) -> float:
    _require(0 < value <= 1)
    return snap(math.acosh(1 / value))


def acoth(value: float, _mode: str) -> float:
    _require(abs(value) > 1)
    return snap(math.atanh(1 / value))


def log10(value: float, _mode: str) -> float:
    _require(value > 0)
    return snap(math.log10(value))


def ln(value: float, _mode: str) -> float:
    _require(value > 0)
    return snap(math.log(value))


def log2(value: float, _mode: str) -> float:
    _require(value > 0)
    return snap(math.log2(value))


def log(value: float, base: float, _mode: str) -> float:
    """``log(x)`` is base 10. ``log(x, base)`` is an arbitrary base."""
    if base == 10 or base is None:
        return log10(value, _mode)
    _require(value > 0 and base > 0 and base != 1)
    return snap(math.log(value) / math.log(base))


def sqrt(value: float, _mode: str) -> float:
    _require(value >= 0)
    return snap(math.sqrt(value))


def cbrt(value: float, _mode: str) -> float:
    return snap(math.copysign(abs(value) ** (1 / 3), value))


def power(base: float, exponent: float) -> float:
    if base == 0 and exponent < 0:
        raise _math("Cannot divide by zero")
    try:
        result = math.pow(base, exponent)
    except (ValueError, OverflowError):
        raise _math() from None
    if math.isnan(result) or math.isinf(result):
        raise _math()
    return snap(result)


def root(degree: float, value: float) -> float:
    if degree == 0:
        raise _math()
    if value < 0:
        _require(abs(degree - round(degree)) < 1e-9 and int(round(degree)) % 2 == 1)
        return snap(-power(-value, 1 / degree))
    return power(value, 1 / degree)


def absolute(value: float, _mode: str) -> float:
    return abs(value)


def _gamma(value: float) -> float:
    """Gamma via mpmath, then SciPy, then the standard library."""
    try:
        import mpmath
        result = float(mpmath.gamma(value))
    except Exception:
        try:
            from scipy.special import gamma
            result = float(gamma(value))
        except Exception:
            result = float(math.gamma(value))
    if math.isnan(result) or math.isinf(result):
        raise _math()
    return result


def factorial(value: float) -> float:
    if abs(value - round(value)) > 1e-9:
        _require(value > -1)
        return snap(_gamma(value + 1))
    number = int(round(value))
    if number < 0:
        raise _math()
    if number > 170:
        raise _math()
    try:
        import sympy
        return float(sympy.factorial(number))
    except Exception:
        return float(math.factorial(number))


def ncr(n_value: float, r_value: float) -> float:
    n_number, r_number = _integer(n_value), _integer(r_value)
    if n_number < 0 or r_number < 0 or r_number > n_number or n_number > 10000:
        raise _math()
    try:
        import sympy
        exact = sympy.binomial(n_number, r_number)
    except Exception:
        exact = math.comb(n_number, r_number)
    if exact > 1e308:
        raise _math()
    return float(exact)


def npr(n_value: float, r_value: float) -> float:
    n_number, r_number = _integer(n_value), _integer(r_value)
    if n_number < 0 or r_number < 0 or r_number > n_number or n_number > 10000:
        raise _math()
    try:
        import sympy
        exact = sympy.factorial(n_number) // sympy.factorial(n_number - r_number)
    except Exception:
        exact = math.perm(n_number, r_number)
    if exact > 1e308:
        raise _math()
    return float(exact)


def floor(value: float, _mode: str) -> float:
    return float(math.floor(value))


def ceil(value: float, _mode: str) -> float:
    return float(math.ceil(value))


def exp(value: float, _mode: str) -> float:
    return power(math.e, value)


def rand(_mode: str | None = None) -> float:
    return random.random()


def round_half(value: float, digits: float = 0) -> float:
    """Round half away from zero to ``digits`` places. Negative digits round left of the decimal."""
    places = _integer(digits)
    if places < -8 or places > 12:
        raise _math()
    quantum = Decimal(1).scaleb(-places)
    rounded = Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP)
    return snap(float(rounded))


def signum(value: float, _mode: str) -> float:
    if value == 0:
        return 0.0
    return 1.0 if value > 0 else -1.0


def is_prime(value: float, _mode: str) -> float:
    number = _integer(value)
    if number < 2:
        return 0.0
    import sympy
    return 1.0 if sympy.isprime(number) else 0.0


def _numbers(args: list[float], minimum: int) -> list[float]:
    if len(args) < minimum:
        raise _math()
    return [float(arg) for arg in args]


def _percentile(values: list[float], percent: float) -> float:
    _require(0 <= percent <= 100)
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (percent / 100) * (len(ordered) - 1)
    low = int(math.floor(rank))
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def data_mean(args: list[float]) -> float:
    values = _numbers(args, 1)
    return snap(sum(values) / len(values))


def data_median(args: list[float]) -> float:
    values = sorted(_numbers(args, 1))
    mid = len(values) // 2
    if len(values) % 2:
        return snap(values[mid])
    return snap((values[mid - 1] + values[mid]) / 2)


def data_mode(args: list[float]) -> float:
    values = _numbers(args, 1)
    counts: dict[float, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    best = max(counts.values())
    if best == 1 and len(values) > 1:
        raise _math("No mode")
    return snap(min(value for value, count in counts.items() if count == best))


def data_variance(args: list[float]) -> float:
    """Population variance."""
    values = _numbers(args, 1)
    center = sum(values) / len(values)
    return snap(sum((value - center) ** 2 for value in values) / len(values))


def data_stdev(args: list[float]) -> float:
    return snap(math.sqrt(data_variance(args)))


def data_min(args: list[float]) -> float:
    return snap(min(_numbers(args, 1)))


def data_max(args: list[float]) -> float:
    return snap(max(_numbers(args, 1)))


def data_range(args: list[float]) -> float:
    values = _numbers(args, 1)
    return snap(max(values) - min(values))


def data_total(args: list[float]) -> float:
    return snap(sum(_numbers(args, 1)))


def data_count(args: list[float]) -> float:
    return float(len(_numbers(args, 1)))


def data_pctile(args: list[float]) -> float:
    """``pctile(p, x1, x2, ...)`` — ``p`` is a percent from 0 to 100."""
    if len(args) < 2:
        raise _math()
    return snap(_percentile([float(value) for value in args[1:]], float(args[0])))


def data_q1(args: list[float]) -> float:
    return snap(_percentile(_numbers(args, 1), 25))


def data_q3(args: list[float]) -> float:
    return snap(_percentile(_numbers(args, 1), 75))


def data_iqr(args: list[float]) -> float:
    values = _numbers(args, 1)
    return snap(_percentile(values, 75) - _percentile(values, 25))


def data_gcd(args: list[float]) -> float:
    values = [_integer(value) for value in _numbers(args, 2)]
    result = 0
    for value in values:
        result = math.gcd(result, value)
    return float(abs(result))


def data_lcm(args: list[float]) -> float:
    values = [abs(_integer(value)) for value in _numbers(args, 2)]
    result = 1
    for value in values:
        result = math.lcm(result, value)
        if result > 10**12:
            raise _math()
    return float(result)


# name -> (arity, callable)
# Angle-aware callables accept (value, mode) or (value, base, mode).
Function = tuple[int, Callable[..., float]]

FUNCTIONS: dict[str, Function] = {
    "sin": (1, sin), "cos": (1, cos), "tan": (1, tan),
    "csc": (1, csc), "sec": (1, sec), "cot": (1, cot),
    "sin⁻¹": (1, asin), "cos⁻¹": (1, acos), "tan⁻¹": (1, atan),
    "csc⁻¹": (1, acsc), "sec⁻¹": (1, asec), "cot⁻¹": (1, acot),
    "asin": (1, asin), "acos": (1, acos), "atan": (1, atan),
    "acsc": (1, acsc), "asec": (1, asec), "acot": (1, acot),
    "sinh": (1, sinh), "cosh": (1, cosh), "tanh": (1, tanh),
    "csch": (1, csch), "sech": (1, sech), "coth": (1, coth),
    "sinh⁻¹": (1, asinh), "cosh⁻¹": (1, acosh), "tanh⁻¹": (1, atanh),
    "csch⁻¹": (1, acsch), "sech⁻¹": (1, asech), "coth⁻¹": (1, acoth),
    "asinh": (1, asinh), "acosh": (1, acosh), "atanh": (1, atanh),
    "acsch": (1, acsch), "asech": (1, asech), "acoth": (1, acoth),
    "log": (2, log), "ln": (1, ln), "log2": (1, log2), "log₂": (1, log2), "log10": (1, log10),
    "sqrt": (1, sqrt), "cbrt": (1, cbrt), "abs": (1, absolute),
    "exp": (1, exp), "floor": (1, floor), "ceil": (1, ceil),
    "round": (2, lambda value, digits, _mode: round_half(value, digits)),
    "sign": (1, signum), "isprime": (1, is_prime),
    "nCr": (2, lambda n, r, _mode: ncr(n, r)),
    "nPr": (2, lambda n, r, _mode: npr(n, r)),
    "mod": (2, lambda n, r, _mode: _modulo(n, r)),
    "rand": (0, lambda _mode: rand()),
    "mean": (-1, data_mean), "median": (-1, data_median), "mode": (-1, data_mode),
    "variance": (-1, data_variance), "stdev": (-1, data_stdev),
    "min": (-1, data_min), "max": (-1, data_max), "range": (-1, data_range),
    "total": (-1, data_total), "count": (-1, data_count),
    "pctile": (-1, data_pctile), "q1": (-1, data_q1), "q3": (-1, data_q3), "iqr": (-1, data_iqr),
    "gcd": (-1, data_gcd), "lcm": (-1, data_lcm),
}


def _modulo(left: float, right: float) -> float:
    if right == 0:
        raise _math("Cannot divide by zero")
    return snap(left % right)


INFIX = {"nCr", "nPr", "mod"}
VARARGS = {
    "mean", "median", "mode", "variance", "stdev",
    "min", "max", "range", "total", "count",
    "pctile", "q1", "q3", "iqr", "gcd", "lcm",
}

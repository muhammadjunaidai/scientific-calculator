# ! Numbers for the screen, and one readable line for each history entry.

from __future__ import annotations

import re
from decimal import Decimal

_SNAP = Decimal("1e-13")
_SCI_HI = Decimal("1e12")
_SCI_LO = Decimal("1e-6")


def snap(value: float) -> float:
    """Treat tiny leftovers such as ``sin(180°)`` as zero, then keep 12 significant digits."""
    if value != value:  # NaN
        return value
    number = Decimal(str(value))
    if abs(number) < _SNAP:
        return 0.0
    return float(f"{value:.12g}")


def format_raw(value: float) -> str:
    """Parser-safe text: no grouping commas, so it can be inserted back into an expression."""
    value = snap(value)
    if value == 0:
        return "0"
    magnitude = abs(Decimal(str(value)))
    if magnitude >= _SCI_HI or magnitude < _SCI_LO:
        return _scientific(value)
    text = f"{value:.12g}"
    if "e" in text or "E" in text:
        return _scientific(value)
    return text


def format_display(value: float) -> str:
    """On-screen number, with thousands separators on the integer part."""
    raw = format_raw(value)
    if "E" in raw:
        return raw
    return _group(raw)


_SUPER = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
_BINARY = re.compile(r"(?<=[\w\d)\]πφ⁰¹²³⁴⁵⁶⁷⁸⁹])\s*([+\-−=<>≤≥×÷])\s*")


# ! History line, for example x² + 5 = 30. The stored expression is not changed.
def format_history(expression: str, shown: str) -> str:
    return f"{_pretty_expression(expression.strip())} = {shown}"


def _pretty_expression(expression: str) -> str:
    text = re.sub(r"\^\(([-−]?\d+)\)", lambda match: _super_number(match.group(1)), expression)
    text = re.sub(r"\^(-?\d+)", lambda match: _super_number(match.group(1)), text)
    return " ".join(_BINARY.sub(r" \1 ", text).split())


def _super_number(digits: str) -> str:
    sign = "⁻" if digits[:1] in "-−" else ""
    body = digits[1:] if sign else digits
    return f"{sign}{body.translate(_SUPER)}"


def to_dms(value: float) -> str:
    """Decimal degrees to a ``30°15′45″`` string."""
    sign = "-" if value < 0 else ""
    rest = abs(value)
    degrees = int(rest)
    minutes_full = (rest - degrees) * 60
    minutes = int(minutes_full)
    seconds = round((minutes_full - minutes) * 60, 4)
    if seconds >= 60:
        seconds = 0
        minutes += 1
    if minutes >= 60:
        minutes = 0
        degrees += 1
    second_text = format_raw(float(seconds))
    return f"{sign}{degrees}°{minutes}′{second_text}″"


def dms_to_degrees(packed: float) -> float:
    """``30.1545`` (dd.mmss) to decimal degrees ``30.2625``."""
    sign = -1.0 if packed < 0 else 1.0
    packed = abs(packed)
    degrees = int(packed)
    hundredths = round((packed - degrees) * 100, 8)
    minutes = int(hundredths)
    seconds = round((hundredths - minutes) * 100, 6)
    if minutes >= 60 or seconds >= 60:
        raise ValueError("Invalid DMS")
    return snap(sign * (degrees + minutes / 60 + seconds / 3600))


def _scientific(value: float) -> str:
    mantissa, exponent = f"{value:.10e}".split("e")
    mantissa = mantissa.rstrip("0").rstrip(".")
    if mantissa in ("-0", "0", "-"):
        return "0"
    return f"{mantissa}E{int(exponent)}"


def _group(text: str) -> str:
    sign = ""
    if text.startswith("-"):
        sign, text = "-", text[1:]
    whole, dot, frac = text.partition(".")
    grouped = f"{int(whole):,}" if whole else "0"
    suffix = f".{frac}" if dot else ""
    return f"{sign}{grouped}{suffix}"

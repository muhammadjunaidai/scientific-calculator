# ! Forwards physical keys to the same actions the keypad uses.

from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components

from ui.model import KEYMAP

_listener = components.declare_component("precision_keyboard", path=str(Path(__file__).parent / "frontend"))


def read_keyboard_events(copy_text: str = "", copy_nonce: int = 0) -> list:
    value = _listener(
        keys=sorted(KEYMAP),
        copyText=copy_text,
        copyNonce=copy_nonce,
        key="precision_kb",
        default=[],
    )
    return value or []

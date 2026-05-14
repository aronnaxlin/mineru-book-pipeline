from __future__ import annotations
import re

from .base import ExportPlugin

try:
    import pangu as _pangu
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

# Protect LaTeX spans from pangu so spaces aren't inserted inside formulas
_LATEX_BLOCK  = re.compile(r'\$\$[\s\S]*?\$\$')
_LATEX_INLINE = re.compile(r'\$[^$\n]+?\$')


def _spacing(text: str) -> str:
    if not _AVAILABLE or not text:
        return text
    placeholders: list[str] = []

    def stash(m: re.Match) -> str:
        placeholders.append(m.group(0))
        return f"\x00L{len(placeholders)-1}\x00"

    protected = _LATEX_BLOCK.sub(stash, text)
    protected = _LATEX_INLINE.sub(stash, protected)
    spaced = _pangu.spacing_text(protected)
    for i, original in enumerate(placeholders):
        spaced = spaced.replace(f"\x00L{i}\x00", original)
    return spaced


class CJKSpacingPlugin(ExportPlugin):
    """
    Insert spaces between CJK characters and ASCII/Latin text using pangu.

    LaTeX inline ($...$) and block ($$...$$) spans are protected and
    passed through unchanged.
    """

    def __init__(self) -> None:
        if not _AVAILABLE:
            import warnings
            warnings.warn(
                "pangu not installed; CJKSpacingPlugin is disabled. "
                "Run: pip install pangu",
                stacklevel=2,
            )

    def on_text(self, item: dict, text: str) -> str:
        return _spacing(text)

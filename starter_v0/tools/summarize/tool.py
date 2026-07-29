from __future__ import annotations

import re
from typing import Any

from tools._shared import err


def summarize_text(
    text: str = "",
    style: str = "bullets",
    max_sentences: int = 5,
) -> dict[str, Any]:
    """
    Condenses a block of text into a shorter summary.

    Args:
        text:          The full text to summarize.
        style:         Output format — "bullets", "paragraph", or "tldr".
        max_sentences: Maximum sentences / bullet points to produce.
    """
    try:
        if not text or not text.strip():
            raise ValueError("'text' argument is required and must not be empty.")

        style = style if style in ("bullets", "paragraph", "tldr") else "bullets"
        max_sentences = max(1, int(max_sentences or 5))

        # Split into sentences (handles both Vietnamese and English punctuation)
        raw_sentences = re.split(r"(?<=[.!?。])\s+", text.strip())
        # Filter very short fragments
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 15]

        if not sentences:
            sentences = [text.strip()[:300]]

        selected = sentences[:max_sentences]

        if style == "tldr":
            summary = "TL;DR: " + selected[0]
        elif style == "paragraph":
            summary = " ".join(selected)
        else:  # bullets
            summary = "\n".join(f"• {s}" for s in selected)

        return {
            "tool": "summarize",
            "summary": summary,
            "word_count": len(summary.split()),
            "style": style,
        }
    except Exception as exc:
        return err("summarize", exc)

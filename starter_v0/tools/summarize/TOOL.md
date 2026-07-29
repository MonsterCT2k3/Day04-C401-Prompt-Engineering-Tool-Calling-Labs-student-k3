---
name: summarize
track: core
kind: local
provider: none
requires_env: []
inputs: [text, style, max_sentences]
outputs: [summary, word_count, style]
side_effect: false
---
# summarize

Condenses a long block of text into a shorter summary.

## When to use
- Use when the user asks to "tóm tắt", "rút gọn", "cho ngắn lại", or "summarize" a piece of text they have already provided inline.
- Use AFTER `fetch` or `lookup` returns raw content and the user explicitly wants a summary of that content.

## When NOT to use
- Do NOT use if the user hasn't provided any text yet — use `fetch` or `lookup` first to get content.
- Do NOT use instead of `fetch` when a URL is available (fetch + summarize is the right pipeline).
- Do NOT use for searching; use `lookup` or `social_search` for that.

## Arguments
| Argument       | Type    | Default    | Description |
|----------------|---------|------------|-------------|
| `text`         | string  | required   | The full text to summarize. |
| `style`        | string  | `"bullets"` | Output format: `"bullets"` (bullet list), `"paragraph"` (flowing text), `"tldr"` (one-line). |
| `max_sentences`| integer | `5`        | Maximum number of sentences or bullet points in the output. |

## Side effects
None. This tool is pure computation — no API calls, no external state.

## Quicktest
```python
from tools import TOOL_FUNCTIONS as T
r = T['summarize']('Artificial intelligence is transforming industries worldwide. Companies are investing billions. Researchers warn of risks.', style='bullets', max_sentences=2)
assert r.get('error') is None
print(r)
```

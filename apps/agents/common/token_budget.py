from __future__ import annotations

import importlib
from dataclasses import dataclass


class Tokenizer:
    """Token counting/truncation abstraction used by budget enforcement."""

    def count_tokens(self, text: str) -> int:
        raise NotImplementedError

    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class _Span:
    start: int
    end: int


def _is_cjk(char: str) -> bool:
    code = ord(char)
    return 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF or 0x3040 <= code <= 0x30FF or 0xAC00 <= code <= 0xD7AF


class UnicodeHeuristicTokenizer(Tokenizer):
    """Deterministic Unicode-aware fallback tokenizer.

    This approximates modern LLM tokenization while ensuring predictable behavior
    in tests and preserving CJK boundaries better than character slicing.
    """

    def _spans(self, text: str) -> list[_Span]:
        spans: list[_Span] = []
        i = 0
        size = len(text)
        while i < size:
            char = text[i]
            if char.isspace():
                i += 1
                continue
            if _is_cjk(char):
                spans.append(_Span(i, i + 1))
                i += 1
                continue
            if char.isalnum() or char in {"_", "'", "-"}:
                start = i
                i += 1
                while i < size:
                    inner = text[i]
                    if inner.isalnum() or inner in {"_", "'", "-"}:
                        i += 1
                    else:
                        break
                spans.append(_Span(start, i))
                continue
            spans.append(_Span(i, i + 1))
            i += 1
        return spans

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(self._spans(text))

    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        if max_tokens <= 0:
            return ""
        spans = self._spans(text)
        if len(spans) <= max_tokens:
            return text
        end = spans[max_tokens - 1].end
        return text[:end].rstrip()


class TiktokenTokenizer(Tokenizer):
    """Tokenizer backed by tiktoken when available."""

    def __init__(self, model_hint: str | None = None) -> None:
        tiktoken = importlib.import_module("tiktoken")
        try:
            self._encoding = tiktoken.encoding_for_model(model_hint or "gpt-4o")
        except Exception:
            self._encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(self._encoding.encode(text))

    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        if max_tokens <= 0:
            return ""
        encoded = self._encoding.encode(text)
        if len(encoded) <= max_tokens:
            return text
        return self._encoding.decode(encoded[:max_tokens]).rstrip()


def create_tokenizer(model_hint: str | None = None) -> Tokenizer:
    """Create the best available tokenizer for the selected model."""
    try:
        return TiktokenTokenizer(model_hint=model_hint)
    except Exception:
        return UnicodeHeuristicTokenizer()

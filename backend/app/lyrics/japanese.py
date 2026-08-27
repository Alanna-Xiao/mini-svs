import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, Optional

from pykakasi import kakasi


_JAPANESE_TEXT = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff]")
_CONVERTER = kakasi()
_SMALL_KANA = frozenset("ぁぃぅぇぉゃゅょゎゕゖ")


@dataclass(frozen=True)
class LyricMora:
    """A timed lyric unit, which may be a silent sokuon closure."""

    phoneme: Optional[str]
    kind: Literal["phoneme", "closure"] = "phoneme"


@lru_cache(maxsize=512)
def lyric_to_phoneme(lyric: str) -> str:
    """Return the combined romanization retained for compatibility."""
    return "".join(lyric_to_phonemes(lyric))


@lru_cache(maxsize=512)
def lyric_to_phonemes(lyric: str) -> tuple[str, ...]:
    """Split a Japanese lyric into romanized mora-sized voicebank keys."""
    return tuple(
        mora.phoneme for mora in lyric_to_morae(lyric) if mora.phoneme is not None
    )


@lru_cache(maxsize=512)
def lyric_to_morae(lyric: str) -> tuple[LyricMora, ...]:
    """Split a lyric into timed phonemes and silent Japanese closures."""
    normalized = unicodedata.normalize("NFKC", lyric).strip().lower()
    if not _JAPANESE_TEXT.search(normalized):
        return tuple(LyricMora(phoneme=part) for part in normalized.split() if part)

    converted = _CONVERTER.convert(normalized)
    hiragana = "".join(part["hira"] for part in converted)
    morae: list[str] = []
    for character in hiragana:
        if character.isspace():
            continue
        if character in _SMALL_KANA and morae and morae[-1] != "ー":
            morae[-1] += character
        else:
            morae.append(character)

    resolved: list[LyricMora] = []
    for mora in morae:
        if mora == "っ":
            resolved.append(LyricMora(phoneme=None, kind="closure"))
            continue
        if mora == "ー":
            previous_phoneme = next(
                (unit.phoneme for unit in reversed(resolved) if unit.phoneme),
                None,
            )
            if previous_phoneme:
                vowel = next(
                    (
                        character
                        for character in reversed(previous_phoneme)
                        if character in "aiueo"
                    ),
                    "",
                )
                if vowel:
                    resolved.append(LyricMora(phoneme=vowel))
            continue
        romanized = "".join(part["hepburn"] for part in _CONVERTER.convert(mora)).lower()
        if romanized:
            resolved.append(LyricMora(phoneme=romanized))
    return tuple(resolved)

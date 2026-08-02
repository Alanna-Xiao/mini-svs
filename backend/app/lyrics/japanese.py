import re
import unicodedata
from functools import lru_cache

from pykakasi import kakasi


_JAPANESE_TEXT = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff]")
_CONVERTER = kakasi()
_SMALL_KANA = frozenset("ぁぃぅぇぉゃゅょゎ")


@lru_cache(maxsize=512)
def lyric_to_phoneme(lyric: str) -> str:
    """Return the combined romanization retained for compatibility."""
    return "".join(lyric_to_phonemes(lyric))


@lru_cache(maxsize=512)
def lyric_to_phonemes(lyric: str) -> tuple[str, ...]:
    """Split a Japanese lyric into romanized mora-sized voicebank keys."""
    normalized = unicodedata.normalize("NFKC", lyric).strip().lower()
    if not _JAPANESE_TEXT.search(normalized):
        return tuple(part for part in normalized.split() if part)

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

    phonemes: list[str] = []
    for mora in morae:
        if mora == "ー":
            if phonemes:
                vowel = next(
                    (character for character in reversed(phonemes[-1]) if character in "aiueo"),
                    "",
                )
                if vowel:
                    phonemes.append(vowel)
            continue
        romanized = "".join(part["hepburn"] for part in _CONVERTER.convert(mora)).lower()
        if romanized:
            phonemes.append(romanized)
    return tuple(phonemes)

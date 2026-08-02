import re
import unicodedata
from functools import lru_cache

from pykakasi import kakasi


_JAPANESE_TEXT = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff]")
_CONVERTER = kakasi()


@lru_cache(maxsize=512)
def lyric_to_phoneme(lyric: str) -> str:
    """Return the romanized voicebank key for one note's lyric."""
    normalized = unicodedata.normalize("NFKC", lyric).strip().lower()
    if not _JAPANESE_TEXT.search(normalized):
        return normalized

    converted = _CONVERTER.convert(normalized)
    return "".join(part["hepburn"] for part in converted).lower()

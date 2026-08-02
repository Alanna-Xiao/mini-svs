from app.lyrics import lyric_to_phonemes


def test_splits_multiple_kana_into_mora_phonemes():
    assert lyric_to_phonemes("かな") == ("ka", "na")


def test_keeps_small_kana_with_the_preceding_mora():
    assert lyric_to_phonemes("きょう") == ("kyo", "u")


def test_resolves_kanji_readings_into_multiple_phonemes():
    assert lyric_to_phonemes("歌") == ("u", "ta")


def test_expands_katakana_long_vowel_marks():
    assert lyric_to_phonemes("スーパー") == ("su", "u", "pa", "a")

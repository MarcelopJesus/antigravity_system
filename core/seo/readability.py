"""Readability scoring for Brazilian Portuguese (PT-BR).

Implements Flesch-Kincaid adapted for Portuguese with syllable counting
optimized for PT-BR phonological rules.
"""
import re


# Common PT-BR diphthongs (count as 1 syllable, not 2)
_DIPHTHONGS = re.compile(
    r'(?:ai|au|ei|eu|oi|ou|ui|iu|ae|ao|oe|ão|ãe|õe)', re.IGNORECASE
)


def count_syllables_pt(word: str) -> int:
    """Count syllables in a Portuguese word.

    Rules:
    - Each vowel group is a potential syllable nucleus
    - Diphthongs (ai, ei, ou, etc.) count as 1 syllable
    - Minimum 1 syllable per word
    """
    word = word.lower().strip()
    if not word:
        return 0

    # Replace diphthongs with single marker to avoid double counting
    reduced = _DIPHTHONGS.sub('V', word)

    # Count remaining vowels (including the V markers)
    vowels = re.findall(r'[aeiouáéíóúâêîôûãõàV]', reduced)
    count = len(vowels)

    return max(count, 1)


def _split_sentences(text: str) -> list:
    """Split text into sentences."""
    # Split on sentence-ending punctuation followed by space or end
    sentences = re.split(r'[.!?]+(?:\s|$)', text)
    return [s.strip() for s in sentences if s.strip()]


def _get_words(text: str) -> list:
    """Extract words from plain text."""
    return [w for w in re.findall(r'[a-záéíóúâêîôûãõàç]+', text.lower()) if len(w) > 1]


def readability_score_pt(text: str) -> dict:
    """Calculate Flesch-Kincaid readability adapted for Brazilian Portuguese.

    Formula (adapted for PT-BR):
        index = 248.835 - (1.015 × ASL) - (84.6 × ASW)
        ASL = Average Sentence Length (words per sentence)
        ASW = Average Syllables per Word

    Scale (0-100, higher = easier):
        75-100: Muito fácil (5ª série)
        50-75:  Fácil (6ª-8ª série) ← TARGET for blog articles
        25-50:  Médio (ensino médio)
        0-25:   Difícil (ensino superior)

    Returns:
        dict with keys: index, level, asl, asw, sentence_count, word_count
    """
    sentences = _split_sentences(text)
    words = _get_words(text)

    if not sentences or not words:
        return {
            "index": 0.0,
            "level": "indefinido",
            "asl": 0.0,
            "asw": 0.0,
            "sentence_count": 0,
            "word_count": 0,
        }

    asl = len(words) / len(sentences)
    total_syllables = sum(count_syllables_pt(w) for w in words)
    asw = total_syllables / len(words)

    # Flesch-Kincaid adapted for PT-BR
    index = 248.835 - (1.015 * asl) - (84.6 * asw)
    # Clamp to 0-100
    index = max(0.0, min(100.0, index))

    if index >= 75:
        level = "muito_facil"
    elif index >= 50:
        level = "facil"
    elif index >= 25:
        level = "medio"
    else:
        level = "dificil"

    return {
        "index": round(index, 1),
        "level": level,
        "asl": round(asl, 1),
        "asw": round(asw, 2),
        "sentence_count": len(sentences),
        "word_count": len(words),
    }

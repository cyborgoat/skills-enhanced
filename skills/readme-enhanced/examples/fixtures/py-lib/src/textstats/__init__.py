"""Count words, sentences and estimated reading time."""
import re


def words(text: str) -> int:
    return len(re.findall(r"\w+", text))


def sentences(text: str) -> int:
    return len([s for s in re.split(r"[.!?]+", text) if s.strip()])


def reading_time(text: str, wpm: int = 200) -> float:
    """Minutes needed to read `text` at `wpm` words per minute."""
    return round(words(text) / wpm, 2)

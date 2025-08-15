import re

POSITIVE_WORDS = {
    "good", "great", "excellent", "amazing", "awesome", "helpful", "positive",
    "love", "loved", "like", "liked", "happy", "satisfied", "thanks", "thankyou",
    "well-done", "well done", "fantastic", "wonderful", "appreciate", "appreciated",
}
NEGATIVE_WORDS = {
    "bad", "poor", "terrible", "awful", "horrible", "hate", "hated", "dislike", "disliked",
    "unhappy", "unsatisfied", "frustrated", "issue", "bug", "broken", "delay", "delayed",
    "late", "missing", "fail", "failed", "failure", "problem", "problems", "slow",
}

EMOJI_POS = {"🙂", "😊", "👍", "💯", "👏", "🎉"}
EMOJI_NEG = {"🙁", "😠", "😡", "👎", "🥴", "💢"}

def _tokenize(text: str):
    # lowercase + simple word extraction
    text = text.lower()
    words = re.findall(r"[a-z']+", text)
    return words

def analyze_sentiment(text: str) -> str:
    """
    Super-lightweight sentiment: positive/negative keywords & emojis.
    Returns: 'positive' | 'neutral' | 'negative'
    """
    if not text:
        return "neutral"

    words = set(_tokenize(text))
    score = 0

    # keyword scoring
    score += sum(1 for w in words if w in POSITIVE_WORDS)
    score -= sum(1 for w in words if w in NEGATIVE_WORDS)

    # emoji scoring
    score += sum(1 for ch in text if ch in EMOJI_POS)
    score -= sum(1 for ch in text if ch in EMOJI_NEG)

    # thresholds (tweakable)
    if score >= 1:
        return "positive"
    if score <= -1:
        return "negative"
    return "neutral"

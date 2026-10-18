"""Deterministic fact-check guard for the Sunday race update.

The Sunday message is written by an LLM for personality/flair, but the LLM has
historically inflated season win counts (saying "3rd win" when it was the 2nd)
and invented promotion/clinch drama that wasn't real. This module checks the
generated message against the AUTHORITATIVE deterministic scenario text that the
code already builds, and reports factual violations so the caller can re-roll or
fall back to a clean template.

Design goals:
- Catch the two real bug classes: (1) win-count INFLATION, (2) INVENTED
  season/promotion/relegation stakes.
- Very low false-positive rate, so 99% of messages pass through untouched and
  keep their original voice/emojis.
- Pure functions — unit-testable without the clock, DB, or OpenAI.
"""
import re

# "2nd win", "3 rd win", etc.
_ORDINAL_WIN_RE = re.compile(r'(\d+)\s*(?:st|nd|rd|th)\s+win', re.IGNORECASE)
# "second win", "third win"
_WORD_ORD = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
             'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10}
_WORD_ORD_RE = re.compile(r'\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+win',
                          re.IGNORECASE)
# division phrasing "now has 2"
_NOW_HAS_RE = re.compile(r'now has (\d+)', re.IGNORECASE)

# Players the scenario explicitly declared out: "... — A, B and C are out of
# contention" or "... — A is out of contention".
_OUT_OF_CONTENTION_RE = re.compile(
    r'out of contention', re.IGNORECASE)
_OUT_NAMES_RE = re.compile(
    r'No one else can catch up\s*[—\-:]\s*(.+?)\s+(?:is|are)\s+out of contention',
    re.IGNORECASE)
# "X needs more games", "X, Y and Z need more games", "needs another game"
_NAME = r"[A-Z][\w'’-]*"
# Separator must tolerate the Oxford comma: "Joanna, Evan, and Malia" carries
# BOTH a comma and an "and" between the last two names.
_SEP = r"(?:\s*,\s*and\s+|\s*,\s*|\s+and\s+)"
_NEEDS_GAMES_RE = re.compile(
    r"(" + _NAME + r"(?:" + _SEP + _NAME + r")*)"
    r"\s+(?:needs?|need)\s+(?:more|another|\d+\s+more)\s+games?",
    re.IGNORECASE)

# Season/promotion/relegation language the AI must not use unless the scenario raised it.
_STAKES_PRESENT_RE = re.compile(r'SEASON STAKES|SEASON CLINCH|Promotion|Relegation', re.IGNORECASE)
_CLAIMED_STAKES_RE = re.compile(
    r'clinch|win[s]? the season|take[s]? the season|season (?:champ|title|victory)|promot|relegat',
    re.IGNORECASE)


def _ordinals_in(text):
    nums = {int(m) for m in _ORDINAL_WIN_RE.findall(text)}
    nums |= {_WORD_ORD[m.lower()] for m in _WORD_ORD_RE.findall(text)}
    nums |= {int(m) for m in _NOW_HAS_RE.findall(text)}
    return nums


def allowed_win_counts(scenario_text):
    """The set of win-count numbers the deterministic scenario actually states."""
    return _ordinals_in(scenario_text or "")


def stakes_allowed(scenario_text):
    """True if the scenario legitimately raised season/promotion/relegation stakes."""
    return bool(_STAKES_PRESENT_RE.search(scenario_text or ""))


def eliminated_names(scenario_text):
    """Players the scenario text explicitly declared out of contention."""
    out = set()
    for blob in _OUT_NAMES_RE.findall(scenario_text or ""):
        for name in re.split(_SEP, blob):
            name = name.strip()
            if name:
                out.add(name)
    return out


def _names_needing_games(message):
    """Players the MESSAGE says merely need more games to qualify."""
    out = set()
    for blob in _NEEDS_GAMES_RE.findall(message or ""):
        for name in re.split(_SEP, blob):
            name = name.strip()
            if name:
                out.add(name)
    return out


def find_violations(message, scenario_text):
    """Return a list of human-readable factual violations (empty = message is clean).

    Conservative: only flags win-count INFLATION (a claimed count higher than the
    data supports) and stakes language when the scenario raised none.
    """
    issues = []
    allowed = allowed_win_counts(scenario_text)
    claimed = _ordinals_in(message)
    if allowed:
        ceiling = max(allowed)
        for n in claimed:
            if n > ceiling:
                issues.append(f"claims a win count of {n} but the data supports at most {ceiling} ({sorted(allowed)})")
    elif claimed:
        # No authoritative count was stated anywhere, so every "Nth win" in the
        # message is invented. This branch used to `return` early on empty
        # scenario text — failing open — which is how league 11 shipped "This is
        # their 3rd win this season" on a week that was the player's 1st: the
        # single-eligible-player path built no scenario text, so there was
        # nothing to check against and the claim sailed through.
        issues.append(
            f"claims win count {sorted(claimed)} but the scenario states no win count at all")

    if not stakes_allowed(scenario_text) and _CLAIMED_STAKES_RE.search(message):
        issues.append("mentions clinch/promotion/relegation but the scenario raised no season stakes")

    # A player the scenario marked ELIMINATED must not be described as merely
    # needing more games. Those read as opposites to a reader: one is "they are
    # done", the other is "they could still turn up and matter".
    #
    # League 1, week 1947: "Joanna, Evan and Malia need more games." Joanna had
    # 4 of 5 and a best-4 of 18 against a leader on 16 — qualifying would have
    # changed nothing, and the scenario had already marked her out. Evan and
    # Malia, with no games at all, genuinely did just need games. Grouping all
    # three flattened a real distinction.
    #
    # Only fires on a direct contradiction of a name the scenario itself named,
    # so it stays silent on every message that does not make the claim.
    out = eliminated_names(scenario_text)
    if out:
        for name in sorted(out & _names_needing_games(message)):
            issues.append(
                f"says {name} needs more games, but the scenario has them out of contention")

    return issues


def build_fallback_message(scenario_text):
    """Deterministic, factually-correct message built from the scenario text.

    Used only when the LLM repeatedly fails the fact check. Less flair than an AI
    message, but the scenario text is already readable and complete, so it still
    reads as a real update — just plainer.
    """
    text = (scenario_text or "").strip()
    if not text:
        return text
    prefix = "🏆 " if "RACE OVER" in text else "📊 "
    return prefix + text


def strip_unsupported_sentences(message, scenario_text):
    """Drop only the sentences carrying unsupported claims, keep everything else.

    Last resort for the case where there is no scenario text to rebuild a
    message from: sending the AI's update minus the one invented sentence beats
    sending an empty one. Returns "" if nothing survives.
    """
    if not message:
        return ""
    allowed = allowed_win_counts(scenario_text)
    ceiling = max(allowed) if allowed else None
    stakes_ok = stakes_allowed(scenario_text)

    kept = []
    for sentence in re.split(r'(?<=[.!?])\s+', message.strip()):
        sentence = sentence.strip()
        if not sentence:
            continue
        nums = _ordinals_in(sentence)
        if nums and (ceiling is None or max(nums) > ceiling):
            continue
        if not stakes_ok and _CLAIMED_STAKES_RE.search(sentence):
            continue
        kept.append(sentence)
    return " ".join(kept).strip()

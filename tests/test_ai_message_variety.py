"""Variety and length safety for the per-score AI messages.

The roast and perfect-score prompts used to be byte-identical on every call —
only the player's name changed — so gpt-4o-mini returned its handful of
favourite Wordle jokes over and over. Temperature was already 0.9/0.95, which
varies the wording but not the idea.

The fix rotates a comedic FRAME, records it, and shows the model what it has
already sent. That produced much better variety and immediately broke the
160-character SMS budget, because a frame like "a solemn eulogy" talks long
and asking nicely for brevity does not stop it. Hence tidy_short_message,
which enforces length deterministically instead of hoping.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from twilio_webhook_app import (  # noqa: E402
    ROAST_ANGLES,
    CONGRATS_ANGLES,
    build_variety_instruction,
    pick_ai_angle,
    tidy_short_message,
)


# --- length enforcement -----------------------------------------------------

def test_short_message_is_untouched():
    msg = "Short and sweet, Gene!"
    assert tidy_short_message(msg) == msg


def test_empty_input_is_safe():
    assert tidy_short_message("") == ""
    assert tidy_short_message(None) == ""


def test_long_message_is_capped():
    msg = ("In the dim light, we gather to mourn. Gene's streak, a majestic beast, has "
           "perished at the hands of a mere five-letter word. You fought valiantly, yet "
           "your brain's dictionary seems to have been devoured by a hungry cat.")
    out = tidy_short_message(msg)
    assert len(out) <= 160
    assert out  # not emptied


def test_trims_at_a_sentence_boundary_when_it_can():
    msg = "First sentence here. " + ("padding words " * 20)
    out = tidy_short_message(msg)
    assert len(out) <= 160
    assert out.endswith((".", "!", "?", "…"))


def test_exactly_one_over_the_limit_is_still_capped():
    # The exact regression: the first implementation searched to limit + 1, so a
    # sentence terminator sitting at index 160 made out[:cut + 1] 161 characters
    # — one over — and returned it. Constructed rather than transcribed so the
    # length is unambiguous.
    msg = ("Gene flamed out again. " * 8)[:160] + "!"
    assert len(msg) == 161
    assert msg[-1] == "!"
    assert len(tidy_short_message(msg)) <= 160


def test_no_length_slips_through_across_the_boundary():
    for n in range(150, 201):
        assert len(tidy_short_message("a" * (n - 1) + "!")) <= 160, n
        assert len(tidy_short_message(("word " * 60)[: n - 1] + "!")) <= 160, n


# --- markdown must be UNWRAPPED, never deleted ------------------------------

def test_bold_is_unwrapped_not_removed():
    # A buggy replacement once deleted the emphasised text entirely, dropping
    # the whole headline out of the message.
    out = tidy_short_message("**BREAKING: Gene failed!** Keep guessing, buddy!")
    assert "BREAKING: Gene failed!" in out
    assert "*" not in out


def test_italic_and_headings_are_stripped_of_syntax_only():
    out = tidy_short_message("## Heading\n**Bold** and *italic* together")
    assert out == "Heading Bold and italic together"


def test_newlines_collapse_to_single_spaces():
    assert tidy_short_message("one\n\ntwo\nthree") == "one two three"


# --- angle rotation ---------------------------------------------------------

def test_angle_avoids_recently_used_ones():
    recent = [("msg", a) for a in ROAST_ANGLES[:5]]
    for _ in range(25):
        assert pick_ai_angle(ROAST_ANGLES, recent) not in ROAST_ANGLES[:5]


def test_angle_falls_back_when_everything_was_used():
    # Must never return None or raise — a blocked message is worse than a
    # repeated frame.
    recent = [("msg", a) for a in CONGRATS_ANGLES]
    assert pick_ai_angle(CONGRATS_ANGLES, recent) in CONGRATS_ANGLES


def test_angle_pools_are_distinct_and_non_trivial():
    assert len(set(ROAST_ANGLES)) == len(ROAST_ANGLES) >= 8
    assert len(set(CONGRATS_ANGLES)) == len(CONGRATS_ANGLES) >= 8


# --- the prompt fragment ----------------------------------------------------

def test_instruction_carries_the_angle():
    angle = ROAST_ANGLES[0]
    assert angle in build_variety_instruction([], angle)


def test_instruction_lists_previous_messages_to_avoid():
    recent = [("The word won today!", ROAST_ANGLES[0]),
              ("Better luck tomorrow!", ROAST_ANGLES[1])]
    out = build_variety_instruction(recent, ROAST_ANGLES[2])
    assert "ALREADY sent" in out
    assert "The word won today!" in out
    assert "Better luck tomorrow!" in out


def test_instruction_is_clean_with_no_history():
    out = build_variety_instruction([], CONGRATS_ANGLES[0])
    assert "ALREADY sent" not in out
    assert CONGRATS_ANGLES[0] in out

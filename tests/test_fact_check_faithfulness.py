"""Unit tests for the Sunday fact-check faithfulness comparison.

Pure tests — no clock, DB, or OpenAI. They feed a sent message plus the stored
scenario text and assert how the check grades the difference.

The distinction under test: scenario_text is only the RACE ANALYSIS block, but the
AI is also handed a standings block naming every player. So a roster player absent
from the scenario is off-brief commentary (a note), while a name that is not on the
roster at all is a fabricated person (a real issue).
"""
from sunday_fact_check import check_faithfulness

ROSTER = ['Tiny Legs', 'Rally', 'Brent']
SCENARIO = "RACE OVER! Tiny Legs wins the week with 13! This is their 2nd win this season."
WIN_CLAIM = [{'type': 'win_count', 'player': 'Tiny Legs', 'number': 2,
              'quote': 'their 2nd win this season'}]


# --- the false positive that triggered this work (must NOT be an issue) ---

def test_roster_player_outside_scenario_is_a_note_not_an_issue():
    # League 19: the AI mentioned Rally, who is real and was in the standings block
    # it was given, but is absent from the RACE ANALYSIS line that gets stored.
    sent = ("RACE OVER! Tiny Legs takes the win with a stellar score of 13! "
            "This marks their 2nd win this season. Rally finishes strong but can't catch up.")
    issues, notes = check_faithfulness(sent, SCENARIO, ROSTER, WIN_CLAIM)
    assert issues == []
    assert any('Rally' in n for n in notes)


# --- the genuinely serious cases (must be CAUGHT) ---

def test_name_off_the_roster_is_an_issue():
    sent = "RACE OVER! Tiny Legs wins with 13! Meanwhile Gandalf collapses."
    claims = WIN_CLAIM + [{'type': 'weekly_win', 'player': 'Gandalf', 'quote': 'Gandalf collapses'}]
    issues, _ = check_faithfulness(sent, SCENARIO, ROSTER, claims)
    assert any('Gandalf' in i for i in issues)


def test_invented_number_still_caught():
    sent = "RACE OVER! Tiny Legs wins with 13! This marks their 5th win this season."
    issues, _ = check_faithfulness(sent, SCENARIO, ROSTER, WIN_CLAIM)
    assert any('5' in i for i in issues)


# --- clean messages must stay silent ---

def test_faithful_message_produces_nothing():
    sent = "RACE OVER! Tiny Legs wins the week with 13 - their 2nd win this season!"
    issues, notes = check_faithfulness(sent, SCENARIO, ROSTER, WIN_CLAIM)
    assert issues == []
    assert notes == []


def test_roster_match_is_case_insensitive():
    # A lowercased name must not be reported as someone who does not play here.
    issues, _ = check_faithfulness("tiny legs wins!", SCENARIO, ROSTER,
                                   [{'type': 'weekly_win', 'player': 'tiny legs'}])
    assert issues == []


def test_complement_number_allowance_survives():
    # "needs a 3 to tie" legitimately becomes "4 or higher" - not an invented figure.
    scenario = "Rally needs a 3 to tie Tiny Legs."
    issues, _ = check_faithfulness("RACE OVER if Rally posts a 4 or higher!", scenario, ROSTER, [])
    assert issues == []

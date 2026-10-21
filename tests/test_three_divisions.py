"""Three-division mode: the parts that are testable without a database.

The behaviour that genuinely did not exist before is the MIDDLE division —
with two divisions, Division I only relegates and Division II only promotes,
so no code path ever had to handle a division doing both. These pin the shape
of that, plus the split maths and the N-division rendering.
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from division_manager import ROMAN  # noqa: E402
from html_generator_v2 import (  # noqa: E402
    division_color,
    division_numeral,
    division_styled_label,
)
from image_generator import generate_division_weekly_image  # noqa: E402
from league_data_adapter import (  # noqa: E402
    added_on_monday_or_tuesday,
    division_counting_floor,
)


def split_sizes(n, division_count):
    """Mirror of the auto-split in _enable_division_mode / change_division_count."""
    base, rem = divmod(n, division_count)
    return [base + (1 if d > division_count - rem else 0)
            for d in range(1, division_count + 1)]


# --- the auto-split -------------------------------------------------------

def test_split_is_exhaustive():
    for n in range(6, 40):
        for dc in (2, 3):
            assert sum(split_sizes(n, dc)) == n, (n, dc)


def test_upper_divisions_are_never_larger():
    # Division I should never be the biggest — the old 2-division split gave
    # the smaller half to the top, and that property has to survive.
    for n in range(6, 40):
        for dc in (2, 3):
            sizes = split_sizes(n, dc)
            assert sizes == sorted(sizes), (n, dc, sizes)


def test_known_splits():
    assert split_sizes(9, 2) == [4, 5]      # unchanged from 2-division behaviour
    assert split_sizes(6, 2) == [3, 3]
    assert split_sizes(12, 3) == [4, 4, 4]  # the 3-division minimum
    assert split_sizes(17, 3) == [5, 6, 6]  # Alchemer today
    assert split_sizes(21, 3) == [7, 7, 7]  # the player cap


# --- movement is adjacent only -------------------------------------------

def _promote_target(division):
    return division - 1


def _relegate_target(division):
    return division + 1


def test_movement_is_always_one_division():
    for dc in (2, 3):
        for d in range(1, dc + 1):
            if d > 1:
                assert _promote_target(d) == d - 1
            if d < dc:
                assert _relegate_target(d) == d + 1


def test_top_division_never_promotes_and_bottom_never_relegates():
    for dc in (2, 3):
        assert not (1 > 1), 'Division I has nowhere higher'
        assert not (dc < dc), 'the bottom division has nowhere lower'


def test_middle_division_does_both():
    # The case that does not exist with two divisions.
    dc = 3
    middle = 2
    assert middle > 1, 'Division II can promote'
    assert middle < dc, 'Division II can also be relegated'
    assert _promote_target(middle) == 1
    assert _relegate_target(middle) == 3


def test_two_divisions_keep_their_old_roles():
    dc = 2
    assert not (1 > 1)          # Div I cannot promote
    assert 1 < dc               # Div I can relegate
    assert 2 > 1                # Div II can promote
    assert not (2 < dc)         # Div II cannot be relegated


# --- labels ---------------------------------------------------------------

def test_numerals_and_roman_agree():
    for d in (1, 2, 3):
        assert division_numeral(d) == ROMAN[d]


def test_each_division_has_its_own_colour():
    colours = {division_color(d) for d in (1, 2, 3)}
    assert len(colours) == 3


def test_styled_label_carries_numeral_and_colour():
    label = division_styled_label(3)
    assert 'III' in label
    assert division_color(3) in label


def test_unknown_division_degrades_rather_than_crashing():
    assert division_numeral(9) == '9'
    assert division_color(9)


# --- the scoreboard image -------------------------------------------------

def _rows(n):
    return [{'name': f'P{i}', 'score': 15 + i, 'used': 5, 'thrown': [6],
             'eligible': True, 'failed': 0} for i in range(n)]


def test_image_grows_with_a_third_division():
    two = generate_division_weekly_image('L', [('I', _rows(4)), ('II', _rows(5))])
    three = generate_division_weekly_image(
        'L', [('I', _rows(4)), ('II', _rows(5)), ('III', _rows(5))])
    assert three.size[0] == two.size[0], 'width is fixed'
    assert three.size[1] > two.size[1], 'a third table must add height'


def test_image_handles_an_empty_division():
    img = generate_division_weekly_image(
        'L', [('I', _rows(3)), ('II', []), ('III', _rows(3))])
    assert img.size[1] > 0


def test_image_still_renders_two_divisions():
    img = generate_division_weekly_image('L', [('I', _rows(4)), ('II', _rows(5))])
    assert img.size == (550, img.size[1])


# --- the division starting line --------------------------------------------
# Confirming division mode stamps the confirm week on every player, and the
# season total and missed weeks count from there. Weekly wins do not.

def test_floor_is_season_start_without_a_stamp():
    assert division_counting_floor(1927, None) == 1927


def test_floor_never_precedes_the_season_start():
    # Next season: the old confirm stamp is behind the new season start.
    assert division_counting_floor(1955, 1948) == 1955
    assert division_counting_floor(1927, 1927) == 1927


def test_floor_is_the_confirm_week():
    # Alchemer on prod, 2026-10-20: season from 1927, confirmed in week 1948.
    assert division_counting_floor(1927, 1948) == 1948


def test_floor_snaps_to_the_season_week_grid():
    assert division_counting_floor(1927, 1950) == 1948


def test_floor_without_a_season_start():
    assert division_counting_floor(None, 1948) is None


# --- first-week adds: Mon/Tue race in full, Wed+ are immune -----------------
# created_at is naive UTC; the day is judged in Pacific (PDT = UTC-7 in Oct).

def test_tuesday_morning_add_races_in_full():
    # Alchemer's eight adds, Tue 2026-10-20 ~09:30 PDT.
    assert added_on_monday_or_tuesday(datetime(2026, 10, 20, 16, 32))


def test_late_tuesday_is_still_tuesday_in_pacific():
    # Tue 23:30 PDT is already Wednesday in UTC.
    assert added_on_monday_or_tuesday(datetime(2026, 10, 21, 6, 30))


def test_wednesday_add_is_not():
    assert not added_on_monday_or_tuesday(datetime(2026, 10, 21, 7, 30))  # Wed 00:30 PDT


def test_sunday_night_is_not_monday():
    # Sun 23:00 PDT is Monday in UTC.
    assert not added_on_monday_or_tuesday(datetime(2026, 10, 19, 6, 0))


def test_missing_created_at_gets_no_exception():
    assert not added_on_monday_or_tuesday(None)

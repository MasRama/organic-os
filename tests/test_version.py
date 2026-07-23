"""The semantic-version comparison behind the diagnose update-currency check.

No fixture here is a real credential or a phone-shaped digit run; these are
version strings. The comparator is pure and does no I/O, so every case runs
without a network.
"""
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

from core import version  # noqa: E402


def test_ordering_by_release_number():
    assert version.compare("0.5.0", "0.5.1") == -1
    assert version.compare("0.5.1", "0.5.0") == 1
    assert version.compare("0.5.1", "0.5.1") == 0
    assert version.compare("0.4.4", "0.5.0") == -1
    assert version.compare("1.0.0", "0.9.9") == 1


def test_double_digit_component_is_not_string_compared():
    # The eyeball trap: as strings "0.5.10" < "0.5.9", but as versions it is newer.
    assert version.compare("0.5.10", "0.5.9") == 1
    assert version.compare("0.5.9", "0.5.10") == -1


def test_leading_v_is_tolerated_on_either_side():
    assert version.compare("v0.5.1", "0.5.1") == 0
    assert version.compare("0.5.0", "v0.5.1") == -1
    assert version.compare("V0.5.2", "v0.5.1") == 1


def test_shorter_release_is_zero_padded():
    assert version.compare("0.5", "0.5.0") == 0
    assert version.compare("1", "1.0.0") == 0
    assert version.compare("0.5", "0.5.1") == -1


def test_prerelease_sorts_below_its_release():
    assert version.compare("0.5.1-rc.1", "0.5.1") == -1
    assert version.compare("0.5.1", "0.5.1-rc.1") == 1
    assert version.compare("0.5.1-alpha", "0.5.1-beta") == -1
    assert version.compare("0.5.1-rc.1", "0.5.1-rc.1") == 0


def test_unparseable_input_compares_to_none():
    assert version.compare(None, "0.5.1") is None
    assert version.compare("0.5.1", None) is None
    assert version.compare("not-a-version", "0.5.1") is None
    assert version.compare("", "0.5.1") is None


def test_currency_words():
    assert version.currency("0.5.1", "0.5.1") == "current"
    assert version.currency("0.5.0", "0.5.1") == "behind"
    assert version.currency("0.6.0", "0.5.1") == "ahead"


def test_currency_unknown_never_reads_as_up_to_date():
    # A missing or unreadable latest must not be mistaken for "current".
    assert version.currency("0.5.1", None) == "unknown"
    assert version.currency("0.5.1", "") == "unknown"
    assert version.currency(None, "0.5.1") == "unknown"
    assert version.currency("0.5.1", "garbage") == "unknown"

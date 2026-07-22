"""The advisory redaction scan.

Every fixture below is a deliberate fake: letter-bearing, never a real
credential shape long enough to be mistaken for one, and never a digit run
long enough to trip the repo audit's phone-shaped pattern.
"""
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "plugin" / "lib"
sys.path.insert(0, str(LIB))

import pytest  # noqa: E402

from core import redact  # noqa: E402


# Fakes, one per pattern. Keys are the pattern names scan() reports.
FAKES = {
    "telegram-bot-token": "1234567:FAKE-BOT-TOKEN-VALUE-abcdefghijklmnop",
    "wordpress-app-password": "abcd EFGH 1234 ijkl MNOP qrst",
    "authorization-bearer": "Authorization: Bearer FAKE-BEARER-VALUE-abcdefgh",
    "api-key-assignment": "api_key=FAKE-API-KEY-VALUE-abcdefghij",
    # .test is the reserved test TLD (RFC 2606): detectable here without
    # planting a live-looking personal address in the repo.
    "personal-email": "someone@gmail.test",
    "phone-number": "(555) 010-0199",
    "local-path": "/Users/example/organic-hq/example-com/site-profile.yaml",
}

CLEAN = ("The weekly report covers 12 pages and 3 sections. Clicks rose from "
         "120 to 150 while average position held at 8.4 on 2026-07-13. "
         "Nothing here is a secret and no token was needed to read it.")


def _tier_of(name):
    return {"telegram-bot-token": "high", "wordpress-app-password": "high",
            "authorization-bearer": "high", "api-key-assignment": "high",
            "personal-email": "medium", "phone-number": "medium",
            "local-path": "low"}[name]


# -- detection per tier -------------------------------------------------------

def test_high_tier_telegram_bot_token_shape():
    found = redact.scan(f"the bot replied with {FAKES['telegram-bot-token']} at noon")
    assert [f["tier"] for f in found] == ["high"]
    assert found[0]["pattern"] == "telegram-bot-token"


def test_high_tier_wordpress_application_password_shape():
    found = redact.scan(f"app password {FAKES['wordpress-app-password']} for the editor")
    assert any(f["tier"] == "high" and f["pattern"] == "wordpress-app-password"
               for f in found)


def test_high_tier_authorization_bearer_header():
    found = redact.scan(f"curl -H '{FAKES['authorization-bearer']}' https://example.com")
    assert any(f["tier"] == "high" and f["pattern"] == "authorization-bearer"
               for f in found)


def test_high_tier_generic_key_assignment():
    found = redact.scan(f"config line: {FAKES['api-key-assignment']}")
    assert any(f["tier"] == "high" and f["pattern"] == "api-key-assignment"
               for f in found)


def test_medium_tier_personal_email_provider():
    found = redact.scan(f"reply to {FAKES['personal-email']} when done")
    assert [(f["tier"], f["pattern"]) for f in found] == [("medium", "personal-email")]


def test_medium_tier_phone_shaped_digit_run():
    found = redact.scan(f"call {FAKES['phone-number']} for the handover")
    assert [(f["tier"], f["pattern"]) for f in found] == [("medium", "phone-number")]


def test_low_tier_absolute_local_paths():
    for raw in (FAKES["local-path"], "/home/example/organic-hq/brain",
                r"C:\Users\example\organic-hq\brain"):
        found = redact.scan(f"the brain lives at {raw}")
        assert [(f["tier"], f["pattern"]) for f in found] == [("low", "local-path")], raw


def test_findings_carry_exactly_the_documented_keys():
    found = redact.scan(FAKES["telegram-bot-token"])
    assert found and all(set(f) == {"tier", "pattern", "excerpt"} for f in found)


# -- masking ------------------------------------------------------------------

# Parametrized by NAME only: a pytest node id built from the fake values
# would write them into .pytest_cache, where the repo audit greps.
@pytest.mark.parametrize("name", sorted(FAKES))
def test_excerpt_never_contains_the_raw_match(name):
    raw = FAKES[name]
    found = redact.scan(f"line before\n{raw}\nline after")
    assert found, f"{name} was not detected at all"
    for f in found:
        assert raw not in f["excerpt"], f"{name} excerpt leaked the raw value"
        assert "*" in f["excerpt"], f"{name} excerpt was not masked"
        # At most the first 4 and the last 2 characters survive.
        assert f["excerpt"].startswith(raw[:4])
        assert f["excerpt"].endswith(raw[-2:])
        assert raw[4:-2] not in f["excerpt"]


def test_short_match_is_masked_whole():
    # Nothing shorter than head+tail may show head+tail: that would be the
    # raw value with extra steps.
    assert set(redact._mask("abc123")) == {"*"}


# -- clean input --------------------------------------------------------------

def test_clean_text_returns_no_findings():
    assert redact.scan(CLEAN) == []


def test_prose_that_merely_looks_technical_does_not_false_positive():
    prose = ("We reviewed the token bucket, the secret sauce behind the "
             "cache, and four short words like this that sit in a row. "
             "Sessions were 120 150 3400 22 across the four days.")
    assert redact.scan(prose) == []


def test_empty_input_is_clean():
    assert redact.scan("") == []
    assert redact.scan(None) == []


# -- summarize ----------------------------------------------------------------

def test_summarize_is_empty_when_there_is_nothing_to_report():
    assert redact.summarize([]) == ""
    assert redact.summarize(redact.scan(CLEAN)) == ""


def test_summarize_counts_by_tier_highest_first():
    findings = [{"tier": "medium", "pattern": "p", "excerpt": "x"},
                {"tier": "high", "pattern": "p", "excerpt": "x"},
                {"tier": "medium", "pattern": "p", "excerpt": "x"}]
    line = redact.summarize(findings)
    assert line == "redaction: 1 high, 2 medium finding(s) - see the run report"


def test_summarize_omits_tiers_with_no_findings():
    line = redact.summarize([{"tier": "low", "pattern": "p", "excerpt": "x"}])
    assert line == "redaction: 1 low finding(s) - see the run report"
    assert "high" not in line and "medium" not in line


def test_summarize_never_carries_an_excerpt():
    findings = redact.scan(FAKES["telegram-bot-token"])
    line = redact.summarize(findings)
    assert FAKES["telegram-bot-token"] not in line
    assert findings[0]["excerpt"] not in line


# -- the honest limit ---------------------------------------------------------

def test_module_docstring_states_that_it_only_reports():
    doc = (redact.__doc__ or "").lower()
    assert "advisory" in doc
    assert "does not block" in doc
    assert "does not prevent" in doc

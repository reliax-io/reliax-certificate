import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from reliax_certificate.wording import render_certificate, check_wording  # noqa: E402
from reliax_certificate.fidelity import fidelity_check  # noqa: E402
from reliax_certificate.schema import validate_payload  # noqa: E402

EX = pathlib.Path(__file__).resolve().parent.parent / "examples" / "chain.json"


def _payloads():
    return [r["payload"] for r in json.loads(EX.read_text())["records"]]


def test_example_payloads_validate_and_render_to_the_stored_text():
    for p in _payloads():
        assert validate_payload(p) == []
        assert render_certificate(p) == p["certificate_text"]
        assert check_wording(p["certificate_text"]) == []
        assert "n = 7,500" in p["certificate_text"] and "sha256 3f9a" in p["certificate_text"]
        assert "not a probability" in p["certificate_text"]


def test_banned_wording():
    assert check_wording("This decision is 95% reliable.")
    assert check_wording("the probability that this applicant repays is 0.97")
    assert check_wording("declined by Reliax")
    assert check_wording("Prediction set {repay}, contains the true outcome at least 95% of the time.") == []


def test_fidelity_accepts_signed_values_and_rejects_others():
    p = _payloads()[0]
    good = "The certified set is {repay}; coverage target 95%; credibility 0.61; bracket 0.02 to 0.05; calibration set of 7,500 rows."
    assert fidelity_check(good, p)["ok"]
    bad = fidelity_check("Coverage 97% and credibility 0.61, so this decision is 95% reliable.", p)
    assert not bad["ok"] and "97%" in bad["unsupported_numbers"] and bad["banned_phrases"]


def test_validate_payload_reports_issues():
    p = json.loads(json.dumps(_payloads()[0]))
    p["credibility"] = 1.5; p["routing"]["route"] = "DECLINE"; del p["calibration_set"]["sha256"]
    issues = validate_payload(p)
    assert any("credibility" in i for i in issues) and any("routing.route" in i for i in issues) and any("calibration_set.sha256" in i for i in issues)


def test_v16_records_still_verify_against_their_own_version():
    """A record written under schema v16 and template 16.0 names the calibration set
    ``cohort`` and prints the word; it must still validate and re-render byte for byte."""
    v16 = pathlib.Path(__file__).resolve().parent.parent / "examples" / "chain.v16.json"
    for p in [r["payload"] for r in json.loads(v16.read_text())["records"]]:
        assert p["versions"]["schema_version"] == 16 and "cohort" in p
        assert validate_payload(p) == []
        assert render_certificate(p) == p["certificate_text"]
        assert "calibration cohort C" in p["certificate_text"]


def test_current_template_does_not_say_cohort():
    for p in _payloads():
        assert p["versions"]["schema_version"] == 17 and "calibration_set" in p and "cohort" not in p
        assert "cohort" not in p["certificate_text"]
        assert "calibration set C" in p["certificate_text"]

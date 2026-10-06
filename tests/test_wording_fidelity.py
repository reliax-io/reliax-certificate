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


def test_current_template_names_the_calibration_set_and_the_rule():
    for p in _payloads():
        assert p["versions"]["schema_version"] == 18 and "calibration_set" in p
        assert "rule" in p["routing"] and "row" not in p["routing"]
        assert all("rule" in t and "row" not in t for t in p["routing"]["route_trace"])
        assert "calibration set C" in p["certificate_text"] and " row " not in p["certificate_text"]
    texts = [p["certificate_text"] for p in _payloads()]
    assert "Route trace: rules 1 to 5 passed; rule 6 allows." in texts[0]
    assert "Route trace: rules 1 and 2 passed; rule 3 fired." in texts[1]


def test_trace_text_covers_every_rule():
    from reliax_certificate.wording import trace_text
    assert [trace_text(r) for r in range(1, 7)] == [
        "Route trace: rule 1 fired.",
        "Route trace: rule 1 passed; rule 2 fired.",
        "Route trace: rules 1 and 2 passed; rule 3 fired.",
        "Route trace: rules 1 to 3 passed; rule 4 fired.",
        "Route trace: rules 1 to 4 passed; rule 5 fired.",
        "Route trace: rules 1 to 5 passed; rule 6 allows.",
    ]

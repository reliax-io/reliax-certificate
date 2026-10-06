"""Build examples/chain.json: two sealed records, one ALLOW and one REVIEW.

Values are illustrative. The route, trace and reasons come from reliax-core's
evaluator when it is installed, so `reliax verify examples/chain.json --recompute`
passes; without it the stored values below are used as they are.
"""
import json
import pathlib

from reliax_certificate import SCHEMA_VERSION, TEMPLATE_VERSION, render_certificate, seal

try:
    from reliax_core import __version__ as CORE_VERSION
    from reliax_core.evaluator import Envelope, Policy, evaluate
except ImportError:  # pragma: no cover
    CORE_VERSION, evaluate = "0.3.0", None

POLICY = {"name": "credit-pd", "version": "4", "alpha": 0.05, "credibility_floor": 0.01, "credibility_extreme": 0.001,
          "invalid_action": "BLOCK", "ood_action": "REVIEW", "ood_extreme_action": "BLOCK", "watch_action": "INFO",
          "bracket_on": True, "pd_upper_allow_max": 0.12, "approve_label": 0}
CALIBRATION_SET = {"name": "C", "n": 7500, "frozen": "2026-06-30", "sha256": "3f9a" + "0" * 60}
SEGMENT = {"name": "thin-file", "definition_hash": "8c1d" + "0" * 60}


def payload(audit_id, ts, prob, labels, cred, bracket, cell_n, codes):
    p = {
        "audit_id": audit_id, "timestamp": ts, "prediction_id": "pred-" + audit_id[-4:], "model_id": "scorecard-v7",
        "mode": "gate", "enforced": True, "domain": "credit PD", "unit": "applicant",
        "versions": {"schema_version": SCHEMA_VERSION, "core_version": CORE_VERSION, "template_version": TEMPLATE_VERSION},
        "policy": POLICY, "calibration_set": CALIBRATION_SET, "segment": SEGMENT,
        "prediction": {"label": 0, "label_name": "repay", "probability": prob},
        "model_reason_codes": codes,
        "coverage_set": {"labels": labels, "label_names": ["repay", "default"][: len(labels)] if labels == [0] else ["repay", "default"]},
        "qhat": 0.62, "credibility": cred,
        "bracket": {"p0": bracket[0], "p1": bracket[1], "on": True},
        "calibration_line": f"The stated probability carries a calibration error of 0.08 on {cell_n} calibration observations in this cell, segment thin-file, error bar ±0.07 at 95%",
        "cell_n": cell_n, "ood": {"flag": False, "percentile": 41.0},
        "drift": {"inputs": "OK", "outcomes": {"as_of": "2026-08-31", "n": 1240, "verdict": "OK"}},
        "martingale": {"stream_id": "credit-pd/thin-file", "seed": 7, "log10_wealth": 0.12, "resets": 0},
        "guarantee": {"state": "active", "scope": "stage"},
        "criticality": 16 if labels == [0] else 44, "auditor_flag": False,
    }
    if evaluate is not None:
        d = evaluate(Policy.from_dict(POLICY), Envelope(credibility=cred, prediction_set=tuple(labels), predicted_label=0,
                                                        bracket=bracket, drift_state="OK", cell_n=cell_n))
        p["routing"] = d.as_dict()
    else:
        rule = 6 if labels == [0] else 3
        p["routing"] = {"route": "ALLOW" if rule == 6 else "REVIEW", "rule": rule,
                        "reason_codes": ["CERTIFIED"] if rule == 6 else ["SET_AMBIGUOUS"],
                        "certificate_reasons": (["input within the scope of the guarantee", "one label left standing", f"{cell_n} observations in the cell"]
                                                if rule == 6 else ["2 labels left standing: the model cannot separate them for this case"])}
    p["certificate_text"] = render_certificate(p)
    return p


def main():
    p1 = payload("rxe_7f3a9b", "2026-09-10T09:14:07Z", 0.03, [0], 0.61, (0.02, 0.05), 412, ["R01", "R07"])
    r1 = seal(p1)
    p2 = payload("rxe_7f3a9c", "2026-09-10T09:14:09Z", 0.31, [0, 1], 0.44, (0.11, 0.19), 388, ["R03"])
    r2 = seal(p2, r1["hash"])
    out = pathlib.Path(__file__).with_name("chain.json")
    out.write_text(json.dumps({"records": [r1, r2]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", out, "head", r2["hash"][:12])


if __name__ == "__main__":
    main()

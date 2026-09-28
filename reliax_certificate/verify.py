"""The verifier: what an auditor runs on a record, or a chain of records.

Record-only replay, always: schema, hash chain, stored wording against the
template, banned wording, routing consistency (the reason codes match the row).
Full replay, when reliax-core is installed and the record carries the
envelope: the route is recomputed and compared with the stored one.
"""
import json

from .chain import verify_chain
from .schema import validate_payload
from .wording import render_certificate, check_wording

_ROW_CODES = {1: {"ENVELOPE_INVALID"}, 2: {"OOD_EXTREME", "OOD_INPUT"}, 3: {"EMPTY_SET", "SET_AMBIGUOUS"},
              4: {"PD_UPPER_EXCEEDS_CEILING"}, 5: {"DRIFT_WATCH"}, 6: {"CERTIFIED"}}


def _routing_consistency(payload: dict) -> list:
    r = payload["routing"]
    issues = []
    codes = set(r.get("reason_codes", []))
    if not codes <= _ROW_CODES.get(r["row"], set()):
        issues.append(f"routing: reason codes {sorted(codes)} do not belong to row {r['row']}")
    if r["row"] == 6 and r["route"] != "ALLOW":
        issues.append("routing: row 6 must route ALLOW")
    if r["row"] in (3, 4) and r["route"] != "REVIEW":
        issues.append(f"routing: row {r['row']} must route REVIEW")
    if payload["drift"]["inputs"] == "ALARM" and r["row"] != 1:
        issues.append("routing: ALARM on the stream must match row 1")
    return issues


def _recompute_route(payload: dict) -> list:
    try:
        from reliax_core.evaluator import Envelope, Policy, evaluate
    except ImportError:
        return ["recompute: reliax-core is not installed"]
    pol = payload["policy"]
    env_fields = {
        "credibility": payload["credibility"],
        "prediction_set": tuple(payload["coverage_set"].get("labels", [])),
        "predicted_label": payload.get("prediction", {}).get("label"),
        "bracket": (payload["bracket"]["p0"], payload["bracket"]["p1"]) if payload.get("bracket") else None,
        "drift_state": payload["drift"]["inputs"],
        "guarantee_state": payload["guarantee"]["state"],
        "cell_n": payload.get("cell_n"),
    }
    policy = Policy.from_dict({k: v for k, v in pol.items() if k in Policy.__dataclass_fields__})
    d = evaluate(policy, Envelope(**env_fields))
    stored = payload["routing"]
    issues = []
    if d.route != stored["route"] or d.row != stored["row"]:
        issues.append(f"recompute: route {d.route} row {d.row} recomputed, record says {stored['route']} row {stored['row']}")
    if list(d.reason_codes) != list(stored.get("reason_codes", [])):
        issues.append(f"recompute: reason codes {list(d.reason_codes)} recomputed, record says {stored.get('reason_codes')}")
    if list(d.certificate_reasons) != list(stored.get("certificate_reasons", [])):
        issues.append("recompute: certificate reasons differ from the record")
    return issues


def verify_records(records: list, recompute: bool = False) -> dict:
    """Verify a chain. Every record is checked; the report names each problem."""
    chain = verify_chain(records)
    per_record = []
    for i, rec in enumerate(records):
        issues = []
        payload = rec.get("payload") if isinstance(rec, dict) else None
        if not isinstance(payload, dict):
            per_record.append({"index": i, "ok": False, "issues": ["no payload"]})
            continue
        issues += validate_payload(payload)
        if not issues:
            expected = render_certificate(payload)
            if payload["certificate_text"] != expected:
                issues.append("wording: stored certificate text differs from the template rendering")
            banned = check_wording(payload["certificate_text"])
            if banned:
                issues.append("wording: banned phrase in the stored text: " + "; ".join(banned))
            issues += _routing_consistency(payload)
            if recompute:
                issues += _recompute_route(payload)
        per_record.append({"index": i, "ok": not issues, "audit_id": payload.get("audit_id"), "issues": issues})
    ok = chain["ok"] and all(r["ok"] for r in per_record)
    return {"ok": ok, "records": len(records), "chain": chain, "per_record": per_record, "recomputed": recompute}


def load_records(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "records" in data:
        return list(data["records"])
    if isinstance(data, dict):
        return [data]
    return list(data)


def verify_file(path: str, recompute: bool = False) -> dict:
    return verify_records(load_records(path), recompute=recompute)

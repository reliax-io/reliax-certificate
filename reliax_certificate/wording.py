"""The certificate wording template (v16) and the banned wording.

The text a reviewer sees is rendered from signed fields only and stored in the
record verbatim, so anything said later about a decision can be checked against
what was certified. The template is the same in every domain; only the cohort,
the segment and the policy change. Never a percentage next to a single decision.
"""
import re

from .schema import TEMPLATE_VERSION  # noqa: F401  (re-exported for callers)

# Phrases that turn a cohort statement into a personal probability, or bring
# in vocabulary the certificate does not use. Case-insensitive regular expressions.
BANNED_WORDING = (
    r"\b\d{1,3}(\.\d+)?\s?%\s*(reliable|reliability|safe|accurate|correct|sure|certain)\b",
    r"(?<!not a )\b(probability|chance|likelihood|odds)\s+(that\s+)?(this|the)\s+(applicant|case|decision|customer|patient|claim|person)\b",
    r"\bthis (decision|prediction|answer) is \d{1,3}(\.\d+)?\s?%",
    r"\b(distrust|disbelief|subjective logic)\b",
    r"\b(declined?|denied|refus(ed|al))\s+by\s+reliax\b",
    r"\bnot reliable enough\b",
)
_BANNED = [re.compile(p, re.I) for p in BANNED_WORDING]


def check_wording(text: str) -> list:
    """Every banned phrase found in the text, as matched substrings."""
    return [m.group(0) for rx in _BANNED for m in rx.finditer(text)]


def _pct(alpha: float) -> str:
    v = 100.0 * (1.0 - float(alpha))
    return f"{v:.0f}%" if abs(v - round(v)) < 1e-9 else f"{v:g}%"


def _num(x) -> str:
    return f"{float(x):.2f}"


def _short(h) -> str:
    return (str(h)[:4] + "…") if h else "…"


def render_certificate(p: dict) -> str:
    """Render the stored text from a payload. Deterministic; the verifier re-renders and compares."""
    labels = p["coverage_set"].get("labels", [])
    names = p["coverage_set"].get("label_names") or [str(v) for v in labels]
    set_text = "{" + ", ".join(names) + "}" if names else "{}"
    c, s, pol, g = p["cohort"], p["segment"], p["policy"], p["guarantee"]
    lines = [
        f"Certificate · {p['audit_id']} · {p.get('domain', 'decision')} · evaluated · {p['timestamp']}",
        (f"Prediction set {set_text}, produced by a procedure that on calibration cohort {c['name']} "
         f"(n = {int(c['n']):,}, frozen {c['frozen']}, sha256 {_short(c['sha256'])}) and segment {s['name']} "
         f"(definition hash {_short(s['definition_hash'])}) contains the true outcome at least {_pct(pol['alpha'])} of the time."),
    ]
    drift_in = p["drift"]["inputs"]
    cred = float(p["credibility"])
    floor = float(pol.get("credibility_floor", 0.01))
    if drift_in == "ALARM" or g["state"] == "suspended":
        ex = "ALARM, guarantee suspended on this segment"
    else:
        ex = "no alarm"
    scope_word = "consistent with" if cred >= floor else "outside the scope of"
    lines.append(f"Exchangeability at this point: {ex}. Credibility {_num(cred)}: this input is {scope_word} cohort {c['name']}.")
    pred = p.get("prediction", {})
    br = p.get("bracket")
    cal = []
    if pred.get("probability") is not None:
        cal.append(f"Calibration at this score level: model said {_num(pred['probability'])}.")
    if br:
        cal.append(f"Calibrated bracket [{_num(br['p0'])}, {_num(br['p1'])}].")
    if p.get("calibration_line"):
        cal.append(str(p["calibration_line"]).rstrip(".") + ".")
    if cal:
        lines.append(" ".join(cal))
    out = p["drift"].get("outcomes")
    if out and out.get("as_of"):
        n = out.get("n")
        lines.append(f"Drift: inputs and scores {drift_in}. Outcome recheck as of {out['as_of']}"
                     + (f", n = {int(n):,}" if n is not None else "") + f": {out.get('verdict', 'OK')}.")
    else:
        lines.append(f"Drift: inputs and scores {drift_in}. Outcome recheck pending.")
    r = p["routing"]
    route_line = f"Routing: {r['route']} under policy {pol['name']}@{pol['version']} · guarantee scope: {g.get('scope', 'stage')}"
    if p.get("criticality") is not None:
        route_line += f" · criticality {int(round(float(p['criticality'])))} (advisory)"
    if g["state"] != "active":
        route_line += f" · guarantee: {g['state']}"
    lines.append(route_line)
    if r["row"] == 1:
        trace = "Route trace: row 1 matched."
    else:
        trace = f"Route trace: row {int(r['row'])} matched, so every check above it passed."
    reasons = "; ".join(r.get("certificate_reasons", [])) or "none recorded"
    codes = p.get("model_reason_codes") or []
    carried = ("The model's own reason codes are recorded as received: " + ", ".join(str(x) for x in codes) + "."
               if codes else "The model gave no reason codes.")
    lines.append(f"Reasons: {trace} Certificate reasons: {reasons}. {carried}")
    unit = p.get("unit", "case")
    lines.append(f"Read this correctly: this is not a probability that this {unit} turns out well.")
    return "\n".join(lines)

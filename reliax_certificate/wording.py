"""The certificate wording template and the banned wording.

The text a reviewer sees is rendered from signed fields only and stored in the
record verbatim, so anything said later about a decision can be checked against
what was certified. The template is the same in every domain; only the
calibration set, the segment and the policy change. Never a percentage next to
a single decision.

Template 18.0 is current and the only one this package renders. A record names
the template it was rendered with, so a later template is a new version and the
verifier can tell which one a record expects.
"""
import re

from .schema import TEMPLATE_VERSION, calibration_set_of  # noqa: F401  (TEMPLATE_VERSION re-exported for callers)

# Phrases that turn a statement about the calibration set into a personal
# probability, or bring in vocabulary the certificate does not use.
# Case-insensitive regular expressions.
BANNED_WORDING = (
    r"\b\d{1,3}(\.\d+)?\s?%\s*(reliable|reliability|safe|accurate|correct|sure|certain)\b",
    r"(?<!not a )\b(probability|chance|likelihood|odds)\s+(that\s+)?(this|the)\s+(applicant|case|decision|customer|patient|claim|person)\b",
    r"\bthis (decision|prediction|answer) is \d{1,3}(\.\d+)?\s?%",
    r"\b(distrust|disbelief|subjective logic)\b",
    r"\b(declined?|denied|refus(ed|al))\s+by\s+reliax\b",
    r"\bnot reliable enough\b",
)
_BANNED = [re.compile(p, re.I) for p in BANNED_WORDING]

# The noun the template uses for the calibration set, in the two places it is printed.
_SET_NOUN = {"18.0": ("calibration set", "calibration set")}


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


def trace_text(rule: int) -> str:
    """The route-trace sentence for the rule that fired (1 to 6); the same text reliax-core writes."""
    if rule == 1:
        return "Route trace: rule 1 fired."
    if rule == 2:
        return "Route trace: rule 1 passed; rule 2 fired."
    passed = "rules 1 and 2" if rule == 3 else f"rules 1 to {rule - 1}"
    return f"Route trace: {passed} passed; rule {rule} {'allows' if rule == 6 else 'fired'}."


def render_certificate(p: dict) -> str:
    """Render the stored text from a payload, with the template version the payload names.
    Deterministic; the verifier re-renders and compares."""
    tv = str((p.get("versions") or {}).get("template_version") or TEMPLATE_VERSION)
    long_noun, short_noun = _SET_NOUN.get(tv, _SET_NOUN[TEMPLATE_VERSION])
    labels = p["coverage_set"].get("labels", [])
    names = p["coverage_set"].get("label_names") or [str(v) for v in labels]
    set_text = "{" + ", ".join(names) + "}" if names else "{}"
    c, s, pol, g = calibration_set_of(p), p["segment"], p["policy"], p["guarantee"]
    lines = [
        f"Certificate · {p['audit_id']} · {p.get('domain', 'decision')} · evaluated · {p['timestamp']}",
        (f"Prediction set {set_text}, produced by a procedure that on {long_noun} {c['name']} "
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
    lines.append(f"Exchangeability at this point: {ex}. Credibility {_num(cred)}: this input is {scope_word} {short_noun} {c['name']}.")
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
    trace = trace_text(int(r["rule"]))
    reasons = "; ".join(r.get("certificate_reasons", [])) or "none recorded"
    codes = p.get("model_reason_codes") or []
    carried = ("The model's own reason codes are recorded as received: " + ", ".join(str(x) for x in codes) + "."
               if codes else "The model gave no reason codes.")
    lines.append(f"Reasons: {trace} Certificate reasons: {reasons}. {carried}")
    unit = p.get("unit", "case")
    lines.append(f"Note: this is not a probability that this {unit} turns out well.")
    return "\n".join(lines)

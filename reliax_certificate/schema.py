"""Envelope schema: the fields of a record's payload and the class of each.

Classes (one per field, never mixed):
  guarantee  a theorem holds on exchangeable data at the stated level
  exact      recomputed bit for bit from the record (routing, hashes, versions)
  signal     a measurement without such a proof; advisory, never in a routing rule
  rule       a threshold or definition the deployer set, kept as a policy version
  carried    recorded as received from the deployer's model, never altered
  record     bookkeeping (ids, timestamps, mode)

The current schema is v17 (schema/certificate.v17.json). Records written under
v16 differ in one field name: the calibration set was called ``cohort``. The
verifier reads both, each against its own version; new records are v17.
``validate_payload`` is the dependency-free check the verifier runs.
"""
SCHEMA_VERSION = 17
TEMPLATE_VERSION = "17.0"
SUPPORTED_SCHEMA_VERSIONS = (16, 17)

GUARANTEE_STATES = ("active", "suspended", "under estimated covariate shift", "outcome recheck pending")
GUARANTEE_SCOPES = ("stage", "end_to_end")
ROUTES = ("ALLOW", "REVIEW", "BLOCK")
DRIFT_STATES = ("OK", "WATCH", "ALARM")
MODES = ("observe", "gate")

FIELD_CLASSES = {
    "audit_id": "record", "timestamp": "record", "prediction_id": "record", "model_id": "record",
    "mode": "record", "enforced": "record", "domain": "record", "unit": "record", "latency_ms": "record",
    "versions": "exact",
    "policy": "rule",
    "calibration_set": "exact",   # name, n, freeze date, sha256 of the calibration rows
    "segment": "rule",            # name and definition hash, chosen by the deployer's MRM
    "prediction": "carried",      # the model's answer and probabilities, as received
    "model_reason_codes": "carried",
    "coverage_set": "guarantee",
    "qhat": "exact",
    "credibility": "guarantee",
    "bracket": "guarantee",
    "calibration_line": "signal",
    "cell_n": "exact",
    "ood": "signal",
    "drift": "guarantee",         # live state is anytime-valid; the outcome verdict is dated
    "martingale": "exact",
    "guarantee": "guarantee",     # state and scope
    "routing": "exact",           # route, row, trace, reason codes, certificate reasons
    "criticality": "signal",
    "auditor_flag": "signal",
    "certificate_text": "exact",
}

# The field that names the calibration set, per schema version.
CALIBRATION_SET_KEY = {16: "cohort", 17: "calibration_set"}

REQUIRED = ("audit_id", "timestamp", "model_id", "mode", "enforced", "versions", "policy",
            "segment", "prediction", "coverage_set", "credibility", "drift", "guarantee", "routing",
            "certificate_text")


def schema_version_of(payload: dict) -> int:
    """The schema version a payload names, or the current one when it names none."""
    v = payload.get("versions") if isinstance(payload, dict) else None
    sv = v.get("schema_version") if isinstance(v, dict) else None
    return sv if sv in SUPPORTED_SCHEMA_VERSIONS else SCHEMA_VERSION


def calibration_set_of(payload: dict) -> dict:
    """The calibration-set object of a payload, whichever version named it."""
    return payload.get(CALIBRATION_SET_KEY[schema_version_of(payload)], {})


def _issue(issues, path, msg):
    issues.append(f"{path}: {msg}")


def validate_payload(payload: dict) -> list:
    """Structural check of one payload against the schema version it names.
    Returns a list of issues; empty means valid."""
    issues = []
    if not isinstance(payload, dict):
        return ["payload: not an object"]
    v = payload.get("versions", {})
    sv = v.get("schema_version") if isinstance(v, dict) else None
    if sv not in SUPPORTED_SCHEMA_VERSIONS:
        _issue(issues, "versions.schema_version", f"must be one of {SUPPORTED_SCHEMA_VERSIONS}")
        sv = SCHEMA_VERSION
    cs_key = CALIBRATION_SET_KEY[sv]
    allowed_fields = {k if k != "calibration_set" else cs_key for k in FIELD_CLASSES}
    for k in REQUIRED + (cs_key,):
        if k not in payload:
            _issue(issues, k, "missing")
    for k in payload:
        if k not in allowed_fields:
            _issue(issues, k, "unknown field (every field must carry a class)")
    for k in ("core_version", "template_version"):
        if not isinstance(v.get(k), str) or not v.get(k):
            _issue(issues, f"versions.{k}", "missing")
    if payload.get("mode") not in MODES:
        _issue(issues, "mode", f"must be one of {MODES}")
    if not isinstance(payload.get("enforced"), bool):
        _issue(issues, "enforced", "must be a boolean")
    pol = payload.get("policy", {})
    if not isinstance(pol, dict) or not pol.get("name") or not pol.get("version"):
        _issue(issues, "policy", "needs name and version")
    if not isinstance(pol.get("alpha"), (int, float)) or not 0 < pol.get("alpha", 1) < 1:
        _issue(issues, "policy.alpha", "must lie in (0, 1)")
    c = payload.get(cs_key, {})
    for k in ("name", "n", "frozen", "sha256"):
        if k not in c:
            _issue(issues, f"{cs_key}.{k}", "missing")
    if isinstance(c.get("n"), bool) or not isinstance(c.get("n"), int) or c.get("n", 0) <= 0:
        _issue(issues, f"{cs_key}.n", "must be a positive integer")
    seg = payload.get("segment", {})
    if not isinstance(seg, dict) or "name" not in seg or "definition_hash" not in seg:
        _issue(issues, "segment", "needs name and definition_hash")
    cs = payload.get("coverage_set", {})
    if not isinstance(cs, dict) or not isinstance(cs.get("labels"), list):
        _issue(issues, "coverage_set.labels", "must be a list")
    cred = payload.get("credibility")
    if not isinstance(cred, (int, float)) or not 0 < cred <= 1:
        _issue(issues, "credibility", "must lie in (0, 1]")
    br = payload.get("bracket")
    if br is not None:
        if not isinstance(br, dict) or not all(isinstance(br.get(k), (int, float)) for k in ("p0", "p1")):
            _issue(issues, "bracket", "needs p0 and p1")
        elif not 0 <= br["p0"] <= br["p1"] <= 1:
            _issue(issues, "bracket", "needs 0 <= p0 <= p1 <= 1")
    d = payload.get("drift", {})
    if not isinstance(d, dict) or d.get("inputs") not in DRIFT_STATES:
        _issue(issues, "drift.inputs", f"must be one of {DRIFT_STATES}")
    g = payload.get("guarantee", {})
    if not isinstance(g, dict) or g.get("state") not in GUARANTEE_STATES:
        _issue(issues, "guarantee.state", f"must be one of {GUARANTEE_STATES}")
    if isinstance(g, dict) and g.get("scope") not in GUARANTEE_SCOPES:
        _issue(issues, "guarantee.scope", f"must be one of {GUARANTEE_SCOPES}")
    r = payload.get("routing", {})
    if not isinstance(r, dict) or r.get("route") not in ROUTES:
        _issue(issues, "routing.route", f"must be one of {ROUTES}")
    elif not isinstance(r.get("row"), int) or not 1 <= r["row"] <= 6:
        _issue(issues, "routing.row", "must be an integer from 1 to 6")
    elif not isinstance(r.get("reason_codes"), list) or not isinstance(r.get("certificate_reasons"), list):
        _issue(issues, "routing", "needs reason_codes and certificate_reasons lists")
    crit = payload.get("criticality")
    if crit is not None and (isinstance(crit, bool) or not isinstance(crit, (int, float)) or not 0 <= crit <= 100):
        _issue(issues, "criticality", "must lie in [0, 100]")
    if not isinstance(payload.get("certificate_text"), str) or not payload.get("certificate_text"):
        _issue(issues, "certificate_text", "missing")
    return issues

"""Fidelity check for any readable rendering of a certificate.

A readable view (a plain template or a customer-hosted language model) may say
only what the signed fields say. The check is mechanical: every number in the
rendering must appear among the signed values, in the same or an equivalent
form (0.95 and 95% are the same value), and no banned wording may appear. A
rendering that fails is replaced by the plain template; it never replaces the
certificate.
"""
import re

from .wording import check_wording

_NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(\s?%)?")


def _flatten(x, out):
    if isinstance(x, dict):
        for v in x.values():
            _flatten(v, out)
    elif isinstance(x, (list, tuple)):
        for v in x:
            _flatten(v, out)
    elif isinstance(x, bool):
        return
    elif isinstance(x, (int, float)):
        out.append(float(x))
    elif isinstance(x, str):
        for m in _NUM.finditer(x):
            out.append(_value(m))


def _value(m) -> float:
    v = float(m.group(1).replace(",", ""))
    return v / 100.0 if m.group(2) else v


def _allowed(payload: dict) -> set:
    vals = []
    _flatten(payload, vals)
    allowed = set(vals)
    alpha = (payload.get("policy") or {}).get("alpha")
    if isinstance(alpha, (int, float)) and not isinstance(alpha, bool):
        allowed.add(1.0 - float(alpha))   # the level may be written as the target: alpha 0.05 is the 95% target
    return allowed


def _decimals(m) -> int:
    tok = m.group(1)
    d = len(tok.split(".")[1]) if "." in tok else 0
    return d + 2 if m.group(2) else d   # 95% is 0.95 written to two decimals


def _matches(x: float, d: int, allowed: set) -> bool:
    rx = round(x, d)
    return any(abs(round(a, d) - rx) < 1e-9 for a in allowed)


def fidelity_check(text: str, payload: dict) -> dict:
    """ok is True when every number in the text is a signed value, at the precision the
    text uses, and no banned wording appears."""
    allowed = _allowed(payload)
    unsupported = []
    for m in _NUM.finditer(text):
        if not _matches(_value(m), _decimals(m), allowed):
            unsupported.append(m.group(0).strip())
    banned = check_wording(text)
    return {"ok": not unsupported and not banned, "unsupported_numbers": unsupported, "banned_phrases": banned}

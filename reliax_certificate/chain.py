"""The hash chain (technical documentation, section 2.12).

    record_hash_k = SHA-256( record_hash_{k-1} || canonical_JSON(payload_k) )
    record_hash_0 = "0" * 64

Canonical JSON is sorted keys, no whitespace, UTF-8. The previous hash is
concatenated as its 64 hexadecimal characters. Any edit to a historical payload,
including a score, changes its hash and every hash after it; verification
reports the first index that no longer matches.
"""
import hashlib
import json

GENESIS = "0" * 64


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def record_hash(prev_hash: str, payload: dict) -> str:
    return hashlib.sha256((prev_hash + canonical_json(payload)).encode("utf-8")).hexdigest()


def seal(payload: dict, prev_hash: str = GENESIS) -> dict:
    """Wrap a payload as a record that links to the previous one."""
    return {"prev_hash": prev_hash, "hash": record_hash(prev_hash, payload), "payload": payload}


def verify_chain(records: list, expected_prev: str = GENESIS) -> dict:
    """Walk a list of records. ok is True only if every link and every hash holds."""
    errors = []
    prev = expected_prev
    first_bad = None
    for i, rec in enumerate(records):
        problems = []
        if not isinstance(rec, dict) or not all(k in rec for k in ("prev_hash", "hash", "payload")):
            problems.append("record needs prev_hash, hash and payload")
        else:
            if rec["prev_hash"] != prev:
                problems.append(f"prev_hash {rec['prev_hash'][:12]}... does not link to the previous record {prev[:12]}...")
            recomputed = record_hash(rec["prev_hash"], rec["payload"])
            if recomputed != rec["hash"]:
                problems.append("hash does not match the payload: the record was altered")
            prev = rec["hash"]
        if problems and first_bad is None:
            first_bad = i
        errors.extend(f"record {i}: {p}" for p in problems)
    return {"ok": not errors, "count": len(records), "first_bad_index": first_bad, "errors": errors,
            "head": prev if records else expected_prev}

"""reliax-certificate: the certificate format, the hash chain and the verifier.

What is written on a Reliax certificate is open and replayable: the schema
(v17, a class on every field; v16 records still verify), the canonical JSON and SHA-256 chain that seals
records, the wording template the stored text is rendered from, the banned
wording, the fidelity check for any readable rendering, and the verifier
``reliax verify record.json`` that walks a chain without contacting anyone.

No I/O beyond the CLI, no network, no dependency. Re-running the route from a
record needs reliax-core (optional).
"""
__version__ = "0.2.0"

from .schema import SCHEMA_VERSION, TEMPLATE_VERSION, FIELD_CLASSES, validate_payload
from .chain import GENESIS, canonical_json, record_hash, seal, verify_chain
from .wording import render_certificate, check_wording, BANNED_WORDING
from .fidelity import fidelity_check
from .verify import verify_records, verify_file

__all__ = [
    "__version__", "SCHEMA_VERSION", "TEMPLATE_VERSION", "FIELD_CLASSES", "validate_payload",
    "GENESIS", "canonical_json", "record_hash", "seal", "verify_chain",
    "render_certificate", "check_wording", "BANNED_WORDING",
    "fidelity_check", "verify_records", "verify_file",
]

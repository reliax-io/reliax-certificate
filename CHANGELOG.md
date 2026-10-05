# Changelog

## 0.3.0 (5 October 2026)

Schema v17 and template 17.0 are the only versions this package reads. The
v16 schema, the v1 policy schema, the v16 fixture and the verifier's
per-version branches are removed, with the former name of the calibration set
they carried. A v16 record is now reported as an unsupported schema version.
Nothing changes for v17 records.

## 0.2.0 (5 October 2026)

Envelope schema v17 and wording template 17.0: the calibration set is named
`calibration_set` in the payload and "calibration set" in the stored text,
replacing the former name used by v16 and 16.0. Nothing else changes. The
policy schema is v2 for the same rename. Route recomputation targets
reliax-core 0.2.1.

## 0.1.0 (28 September 2026)

First release. Envelope schema v16 (`schema/certificate.v16.json`, a class on
every field: guarantee, exact, signal, rule, carried, record), the policy
schema, the rendering-record schema, TypeScript types, the canonical-JSON
SHA-256 hash chain, the certificate wording template (16.0) with the banned
wording, the fidelity check for readable renderings, and the verifier
`reliax verify record.json`, with optional route recomputation through
reliax-core 0.2.0.

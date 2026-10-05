# Changelog

## 0.2.0 (5 October 2026)

Envelope schema v17 and wording template 17.0: the calibration set is named
`calibration_set` in the payload and "calibration set" in the stored text,
where v16 and 16.0 said `cohort` and "cohort". Nothing else changes. The
policy schema is v2 for the same rename. Records written under v16 still
verify: the verifier validates each record against the schema version it
names and re-renders its text with the template version it names
(`examples/chain.v16.json` is kept as the fixture). New records are v17.
Route recomputation targets reliax-core 0.2.1.

## 0.1.0 (28 September 2026)

First release. Envelope schema v16 (`schema/certificate.v16.json`, a class on
every field: guarantee, exact, signal, rule, carried, record), the policy
schema, the rendering-record schema, TypeScript types, the canonical-JSON
SHA-256 hash chain, the certificate wording template (16.0) with the banned
wording, the fidelity check for readable renderings, and the verifier
`reliax verify record.json`, with optional route recomputation through
reliax-core 0.2.0.

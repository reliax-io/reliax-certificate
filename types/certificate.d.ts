// Reliax certificate: envelope schema v16. Mirrors schema/certificate.v16.json.
// Every field carries one class: guarantee, exact, signal, rule, carried or record.

export type Route = "ALLOW" | "REVIEW" | "BLOCK";
export type DriftState = "OK" | "WATCH" | "ALARM";
export type GuaranteeState = "active" | "suspended" | "under estimated covariate shift" | "outcome recheck pending";
export type GuaranteeScope = "stage" | "end_to_end";
export type Mode = "observe" | "gate";
export type FieldClass = "guarantee" | "exact" | "signal" | "rule" | "carried" | "record";
export type ReasonCode =
  | "ENVELOPE_INVALID" | "OOD_EXTREME" | "OOD_INPUT" | "EMPTY_SET" | "SET_AMBIGUOUS"
  | "PD_UPPER_EXCEEDS_CEILING" | "DRIFT_WATCH" | "CERTIFIED";

export interface Versions { schema_version: 16; core_version: string; core_commit?: string; template_version: string; }

export interface Policy {                       // rule
  name: string; version: string; alpha: number;
  credibility_floor?: number; credibility_extreme?: number;
  invalid_action?: Route; ood_action?: Route; ood_extreme_action?: Route; watch_action?: "REVIEW" | "INFO";
  bracket_on?: boolean; pd_upper_allow_max?: number | null; approve_label?: number | null;
  thresholds?: Record<string, unknown>;
}

export interface Cohort { name: string; n: number; frozen: string; sha256: string; }          // exact
export interface Segment { name: string; definition_hash: string; }                          // rule
export interface Prediction { label?: number | null; label_name?: string; probability?: number; probabilities?: number[]; }  // carried
export interface CoverageSet { labels: number[]; label_names?: string[]; marginal_labels?: number[]; }          // guarantee
export interface Bracket { p0: number; p1: number; on?: boolean; }                                             // guarantee
export interface Ood { flag: boolean; percentile?: number; }                                                   // signal
export interface Outcomes { as_of: string; n?: number; verdict?: string; }
export interface Drift { inputs: DriftState; outcomes?: Outcomes | null; }                                     // guarantee
export interface Martingale { stream_id: string; seed?: number; wealth?: number; log10_wealth?: number; resets?: number; }  // exact
export interface Guarantee { state: GuaranteeState; scope: GuaranteeScope; weights_hash?: string; }           // guarantee
export interface RouteTraceEntry { row: number; check: string; value: unknown; fired: boolean; }
export interface Routing {                      // exact
  route: Route; row: number; reason_codes: ReasonCode[]; certificate_reasons: string[]; route_trace?: RouteTraceEntry[];
}

export interface CertificatePayload {
  audit_id: string; timestamp: string; prediction_id?: string; model_id: string;
  mode: Mode; enforced: boolean; domain?: string; unit?: string; latency_ms?: number;
  versions: Versions; policy: Policy; cohort: Cohort; segment: Segment;
  prediction: Prediction; model_reason_codes?: string[];
  coverage_set: CoverageSet; qhat?: number; credibility: number; bracket?: Bracket | null;
  calibration_line?: string; cell_n?: number; ood?: Ood; drift: Drift; martingale?: Martingale;
  guarantee: Guarantee; routing: Routing; criticality?: number | null; auditor_flag?: boolean;
  certificate_text: string;
}

export interface Record { prev_hash: string; hash: string; payload: CertificatePayload; }
export interface Chain { records: Record[]; }

export const FIELD_CLASSES: Record<keyof CertificatePayload, FieldClass>;

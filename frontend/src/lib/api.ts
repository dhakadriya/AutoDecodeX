const BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export interface DecodingStep {
  step_number: number;
  encoding_type: string;
  confidence: number;
  input_text: string;
  output_text: string;
  score: number;
}

export interface DecodeResponse {
  success: boolean;
  final_output: string;
  total_score: number;
  path_description: string;
  is_ctf_flag: boolean;
  steps: DecodingStep[];
  detections?: Detection[]; // Optional since backend doesn't always return it
}

export interface Detection {
  type: string;
  confidence: number;
  encoding_type?: string; // Alias for backward compatibility
}

export interface DetectResponse {
  detections: Detection[];
}

export interface BruteForceResult {
  shift?: number;
  key?: number;
  key_hex?: string;
  decoded: string;
  score: number;
}

export interface BruteForceResponse {
  mode: string;
  results: BruteForceResult[];
}

export async function decodeText(input: string, ctf_mode = false): Promise<DecodeResponse> {
  let confidence_threshold: number | undefined = undefined;
  let max_depth: number | undefined = undefined;

  if (typeof window !== "undefined") {
    const saved = localStorage.getItem("autodecodex_settings");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.confidenceThreshold !== undefined) {
          confidence_threshold = Number(parsed.confidenceThreshold);
        }
        if (parsed.recursionDepth !== undefined) {
          max_depth = Number(parsed.recursionDepth);
        }
      } catch (e) {
        // ignore
      }
    }
  }

  const res = await fetch(`${BASE}/decode`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      input,
      ctf_mode,
      confidence_threshold,
      max_depth
    }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function detectText(input: string): Promise<DetectResponse> {
  const res = await fetch(`${BASE}/detect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function bruteForce(input: string, mode: "caesar" | "xor"): Promise<BruteForceResponse> {
  const res = await fetch(`${BASE}/brute-force`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input, mode }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ── Stego API ──────────────────────────────────────────────────────────────

export interface StegoLSBResult {
  raw_bytes_hex: string;
  ascii_text: string;
  possible_b64: string[];
  bits_used: number;
  channels: string;
  total_bits_extracted: number;
}

export interface StegoEntropy {
  global_entropy: number;
  channel_entropy: { R: number; G: number; B: number };
  lsb_entropy: { R: number; G: number; B: number };
  stego_likelihood: number;
  chi_square_score: number;
  suspicious: boolean;
}

export interface StegoDecodeResult {
  success?: boolean;
  final_output: string;
  total_score: number;
  path_description: string;
  is_ctf_flag: boolean;
  steps?: Array<{
    step_number: number;
    encoding_type: string;
    confidence: number;
    output_text: string;
    score: number;
  }>;
  error?: string;
}

export interface StegoAnalyzeResponse {
  filename: string;
  lsb: StegoLSBResult;
  entropy: StegoEntropy;
  auto_decode: StegoDecodeResult | null;
}

export interface StegoBruteResult {
  bits: number;
  channels: string;
  ascii_text: string;
  possible_b64: string[];
  raw_bytes_hex: string;
  score: number;
  decode_result?: {
    final_output: string;
    path_description: string;
    is_ctf_flag: boolean;
    total_score: number;
  };
}

export interface TextStegoResponse {
  zero_width: {
    found: boolean;
    bit_count?: number;
    bits?: string;
    decoded: string;
    auto_decode?: { final_output: string; is_ctf_flag: boolean };
  };
  whitespace: { found: boolean; bit_count?: number; decoded: string };
  first_letters: { first_letter_each_line: string; first_letter_each_word: string };
  unicode_hidden: Array<{ position: number; char: string; codepoint: string }>;
  invisible_chars_found: number;
}

export async function stegoAnalyze(
  file: File,
  bits = 1,
  channels = "RGB",
  password = "",
  autoDecode = true,
): Promise<StegoAnalyzeResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("bits", String(bits));
  form.append("channels", channels);
  if (password) form.append("password", password);
  form.append("auto_decode_flag", String(autoDecode));
  const res = await fetch(`${BASE}/stego/analyze`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Stego API error: ${res.status}`);
  return res.json();
}

export async function stegoBruteForce(file: File, autoDecode = true): Promise<{ results: StegoBruteResult[] }> {
  const form = new FormData();
  form.append("file", file);
  form.append("auto_decode_flag", String(autoDecode));
  const res = await fetch(`${BASE}/stego/brute-force`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Stego brute-force error: ${res.status}`);
  return res.json();
}

export async function stegoBitPlanes(file: File): Promise<{ planes: Record<string, Record<string, string>> }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/stego/bit-planes`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Bit planes error: ${res.status}`);
  return res.json();
}

export async function stegoPixelDiff(file: File): Promise<{ diff_map: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/stego/pixel-diff`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Pixel diff error: ${res.status}`);
  return res.json();
}

export async function stegoTextAnalyze(text: string): Promise<TextStegoResponse> {
  const res = await fetch(`${BASE}/stego/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`Text stego error: ${res.status}`);
  return res.json();
}

// ── Metadata API ───────────────────────────────────────────────────────────

export interface MetadataFinding {
  field: string;
  section: string;
  raw_value: string;
  length: number;
  entropy: number;
  flags: string[];
  encoding: { type: string; confidence: number } | Record<string, never>;
  decode_result: {
    final_output: string;
    path_description: string;
    total_score: number;
    is_ctf_flag: boolean;
    steps: Array<{ step_number: number; encoding_type: string; confidence: number; output_text: string }>;
  } | null;
  suspicious: boolean;
  suspicious_reasons: string[];
}

export interface MetadataResponse {
  metadata: {
    file_info: Record<string, string | number>;
    exif: Record<string, string>;
    gps: Record<string, string>;
    png_text: Record<string, string>;
    pil_info: Record<string, string>;
  };
  analysis: {
    findings: MetadataFinding[];
    flags_found: string[];
    total_suspicious: number;
    total_fields_scanned: number;
  };
  embedded_files: Array<{
    offset: number;
    offset_hex: string;
    file_type: string;
    signature_hex: string;
    context: string;
  }>;
  summary: {
    flags_found: string[];
    suspicious_fields: number;
    total_fields: number;
    embedded_files_count: number;
    has_exif: boolean;
    has_gps: boolean;
    has_png_text: boolean;
  };
}

export interface FullScanResponse {
  filename: string;
  metadata: MetadataResponse;
  lsb: StegoLSBResult;
  lsb_decode: StegoDecodeResult | null;
  entropy: StegoEntropy;
  all_flags: string[];
  summary: {
    flags_found: string[];
    suspicious_fields: number;
    total_fields: number;
    embedded_files_count: number;
    has_exif: boolean;
    has_gps: boolean;
    has_png_text: boolean;
    lsb_suspicious: boolean;
    total_flags: number;
  };
}

export async function stegoMetadata(file: File): Promise<MetadataResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/stego/metadata`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Metadata API error: ${res.status}`);
  return res.json();
}

export async function stegoFullScan(
  file: File,
  bits = 1,
  channels = "RGB",
  password = "",
): Promise<FullScanResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("bits", String(bits));
  form.append("channels", channels);
  if (password) form.append("password", password);
  const res = await fetch(`${BASE}/stego/full-scan`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Full scan error: ${res.status}`);
  return res.json();
}

export async function fileAnalyze(file: File): Promise<any> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/file/analyze`, { method: "POST", body: form });
  if (!res.ok) {
    let errMsg = `File analysis error: ${res.status}`;
    try {
      const errData = await res.json();
      if (errData && errData.detail && errData.detail.message) {
        errMsg = errData.detail.message;
      } else if (errData && errData.detail) {
        errMsg = typeof errData.detail === "string" ? errData.detail : JSON.stringify(errData.detail);
      }
    } catch (e) {}
    throw new Error(errMsg);
  }
  return res.json();
}


// ── Case Management API ────────────────────────────────────────────────────

export type FindingStatus =
  | "CONFIRMED_ARTIFACT"
  | "SUSPICIOUS_INDICATOR"
  | "NO_INDICATOR_DETECTED"
  | "INCONCLUSIVE";

export type Severity = "informational" | "low" | "medium" | "high" | "critical";

export type ArtifactKind =
  | "original_evidence"
  | "extracted_data"
  | "decoded_content"
  | "derived_artifact";

export interface CaseFinding {
  finding_id: string;
  case_id: string;
  artifact_id: string;
  category: string;
  title: string;
  summary: string;
  status: FindingStatus;
  severity: Severity;
  observed_value?: string | null;
  expected_value?: string | null;
  evidence_details?: Record<string, unknown> | null;
  detection_method: string;
  rule_id?: string | null;
  detector_version?: string | null;
  explanation: string;
  limitations: string;
  recommended_next_step?: string | null;
  parent_finding_ids: string[];
  supporting_offsets?: number[] | null;
  input_artifact_hash?: string | null;
  output_artifact_hash?: string | null;
  timestamp_utc: string;
}

export interface CaseArtifact {
  artifact_id: string;
  case_id: string;
  kind: ArtifactKind;
  filename: string;
  size_bytes: number;
  sha256: string;
  md5: string;
  mime_type?: string | null;
  detected_format?: string | null;
  parent_artifact_id?: string | null;
  parent_operation?: string | null;
  recursion_depth: number;
  timestamp_utc: string;
}

export interface TransformationStep {
  step_id: string;
  case_id: string;
  source_artifact_id: string;
  source_sha256: string;
  decoder_name: string;
  input_size_bytes: number;
  output_size_bytes: number;
  output_artifact_id?: string | null;
  output_sha256?: string | null;
  recursion_depth: number;
  duration_ms: number;
  status: string;
  warnings: string[];
  errors: string[];
}

export interface CorrelationResult {
  correlation_id: string;
  case_id: string;
  rule_id: string;
  rule_description: string;
  triggered_by_finding_ids: string[];
  status: FindingStatus;
  severity: Severity;
  match_reason: string;
  supporting_evidence: string;
  what_this_does_not_prove: string;
  next_step: string;
  timestamp_utc: string;
}

export interface ModuleResult {
  module_name: string;
  artifact_id: string;
  status: string;
  duration_ms: number;
  findings: CaseFinding[];
  warnings: string[];
  errors: string[];
}

export interface CaseData {
  case_id: string;
  created_at_utc: string;
  completed_at_utc?: string | null;
  original_filename: string;
  file_size_bytes: number;
  detected_format?: string | null;
  mime_type?: string | null;
  sha256: string;
  md5: string;
  status: string;
  enabled_modules: string[];
  completed_modules: string[];
  artifacts: CaseArtifact[];
  findings: CaseFinding[];
  correlations: CorrelationResult[];
  transformation_graph: TransformationStep[];
  module_results: ModuleResult[];
  summary?: string | null;
  errors: string[];
  warnings: string[];
  app_version: string;
  engine_version: string;
}

export interface CaseSummary {
  case_id: string;
  created_at_utc: string;
  completed_at_utc?: string | null;
  original_filename: string;
  file_size_bytes: number;
  detected_format?: string | null;
  sha256: string;
  status: string;
  finding_count: number;
  correlation_count: number;
  modules_completed: string[];
}

export interface CaseListResponse {
  cases: CaseSummary[];
  total: number;
  limit: number;
  offset: number;
  storage_note: string;
}

export async function createCase(file: File): Promise<CaseData> {
  const form = new FormData();
  form.append("file", file);
  form.append("run_stego", "true");
  const res = await fetch(`${BASE}/cases`, { method: "POST", body: form });
  if (!res.ok) {
    let msg = `Case creation failed: ${res.status}`;
    try {
      const err = await res.json();
      if (err?.detail?.message) msg = err.detail.message;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export async function getCases(limit = 20, offset = 0): Promise<CaseListResponse> {
  const res = await fetch(`${BASE}/cases?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error(`Failed to list cases: ${res.status}`);
  return res.json();
}

export async function getCase(caseId: string): Promise<CaseData> {
  const res = await fetch(`${BASE}/cases/${caseId}`);
  if (!res.ok) throw new Error(`Case not found: ${res.status}`);
  return res.json();
}

export async function deleteCase(caseId: string): Promise<void> {
  const res = await fetch(`${BASE}/cases/${caseId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
}

export function getJsonReportUrl(caseId: string): string {
  return `${BASE}/cases/${caseId}/report/json`;
}

export function getPdfReportUrl(caseId: string): string {
  return `${BASE}/cases/${caseId}/report/pdf`;
}

export async function runBenchmark(
  split: "dev" | "eval" | "all" = "eval",
  entropyThreshold = 0.5,
  lsbThreshold = 0.5,
): Promise<Record<string, unknown>> {
  const params = new URLSearchParams({
    split,
    entropy_threshold: String(entropyThreshold),
    lsb_threshold: String(lsbThreshold),
  });
  const res = await fetch(`${BASE}/benchmark/run?${params}`, { method: "POST" });
  if (!res.ok) throw new Error(`Benchmark failed: ${res.status}`);
  return res.json();
}

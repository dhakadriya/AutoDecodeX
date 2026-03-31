const BASE = "/api";

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
}

export interface Detection {
  type: string;
  confidence: number;
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
  const res = await fetch(`${BASE}/decode`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input, ctf_mode }),
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

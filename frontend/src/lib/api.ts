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

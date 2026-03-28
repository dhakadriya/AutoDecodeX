# AutoDecodeX

An intelligent, AI-assisted encoding detection and decoding tool for CTF players and cybersecurity students.

> CyberChef + AI + Automation + Hacker UI

---

## Architecture

```
autodecodex/
├── backend/
│   ├── detectors/      # Heuristic encoding detectors (regex, entropy, charset)
│   ├── decoders/       # Decoder implementations (Base64, Hex, ROT13, XOR, etc.)
│   ├── scoring/        # Readability/confidence scoring engine
│   ├── engine/         # BFS orchestrator — multi-layer decoding
│   ├── api/            # FastAPI routes
│   └── main.py         # App entry point
├── frontend/
│   ├── src/app/        # Next.js app router
│   ├── src/components/ # UI components
│   └── src/lib/        # API client
└── autodecodex.py      # CLI entry point
```

## Detection Logic

Each detector returns a confidence score (0–1) using:
- **Regex patterns** — charset validation (Base64, Hex, Binary, Morse, URL)
- **Entropy analysis** — Shannon entropy to distinguish encoded vs plaintext
- **Structural heuristics** — length divisibility, padding, character distribution

Supported encodings: `Base64`, `Base32`, `Base85`, `Hex`, `Binary`, `Decimal ASCII`, `ROT13`, `Caesar`, `Morse`, `URL Encoding`

Brute force modules: `Caesar (all 26 shifts)`, `Single-byte XOR (0–255)`

## How to Run Locally

### Backend

```bash
cd backend
pip install -r requirements.txt
# From project root:
uvicorn backend.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:3000

### CLI

```bash
# Basic decode
python autodecodex.py "SGVsbG8gV29ybGQ="

# CTF mode
python autodecodex.py "ZmxhZ3t0ZXN0fQ==" --ctf

# Brute force Caesar
python autodecodex.py "Uryyb Jbeyq" --brute-force caesar

# Brute force XOR
python autodecodex.py "1b1b1b" --brute-force xor

# Detection only
python autodecodex.py "48656c6c6f" --detect-only
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/decode` | Full multi-layer decode |
| POST | `/api/detect` | Detection only |
| POST | `/api/brute-force` | Caesar or XOR brute force |
| GET  | `/api/health` | Health check |

### Example Request

```json
POST /api/decode
{
  "input": "SGVsbG8gV29ybGQ=",
  "ctf_mode": false
}
```

### Example Response

```json
{
  "success": true,
  "final_output": "Hello World",
  "total_score": 0.87,
  "path_description": "BASE64 (92%) → Plaintext",
  "is_ctf_flag": false,
  "steps": [
    {
      "step_number": 1,
      "encoding_type": "base64",
      "confidence": 0.92,
      "input_text": "SGVsbG8gV29ybGQ=",
      "output_text": "Hello World",
      "score": 0.87
    }
  ]
}
```

## Test Cases

| Input | Expected Output |
|-------|----------------|
| `SGVsbG8gV29ybGQ=` | `Hello World` (Base64) |
| `48656c6c6f` | `Hello` (Hex) |
| `Uryyb Jbeyq` | `Hello World` (ROT13) |
| `01001000 01100101 01101100 01101100 01101111` | `Hello` (Binary) |
| `.... . .-.. .-.. ---` | `HELLO` (Morse) |
| `ZmxhZ3t0ZXN0X2ZsYWd9` | `flag{test_flag}` (Base64 → CTF flag) |
| `NTM2NTZjNmM2ZjIwNTc2ZjcyNmM2NA==` | `Hello World` (Base64 → Hex) |

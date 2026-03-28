# AutoDecodeX Implementation Plan

AutoDecodeX is an advanced AI-assisted encoding and cipher detection & decoding tool designed for CTF players and cybersecurity students. It automatically detects and decodes multi-layer encodings with a rich, explainable pipeline and visualizes the attack path step-by-step.

## User Review Required

> [!IMPORTANT]
> Please review the chosen dependencies and the proposed module structure below. 
> - **Frontend**: Next.js (React), TailwindCSS, Framer Motion, and `lucide-react` for icons.
> - **Backend**: Python 3, FastAPI, Uvicorn, and optionally `click` for the CLI.
> - **CLI Approach**: Do you prefer the CLI to be a standalone script that imports the engine directly, or an API client that sends requests to the FastAPI backend? The plan assumes a standalone script using the shared engine.

## Action Plan overview

The project will be split into two main directory trees: `frontend/` and `backend/`.

### 1. Backend Architecture (Python + FastAPI)
The backend will be modular to support easy addition of new ciphers.

- **`backend/`**
  - **`engine/`**: Core orchestrator. Given an input string, intelligently tries decoders (guided by detectors/scoring) and branches into multi-path exploration. Implements loop mitigation, maximum depth limits, and Attack Path calculation showing step-by-step paths.
  - **`detectors/`**: Heuristics to guess encoding types fast. (Regexes for Base64, Hex, URL encoding, Morse; Entropy/Charset stats).
  - **`decoders/`**: Implementation of specific decoders:
    - Base64, Base32, Base85
    - Hex, Binary, Decimal ASCII
    - ROT13, Caesar cipher (Brute force module)
    - Morse Code
    - URL Encoding
    - Single-byte XOR brute force
  - **`scoring/`**: Analyzes the "readability" of a string. Returns a confidence % based on English character frequency, printable characters proportion, and common CTF flag formats (e.g. `flag{...}`).
  - **`api/`**: FastAPI routes (`/api/decode`, etc.) to interface with the frontend.
  - **`cli/`**: A CLI entrypoint (`autodecodex.py`).

### 2. Frontend Architecture (Next.js + TailwindCSS + Framer Motion)
A robust and beautiful hacker/cyberpunk themed SPA.

- **`frontend/`**
  - **Pages**: Main decode dashboard (split into Input, Pipeline Graph, Output).
  - **Components**:
    - **CyberInput**: A glowing animated textarea with neon accents for input holding.
    - **PipelineVisualizer**: A dynamic flow diagram representing the multi-level decoding steps with confidence bars and animations (using Framer Motion).
    - **TerminalOutput**: A simulated terminal window showing the final readable output or best brute-force candidates.
    - **SettingsPanel**: Toggle for CTF Mode, strict brute force checks, etc.
  - **Styling**: Extensive use of CSS Custom Properties for neon colors (green, blue, purple) and dark gradients to achieve the premium CyberChef+AI aesthetic.

### 3. Engine Loop & Smart Exploration
- **Input phase**: Accept string, analyze charset.
- **Queue phase**: Maintain a queue of `(current_string, path_history, score)`.
- **Exploration**: 
  - For each string, run `detectors`.
  - Try decoding with the most likely top 3 tools.
  - For each valid returned string, check `scoring`.
  - If score > threshold (e.g., 90%) or matches flag regex, halt or add to `best_results`.
  - Recurse up to max depth (e.g., 10 layers).

## Proposed Changes

### Setup and Scaffolding
- Initializing Next.js app in `frontend/`
- Setting up Python virtual environment and dependencies in `backend/`

### Backend Modules

#### [NEW] backend/requirements.txt
List of python dependencies: `fastapi`, `uvicorn`, `pydantic`.

#### [NEW] backend/main.py
FastAPI application initialization and routing.

#### [NEW] backend/scoring/scorer.py
Logic for evaluating text readability and probability of being plaintext or a flag.

#### [NEW] backend/decoders/base_decoder.py and specific decoders
Implementations for Base64, Base32, Hex, ROT13, XOR, etc., with error handling.

#### [NEW] backend/engine/orchestrator.py
The solver engine applying BFS/DFS across possible decodings.

#### [NEW] autodecodex (CLI script at root)
CLI entrypoint to use the backend engine directly.

### Frontend Modules

#### [NEW] frontend/package.json
Tailwind, Next.js, Framer Motion and dependencies.

#### [NEW] frontend/src/app/page.tsx
Main application layout.

#### [NEW] frontend/src/components/CyberInput.tsx
Text input with smooth animations and neon focus states.

#### [NEW] frontend/src/components/DecodingPipeline.tsx
Animated step-by-step visualization of the decoding process using Framer Motion.

#### [NEW] frontend/src/components/TerminalOutput.tsx
A terminal-like view for displaying the final decoded text or brute-force candidates.

## Verification Plan

### Automated Tests
- Simple unit scripts in backend to assert `orchestrator.py` can solve stacked encodings (e.g., Base64(Hex(ROT13("flag{test_flag}")))).

### Manual Verification
- Start FastAPI server and Next.js frontend.
- Provide encoded strings from common CTF challenges.
- Verify that the pipeline animation runs smoothly and displays confidence scores correctly.
- Verify CLI works by executing `python autodecodex "encoded_string"`.

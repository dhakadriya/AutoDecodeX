# AutoDecodeX

AutoDecodeX is a digital forensics and steganalysis tool built for CTF players and security students. You upload a file or paste encoded text and the app automatically detects the encoding, decodes it layer by layer, and scans images for hidden data — all from one interface.

---

## What it does

- **Decodes encoded text** — Base64, Hex, Binary, ROT13, Morse, URL, Gzip, and more, including multi-layer chains
- **Detects CTF flags** automatically during decoding
- **Analyzes images for hidden data** — LSB steganography, chi-square analysis, entropy maps, bit-plane viewer, pixel difference maps
- **Extracts metadata** — EXIF, PNG text chunks, GPS data, embedded file signatures
- **Creates investigation cases** — every uploaded file gets a unique case with SHA-256/MD5 hashes, structured findings, and a downloadable forensic report (JSON or PDF)

---

## Tech stack

- **Frontend:** Next.js 14, TypeScript, Tailwind CSS
- **Backend:** FastAPI, Python 3.11+, Pillow, NumPy

---

## Running locally

**Requirements:** Python 3.11+, Node.js 18+

```bash
# 1. Clone the repo
git clone https://github.com/your-username/AutoDecodeX.git
cd AutoDecodeX

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Install frontend dependencies
cd frontend && npm install && cd ..

# 4. Start the backend (terminal 1)
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 5. Start the frontend (terminal 2)
cd frontend && npm run dev
```

Open **http://localhost:3000** in your browser.

The API docs are available at **http://localhost:8000/docs**.

---

## Environment variables

Create `frontend/.env.local` for the frontend:

```
BACKEND_URL=http://localhost:8000
```

For production, set these in your hosting dashboard:

| Variable | Description |
|---|---|
| `BACKEND_URL` | URL of your FastAPI backend (server-side) |
| `NEXT_PUBLIC_API_URL` | URL of your FastAPI backend (browser-side, if not using rewrites) |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins |

---

## Deploying

**Frontend → Vercel**

1. Push the repo to GitHub
2. Go to [vercel.com](https://vercel.com) → New Project → import the repo
3. Set **Root Directory** to `frontend`
4. Add environment variables (`BACKEND_URL` pointing to your backend)
5. Deploy

**Backend → Render**

1. Go to [render.com](https://render.com) → New Web Service → import the repo
2. Set **Build Command** to `pip install -r backend/requirements.txt`
3. Set **Start Command** to `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variable: `PYTHONPATH` = `/opt/render/project/src`
5. Add `ALLOWED_ORIGINS` = your Vercel frontend URL
6. Deploy — copy the service URL, then paste it as `BACKEND_URL` in Vercel

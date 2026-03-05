# Real-time Speech Transcription (Streamlit + Next.js)

This repository contains two app frontends backed by Oracle AI Speech:

- **Streamlit app** (`app.py`) for quick local transcription UX
- **Next.js app** (`frontend/`) for web-based recording/transcript UI

## Project scope

This project is designed for **local development and learning**. It is not intended as a production deployment template.

## Prerequisites

- Python 3.12+
- Node.js 20.9+
- OCI account and valid credentials

## Environment

Create a `.env` file in the repository root:

```env
OCI_USER=<your-user-ocid>
OCI_KEY_FILE=<path-to-api-key-file>
OCI_FINGERPRINT=<api-key-fingerprint>
OCI_TENANCY=<your-tenancy-ocid>
OCI_REGION=<your-region>
OCI_COMPARTMENT_ID=<your-compartment-id>
```

Optional frontend override for the Next.js websocket client:

```env
NEXT_PUBLIC_PYTHON_WS_URL=ws://127.0.0.1:5000
```

## Install

Python dependencies:

```bash
uv sync
```

Node dependencies:

```bash
cd frontend
npm install
```

## Quick start

### Option A: Streamlit only

```bash
uv run streamlit run app.py
```

Open `http://localhost:8501`.

### Option B: Next.js + websocket backend

Terminal 1:

```bash
uv run python server.py
```

Terminal 2:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

## Run

### Streamlit app

```bash
uv run streamlit run app.py
```

### Next.js app + Python websocket backend

Terminal 1:

```bash
uv run python server.py
```

Backend utility endpoints:

- `http://localhost:5000/health`
- `http://localhost:5000/ready`

Terminal 2:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

## Docker (Streamlit app)

Build image:

```bash
docker build -t oracle-ai-speech:dev .
```

Run container:

```bash
docker run --rm -p 8501:8501 \
  --env-file .env \
  -e OCI_KEY_FILE=/home/appuser/.oci/oci_api_key.pem \
  -v "$HOME/.oci:/home/appuser/.oci:ro" \
  oracle-ai-speech:dev
```

Then open `http://localhost:8501`.

## Troubleshooting

- **No transcript appears**
  - Ensure backend is running (`uv run python server.py`) and frontend websocket URL points to `ws://127.0.0.1:5000`.
- **OCI auth/config errors**
  - Verify all OCI vars in `.env` and confirm key file path is valid and readable.
- **Microphone device issues**
  - Browser must have mic permission; re-check selected input device in UI.
- **Docker cannot authenticate OCI**
  - Mount `~/.oci` and set `OCI_KEY_FILE` to container path (`/home/appuser/.oci/oci_api_key.pem`).

## Project structure

```text
app.py
audio_handler.py
config.py
speech_service.py
server.py
frontend/
```

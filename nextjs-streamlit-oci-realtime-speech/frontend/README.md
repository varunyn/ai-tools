# Frontend (Next.js 16)

This directory contains the Next.js frontend for realtime microphone streaming and live transcription display.

## Prerequisites

- Node.js 20.9+
- Python backend websocket server running from project root (`uv run python server.py`)

## Install

```bash
npm install
```

## Run

```bash
npm run dev
```

Open `http://localhost:3000`.

## Environment

Set in root `.env` or `frontend/.env.local`:

```env
NEXT_PUBLIC_PYTHON_WS_URL=ws://127.0.0.1:5000
PYTHON_WS_URL=ws://127.0.0.1:5000
PYTHON_HTTP_BASE=http://127.0.0.1:5000
```

## Key paths

- `pages/index.js` — main recording/transcript UI
- `pages/api/transcribe.js` — optional websocket proxy route
- `public/audio-processor.js` — AudioWorklet processor for PCM conversion
- `stores/transcriptionStore.js` — Zustand session/UI store

## Websocket message contract (from backend)

- `type: "session_started"` with `sessionId`
- `type: "transcription"`, `status: "success"`, `transcript`, `is_final`
- `type: "session_stopped"`
- `type: "error"` with `message`

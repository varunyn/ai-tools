#!/bin/bash

# Run from backend root so app imports resolve correctly (works when called from repo root or backend)
cd "$(dirname "$0")/.."

# Run the FastAPI app using uv
echo "Starting FastAPI server on http://localhost:3001"
uv run uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload

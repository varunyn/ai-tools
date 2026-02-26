#!/usr/bin/env bash
# Test backend /v1/chat/completions directly with curl.
# Usage: ./scripts/test_chat_curl.sh [BASE_URL]
# Default BASE_URL=http://localhost:3001 (use host.docker.internal or your backend URL if needed)

set -e
BASE_URL="${1:-http://localhost:3001}"

echo "=== Testing backend at $BASE_URL ==="
echo ""

# 1) Non-streaming: should return full content in one JSON body
echo "--- 1) Non-streaming (stream=false) ---"
RESP=$(curl -s -X POST "$BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "xai.grok-4-fast-non-reasoning",
    "messages": [{"role": "user", "content": "What is 2 + 2? Reply with just the number."}],
    "stream": false,
    "max_tokens": 100
  }')

if echo "$RESP" | grep -q '"error"'; then
  echo "Error response: $RESP"
else
  CONTENT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); m=d.get('choices',[{}])[0].get('message',{}); c=m.get('content',''); print('content length:', len(c)); print('content:', repr(c[:300]))" 2>/dev/null || echo "$RESP" | head -c 500)
  echo "$CONTENT"
fi
echo ""

# 2) Tool-call prompt (non-streaming) - backend should forward tool_calls
echo "--- 2) Non-streaming, tool-call prompt ---"
RESP2=$(curl -s -X POST "$BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "xai.grok-4-fast-non-reasoning",
    "messages": [{"role": "user", "content": "Call a function named \"get_namespace\" with no args."}],
    "stream": false,
    "max_tokens": 500
  }')

if echo "$RESP2" | grep -q '"error"'; then
  echo "Error response: $RESP2"
else
  CONTENT2=$(echo "$RESP2" | python3 -c "import sys,json; d=json.load(sys.stdin); m=d.get('choices',[{}])[0].get('message',{}); c=m.get('content',''); print('content length:', len(c)); print('content:', repr(c[:400]))" 2>/dev/null || echo "$RESP2" | head -c 600)
  echo "$CONTENT2"
fi
echo ""

# 3) Streaming: one request, show first few SSE lines
echo "--- 3) Streaming (stream=true), first 5 data lines ---"
curl -s -N -X POST "$BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "xai.grok-4-fast-non-reasoning",
    "messages": [{"role": "user", "content": "Say hello in one word."}],
    "stream": true,
    "max_tokens": 50
  }' | head -n 5

echo ""
echo "=== Done ==="

#!/bin/bash

set -euo pipefail
BASE_URL="${1:-http://localhost:3001}"

cat <<'MSG'
==========================================
Generic tool forwarding check
==========================================
This script demonstrates how /v1/chat/completions handles tool_calls with and
without streaming. It does NOT execute calculator functions; it only verifies
that the backend forwards the tool metadata to the caller.
==========================================
MSG

non_stream_payload='{
  "model": "xai.grok-4-fast-non-reasoning",
  "messages": [
    {"role": "user", "content": "Call calculate with operation add"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "calculate",
        "description": "Dummy calculator (client executed)",
        "parameters": {
          "type": "object",
          "properties": {
            "operation": {"type": "string", "enum": ["add", "subtract"], "description": "Operation"},
            "a": {"type": "number"},
            "b": {"type": "number"}
          },
          "required": ["operation", "a", "b"]
        }
      }
    }
  ],
  "stream": false,
  "max_tokens": 200,
  "temperature": 0
}'

resp=$(curl -s -X POST "$BASE_URL/v1/chat/completions" -H "Content-Type: application/json" -d "$non_stream_payload")
finish_reason=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0].get('finish_reason',''))" 2>/dev/null || echo "")
echo "Non-stream response:"
echo "$resp" | python3 -m json.tool 2>/dev/null || echo "$resp"
[[ "$finish_reason" == "tool_calls" ]] && echo "✓ tool_calls forwarded (non-stream)." || echo "⚠️ Unexpected finish_reason: $finish_reason"

echo ""
echo "Streaming response (first 6 lines):"
stream_payload='{
  "model": "xai.grok-4-fast-non-reasoning",
  "messages": [
    {"role": "user", "content": "Call get_namespace function"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_namespace",
        "parameters": {"type": "object", "properties": {}}
      }
    }
  ],
  "stream": true,
  "max_tokens": 200
}'

curl -s -N -X POST "$BASE_URL/v1/chat/completions" -H "Content-Type: application/json" -d "$stream_payload" | head -n 6

#!/bin/bash

set -euo pipefail
BASE_URL="${1:-http://localhost:3001}"

cat <<'MSG'
==========================================
RAG forwarding check
==========================================
This script sends a chat completion request that includes the
search_knowledge_base tool definition. The backend should respond with
finish_reason="tool_calls" and echo the tool call back to the client.

Actual tool execution must happen in your client (Open WebUI MCP, custom agent,
etc.). Use this script only to confirm the backend behaves like an OpenAI proxy.
==========================================
MSG

payload='{
  "model": "xai.grok-4-fast-reasoning",
  "messages": [
    {"role": "user", "content": "Search the resume knowledge base for Satish"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "search_knowledge_base",
        "description": "Search the Oracle 23ai knowledge base",
        "parameters": {
          "type": "object",
          "properties": {
            "query": {"type": "string", "description": "Natural language query"},
            "top_k": {"type": "integer", "description": "Number of rows", "default": 5},
            "table_name": {"type": "string", "description": "Oracle table", "default": "ORACLE_WEB_EMBEDDINGS"}
          },
          "required": ["query"]
        }
      }
    }
  ],
  "stream": false
}'

resp=$(curl -s -X POST "$BASE_URL/v1/chat/completions" -H "Content-Type: application/json" -d "$payload")

echo "Raw response:"
echo "$resp" | python3 -m json.tool 2>/dev/null || echo "$resp"

finish_reason=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0].get('finish_reason',''))" 2>/dev/null || echo "")

if [[ "$finish_reason" == "tool_calls" ]]; then
  echo "✅ Backend forwarded tool_calls as expected."
else
  echo "⚠️  Unexpected finish_reason: $finish_reason"
fi

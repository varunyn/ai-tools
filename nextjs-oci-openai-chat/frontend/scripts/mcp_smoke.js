#!/usr/bin/env node
function log(msg) {
  console.log(`[mcp_smoke] ${msg}`)
}

const {
  MCP_ORACLE_RAG_URL,
  MCP_CALCULATOR_URL,
  MCP_ORACLE_RAG_AUTH_TOKEN,
  MCP_CALCULATOR_AUTH_TOKEN
} = process.env

async function tryList(url, authToken) {
  const clientMod = await import('@modelcontextprotocol/sdk/client/index.js').catch(() => null)
  const transportMod = await import('@modelcontextprotocol/sdk/client/streamableHttp.js').catch(() => null)
  const Client = clientMod && clientMod.Client
  const StreamableHTTPClientTransport = transportMod && transportMod.StreamableHTTPClientTransport
  if (!Client || !StreamableHTTPClientTransport) {
    log('MCP SDK not installed. Run: cd frontend && pnpm add @modelcontextprotocol/sdk zod @cfworker/json-schema')
    return
  }
  const transport = new StreamableHTTPClientTransport(new URL(url), authToken ? { headers: { Authorization: `Bearer ${authToken}` } } : undefined)
  const client = new Client({ name: 'mcp-smoke', version: '0.0.0' })
  try {
    await client.connect(transport)
    const tools = await client.listTools()
    const count = Array.isArray(tools?.tools) ? tools.tools.length : 0
    log(`Connected to ${url} — tools: ${count}`)
  } catch (err) {
    log(`Tried ${url} but got: ${(err && err.message) || String(err)}`)
  } finally {
    try { typeof client.close === 'function' && (await client.close()) } catch {}
    try { typeof transport.close === 'function' && (await transport.close()) } catch {}
  }
}

;(async () => {
  if (!MCP_ORACLE_RAG_URL && !MCP_CALCULATOR_URL) {
    log('No MCP URLs configured. Set MCP_ORACLE_RAG_URL or MCP_CALCULATOR_URL in frontend/.env.local')
    log('Example: MCP_ORACLE_RAG_URL=http://localhost:3021/mcp')
    process.exit(0)
  }
  if (MCP_ORACLE_RAG_URL) {
    await tryList(MCP_ORACLE_RAG_URL, MCP_ORACLE_RAG_AUTH_TOKEN)
  }
  if (MCP_CALCULATOR_URL) {
    await tryList(MCP_CALCULATOR_URL, MCP_CALCULATOR_AUTH_TOKEN)
  }
  log('Smoke complete.')
})()

import http from 'http'

export async function startMockRagMcp(port = 3021): Promise<{ url: string; close: () => Promise<void> }> {
  const server = http.createServer(async (req, res) => {
    if (req.method !== 'POST' || !req.url || !req.url.startsWith('/mcp')) {
      res.statusCode = 404
      return res.end('Not Found')
    }

    const chunks: Buffer[] = []
    for await (const chunk of req) chunks.push(chunk as Buffer)
    const bodyStr = Buffer.concat(chunks).toString('utf8')

    let rpc: { id?: unknown; method?: string; params?: unknown } | null = null
    try {
      rpc = JSON.parse(bodyStr || '{}') as { id?: unknown; method?: string; params?: unknown }
    } catch {
      res.writeHead(400, { 'Content-Type': 'application/json' })
      return res.end(JSON.stringify({ error: 'invalid json' }))
    }

    const { id, method, params } = rpc || {}

    if (method === 'initialize') {
      res.writeHead(200, { 'Content-Type': 'application/json' })
      return res.end(
        JSON.stringify({
          jsonrpc: '2.0',
          id,
          result: {
            protocolVersion: '2024-11-05',
            capabilities: { tools: {} },
            serverInfo: { name: 'mock-mcp-rag', version: '0.1.0' }
          }
        })
      )
    }

    if (method === 'tools/list') {
      res.writeHead(200, { 'Content-Type': 'application/json' })
      return res.end(
        JSON.stringify({
          jsonrpc: '2.0',
          id,
          result: {
            tools: [
              {
                name: 'search_knowledge_base',
                description: 'Return deterministic snippet for testing',
                inputSchema: {
                  type: 'object',
                  properties: {
                    query: { type: 'string' },
                    top_k: { type: 'number' },
                    table_name: { type: 'string' }
                  },
                  required: ['query']
                }
              }
            ]
          }
        })
      )
    }

    if (method === 'tools/call') {
      const callParams = params as { name?: string; arguments?: Record<string, unknown> } | undefined
      const name = callParams?.name
      if (name !== 'search_knowledge_base') {
        res.writeHead(200, { 'Content-Type': 'application/json' })
        return res.end(
          JSON.stringify({ jsonrpc: '2.0', id, result: { content: [{ type: 'text', text: '[]' }], structuredContent: { results: [] } } })
        )
      }
      const query = String((callParams?.arguments as { query?: string } | undefined)?.query ?? '')
      const results = [{ id: 'kb-1', score: 0.99, text: `RAG snippet for: ${query}` }]
      res.writeHead(200, { 'Content-Type': 'application/json' })
      return res.end(
        JSON.stringify({
          jsonrpc: '2.0',
          id,
          result: { content: [{ type: 'text', text: JSON.stringify(results) }], structuredContent: { results } }
        })
      )
    }

    if (id === undefined) {
      res.statusCode = 204
      return res.end()
    }

    res.writeHead(200, { 'Content-Type': 'application/json' })
    return res.end(JSON.stringify({ jsonrpc: '2.0', id, error: { code: -32601, message: 'Method not found' } }))
  })

  await new Promise<void>(resolve => server.listen(port, resolve))

  return {
    url: `http://localhost:${port}/mcp`,
    close: () => new Promise(resolve => server.close(() => resolve()))
  }
}

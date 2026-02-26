import http from 'http'

function sendJson(res: http.ServerResponse, status: number, obj: unknown) {
  const buf = Buffer.from(JSON.stringify(obj))
  res.writeHead(status, { 'Content-Type': 'application/json', 'Content-Length': buf.length })
  res.end(buf)
}

export async function startMockCalculatorMcp(port = 3020): Promise<{ url: string; close: () => Promise<void> }> {
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
      return sendJson(res, 400, { error: 'invalid json' })
    }

    const { id, method, params } = rpc || {}

    if (method === 'initialize') {
      return sendJson(res, 200, {
        jsonrpc: '2.0',
        id,
        result: {
          protocolVersion: '2024-11-05',
          capabilities: { tools: {} },
          serverInfo: { name: 'mock-mcp-calculator', version: '0.1.0' }
        }
      })
    }

    if (method === 'tools/list') {
      return sendJson(res, 200, {
        jsonrpc: '2.0',
        id,
        result: {
          tools: [
            {
              name: 'calculate',
              description: 'Evaluate a simple math expression',
              inputSchema: {
                type: 'object',
                properties: { expression: { type: 'string' } },
                required: ['expression']
              }
            }
          ]
        }
      })
    }

    if (method === 'tools/call') {
      const callParams = params as { name?: string; arguments?: Record<string, unknown> } | undefined
      const name = callParams?.name
      const expression = String(name === 'calculate' ? (callParams?.arguments as { expression?: string } | undefined)?.expression ?? '' : '')
      const result = expression === '1+2' ? 3 : NaN
      return sendJson(res, 200, {
        jsonrpc: '2.0',
        id,
        result: {
          content: [{ type: 'text', text: String(result) }],
          structuredContent: { result }
        }
      })
    }

    if (id === undefined) {
      res.statusCode = 204
      return res.end()
    }

    return sendJson(res, 200, {
      jsonrpc: '2.0',
      id,
      error: { code: -32601, message: 'Method not found' }
    })
  })

  await new Promise<void>(resolve => server.listen(port, resolve))

  return {
    url: `http://localhost:${port}/mcp`,
    close: () => new Promise(resolve => server.close(() => resolve()))
  }
}

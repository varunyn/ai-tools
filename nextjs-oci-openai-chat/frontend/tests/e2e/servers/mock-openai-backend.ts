import http from 'http'

interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'tool'
  content?: string | Array<{ type: string; text?: string }>
  tool_call_id?: string
  name?: string
}

function hasToolMessage(messages: ChatMessage[] = []): boolean {
  return messages.some(m => m.role === 'tool')
}

function json(res: http.ServerResponse, status: number, body: unknown) {
  const data = Buffer.from(JSON.stringify(body))
  res.writeHead(status, {
    'Content-Type': 'application/json',
    'Content-Length': data.length
  })
  res.end(data)
}

function sseWrite(res: http.ServerResponse, payload: unknown) {
  res.write(`data: ${JSON.stringify(payload)}\n\n`)
}

export async function startMockOpenAIBackendServer(port = 4545): Promise<{ url: string; close: () => Promise<void> }> {
  const server = http.createServer(async (req, res) => {
    try {
      const { method, url } = req
      if (method === 'GET' && (url === '/api/chat/models' || url === '/v1/models')) {
        return json(res, 200, {
          models: [
            { id: 'mock-model', name: 'Mock Model', chef: 'Mock', chefSlug: 'mock', providers: ['oci'] }
          ]
        })
      }
      if (method === 'POST' && url === '/v1/chat/completions') {
        const chunks: Buffer[] = []
        for await (const chunk of req) {
          chunks.push(chunk as Buffer)
        }
        const bodyStr = Buffer.concat(chunks).toString('utf8')
        let body: Record<string, unknown> = {}
        try {
          body = JSON.parse(bodyStr || '{}') as Record<string, unknown>
        } catch {
          body = {}
        }

        const messages: ChatMessage[] = Array.isArray(body?.messages) ? body.messages : []

        if (body?.stream === true) {
                  const created = Math.floor(Date.now() / 1000)
                  const model = body?.model ?? 'mock-model'
                  const id = hasToolMessage(messages) ? 'chatcmpl-mock-2-sse' : 'chatcmpl-mock-1-sse'
        
                  res.writeHead(200, {
                    'Content-Type': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                    Connection: 'keep-alive'
                  })
                  ;(res as http.ServerResponse & { flushHeaders?: () => void }).flushHeaders?.()
        
                  if (!hasToolMessage(messages)) {
                    const toolCallId = 'toolu_12345'
                    sseWrite(res, {
                      id,
                      object: 'chat.completion.chunk',
                      created,
                      model,
                      choices: [
                        {
                          index: 0,
                          delta: {
                            role: 'assistant',
                            tool_calls: [
                              {
                                index: 0,
                                id: toolCallId,
                                type: 'function',
                                function: {
                                  name: 'calculate',
                                  arguments: JSON.stringify({ expression: '1+2' })
                                }
                              }
                            ]
                          },
                          finish_reason: null
                        }
                      ]
                    })
        
                    sseWrite(res, {
                      id,
                      object: 'chat.completion.chunk',
                      created,
                      model,
                      choices: [
                        {
                          index: 0,
                          delta: {},
                          finish_reason: 'tool_calls'
                        }
                      ]
                    })
        
                    res.write('data: [DONE]\n\n')
                    return res.end()
                  }
        
                  sseWrite(res, {
                    id,
                    object: 'chat.completion.chunk',
                    created,
                    model,
                    choices: [
                      {
                        index: 0,
                        delta: { role: 'assistant' },
                        finish_reason: null
                      }
                    ]
                  })
        
                  sseWrite(res, {
                    id,
                    object: 'chat.completion.chunk',
                    created,
                    model,
                    choices: [
                      {
                        index: 0,
                        delta: { content: 'The result is 3.' },
                        finish_reason: null
                      }
                    ]
                  })
        
                  sseWrite(res, {
                    id,
                    object: 'chat.completion.chunk',
                    created,
                    model,
                    choices: [
                      {
                        index: 0,
                        delta: {},
                        finish_reason: 'stop'
                      }
                    ]
                  })
        
                  res.write('data: [DONE]\n\n')
                  return res.end()
                }

        if (!hasToolMessage(messages)) {
          const toolCallId = 'toolu_12345'
          return json(res, 200, {
            id: 'chatcmpl-mock-1',
            object: 'chat.completion',
            created: Math.floor(Date.now() / 1000),
            model: body?.model ?? 'mock-model',
            choices: [
              {
                index: 0,
                message: {
                  role: 'assistant',
                  content: null,
                  tool_calls: [
                    {
                      id: toolCallId,
                      type: 'function',
                      function: {
                        name: 'calculate',
                        arguments: JSON.stringify({ expression: '1+2' })
                      }
                    }
                  ]
                },
                finish_reason: 'tool_calls'
              }
            ],
            usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 }
          })
        }

        return json(res, 200, {
          id: 'chatcmpl-mock-2',
          object: 'chat.completion',
          created: Math.floor(Date.now() / 1000),
          model: body?.model ?? 'mock-model',
          choices: [
            {
              index: 0,
              message: {
                role: 'assistant',
                content: 'The result is 3.'
              },
              finish_reason: 'stop'
            }
          ],
          usage: { prompt_tokens: 2, completion_tokens: 2, total_tokens: 4 }
        })
      }

      res.statusCode = 404
      res.end('Not Found')
    } catch {
      res.statusCode = 500
      res.end('Internal Server Error')
    }
  })

  await new Promise<void>(resolve => server.listen(port, resolve))

  return {
    url: `http://localhost:${port}`,
    close: () =>
      new Promise(resolve => {
        server.close(() => resolve())
      })
  }
}

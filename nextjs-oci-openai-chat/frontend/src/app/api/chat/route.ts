import { streamText, convertToModelMessages, stepCountIs, type UIMessage } from 'ai'
import { createOpenAICompatible } from '@ai-sdk/openai-compatible'
import { buildMcpTools } from '@/lib/mcp/tools'

export const runtime = 'nodejs'
export const maxDuration = 30

export async function POST(request: Request) {
  try {
    const toolsPromise = buildMcpTools()
    const reqJson = (await request.json().catch(() => null)) as
      | {
          messages?: UIMessage[]
          body?: Record<string, unknown>
          model?: string
        }
      | null

    const messages = reqJson?.messages

    if (!messages || !Array.isArray(messages)) {
      return Response.json({ error: 'Messages array is required' }, { status: 400 })
    }

    const bodyModel =
      reqJson && reqJson.body && typeof reqJson.body === 'object'
        ? (reqJson.body.model as string | undefined)
        : undefined

    const modelId =
      bodyModel ?? reqJson?.model ?? process.env.MODEL_ID ?? 'meta.llama-4-scout-17b-16e-instruct'

    const baseURL = `${process.env.FASTAPI_BACKEND_URL ?? 'http://localhost:3001'}/v1`
    const apiKey = process.env.FASTAPI_OPENAI_API_KEY ?? 'local'

    const openaiCompat = createOpenAICompatible({ name: 'fastapi', baseURL, apiKey })

    const [tools, modelMessages] = await Promise.all([
      toolsPromise,
      convertToModelMessages(messages as UIMessage[]),
    ])

    const loggedTools: typeof tools = {}
    for (const [name, tool] of Object.entries(tools)) {
      loggedTools[name] = {
        ...tool,
        execute: async (args: unknown, options?: unknown) => {
          const start = Date.now()
          console.log('[tool]', { phase: 'start', toolName: name })
          try {
            const executeFn = (tool as { execute?: (args: unknown, options?: unknown) => Promise<unknown> }).execute
            if (!executeFn) throw new Error(`Tool ${name} has no execute function`)
            const result = await executeFn(args, options)
            const duration = Date.now() - start
            console.log('[tool]', { phase: 'success', toolName: name, duration })
            return result
          } catch (error: unknown) {
            const duration = Date.now() - start
            const errorMsg = (error instanceof Error ? error.message : String(error)).slice(0, 100) || 'Unknown error'
            console.log('[tool]', { phase: 'error', toolName: name, duration, error: errorMsg })
            throw error
          }
        }
      }
    }

    const result = await streamText({
      model: openaiCompat.chatModel(modelId),
      messages: modelMessages,
      tools: Object.keys(loggedTools).length > 0 ? loggedTools : undefined,
      ...(Object.keys(loggedTools).length > 0 ? { stopWhen: stepCountIs(5) } : {}),
    })

    return result.toUIMessageStreamResponse()
  } catch (error) {
    console.error('API route error:', error)
    return Response.json({ error: 'Internal server error' }, { status: 500 })
  }
}

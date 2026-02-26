import { generateText } from 'ai'
import { createOpenAICompatible } from '@ai-sdk/openai-compatible'

export const runtime = 'nodejs'
export const maxDuration = 15

const FOLLOW_UP_SYSTEM = `You suggest follow-up questions. Given an assistant's message, output 3 to 5 short follow-up questions a user might ask next.
Return only a JSON array of strings. No markdown, no explanation. Example: ["First question?","Second question?"]`

export async function POST(request: Request) {
  try {
    const body = (await request.json().catch(() => null)) as
      | { lastMessage?: string; model?: string }
      | null
    const lastMessage = typeof body?.lastMessage === 'string' ? body.lastMessage.trim() : ''
    if (!lastMessage) {
      return Response.json({ suggestions: [] }, { status: 200 })
    }

    const modelId =
      body?.model ?? process.env.MODEL_ID ?? 'meta.llama-4-scout-17b-16e-instruct'
    const baseURL = `${process.env.FASTAPI_BACKEND_URL ?? 'http://localhost:3001'}/v1`
    const apiKey = process.env.FASTAPI_OPENAI_API_KEY ?? 'local'
    const openaiCompat = createOpenAICompatible({ name: 'fastapi', baseURL, apiKey })

    const { text } = await generateText({
      model: openaiCompat.chatModel(modelId),
      system: FOLLOW_UP_SYSTEM,
      prompt: lastMessage.slice(-4000),
      maxOutputTokens: 300,
    })

    const raw = text.trim().replace(/^```json?\s*|\s*```$/g, '').trim()
    let suggestions: string[] = []
    try {
      const parsed = JSON.parse(raw) as unknown
      if (Array.isArray(parsed)) {
        suggestions = parsed
          .filter((s): s is string => typeof s === 'string')
          .map((s) => s.trim())
          .filter(Boolean)
          .slice(0, 6)
      }
    } catch {
    }

    return Response.json({ suggestions })
  } catch (error) {
    console.error('[suggestions]', error)
    return Response.json({ suggestions: [] }, { status: 200 })
  }
}

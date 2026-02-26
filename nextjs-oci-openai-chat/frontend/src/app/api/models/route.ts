/**
 * Proxies the backend /api/chat/models endpoint so the client can fetch
 * the list of available OCI models without exposing FASTAPI_BACKEND_URL.
 */
export const dynamic = 'force-dynamic'

export async function GET() {
  const baseUrl = process.env.FASTAPI_BACKEND_URL ?? 'http://localhost:3001'
  const url = `${baseUrl.replace(/\/$/, '')}/api/chat/models`

  try {
    const res = await fetch(url, {
      headers: { Accept: 'application/json' },
      next: { revalidate: 0 },
    })

    if (!res.ok) {
      const text = await res.text()
      return Response.json(
        { error: 'Backend models request failed', details: text },
        { status: res.status }
      )
    }

    const data = await res.json()
    return Response.json(data)
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    return Response.json(
      { error: 'Failed to fetch models', details: message },
      { status: 502 }
    )
  }
}

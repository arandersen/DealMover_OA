import type { ExtractResponse, ApiError } from '../types'

export async function uploadPdf(file: File, periodEndDate?: string): Promise<ExtractResponse> {
  const fd = new FormData()
  fd.append('file', file)
  if (periodEndDate) fd.append('period_end_date', periodEndDate)

  const res = await fetch('/api/extract/', { method: 'POST', body: fd })
  const text = await res.text()

  let json: ExtractResponse | ApiError | unknown
  try { json = JSON.parse(text) } catch {
    throw new Error('Unexpected server response')
  }

  if (!res.ok) {
    const msg = (json as ApiError)?.error || 'Request failed'
    throw new Error(msg)
  }
  return json as ExtractResponse
}

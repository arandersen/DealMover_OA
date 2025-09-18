import { useState } from 'react'
import './App.css'
import { uploadPdf } from './api/client'
import { ResultsGrid } from './components/ResultsGrid'

export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [date, setDate] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<Awaited<ReturnType<typeof uploadPdf>> | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setData(null)
    if (!file) { setError('Please select a PDF.'); return }
    setLoading(true)
    try {
      const resp = await uploadPdf(file, date || undefined)
      setData(resp)
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Failed to upload')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 720, margin: '40px auto', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <h1 style={{ fontSize: 24, marginBottom: 12 }}>DealMover Extractor</h1>
      <form onSubmit={onSubmit} style={{ display: 'grid', gap: 12, marginBottom: 20 }}>
        <label>
          PDF file:
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>

        <label>
          Period end date (optional):
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </label>

        <button type="submit" disabled={loading} style={{ padding: '8px 12px' }}>
          {loading ? 'Extracting…' : 'Upload & Extract'}
        </button>
      </form>

      {error && (
        <div style={{ background: '#fee', color: '#900', padding: 12, borderRadius: 6, marginBottom: 12 }}>
          {error}
        </div>
      )}

      {data && (
        <>
          <p style={{ color: '#555', margin: '8px 0' }}>
            Statement period: <strong>{data.period_end_date ?? '—'}</strong>
          </p>
          <ResultsGrid revenue={data.results.revenue} grossProfit={data.results.gross_profit} />
        </>
      )}
    </div>
  )
}
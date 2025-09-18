export type ExtractResponse = {
  period_end_date: string | null
  results: {
    revenue: string
    cos: string
    gross_profit: string
  }
}

export type ApiError = { error: string }

import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token if available
if (typeof window !== 'undefined') {
  const token = localStorage.getItem('token')
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }
}

export interface Market {
  id: string
  symbol: string
  name: string
  type: string
  exchange?: string
  created_at: string
}

export interface Sentiment {
  symbol: string
  sentiment: 'bull' | 'bear' | 'neutral'
  bull_score: number
  bear_score: number
  confidence: number
  reasoning: string
  support?: number
  resistance?: number
  timestamp?: string
}

export interface Candle {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export const marketAPI = {
  listMarkets: () => apiClient.get<Market[]>('/api/v1/markets/list'),

  addMarket: (data: { symbol: string; name: string; type: string; exchange?: string }) =>
    apiClient.post<Market>('/api/v1/markets/add', data),

  getSentiment: (symbol: string) =>
    apiClient.get<Sentiment>(`/api/v1/markets/${symbol}/sentiment`),

  computeSentiment: (symbol: string) =>
    apiClient.post<Sentiment>(`/api/v1/markets/${symbol}/compute-sentiment`),

  getCandles: (symbol: string, limit?: number) =>
    apiClient.get(`/api/v1/markets/${symbol}/candles`, { params: { limit } }),
}

export default apiClient

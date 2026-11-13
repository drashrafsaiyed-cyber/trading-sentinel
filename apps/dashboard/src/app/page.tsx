'use client'

import { useEffect, useState } from 'react'
import { marketAPI, Market, Sentiment } from '@/lib/api'
import SentimentCard from '@/components/SentimentCard'
import Header from '@/components/Header'
import axios from 'axios'

const EXAMPLES = [
  { label: 'Reliance', symbol: 'RELIANCE.NS' },
  { label: 'TCS', symbol: 'TCS.NS' },
  { label: 'Infosys', symbol: 'INFY.NS' },
  { label: 'HDFC Bank', symbol: 'HDFCBANK.NS' },
  { label: 'Nifty 50', symbol: '^NSEI' },
  { label: 'Apple', symbol: 'AAPL' },
  { label: 'Bitcoin', symbol: 'BTC-USD' },
]

function friendlyError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    if (err.response?.data?.detail) return err.response.data.detail
    if (err.code === 'ERR_NETWORK' || err.message === 'Network Error') {
      return 'Server is waking up (free tier sleeps when idle). Wait ~40s and try again.'
    }
    return err.message
  }
  return 'Something went wrong'
}

export default function Dashboard() {
  const [markets, setMarkets] = useState<Market[]>([])
  const [sentiments, setSentiments] = useState<Record<string, Sentiment>>({})
  const [loading, setLoading] = useState(true)
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [input, setInput] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const marketsRes = await marketAPI.listMarkets()
      setMarkets(marketsRes.data)
      // Load sentiment for each existing market (best-effort)
      for (const market of marketsRes.data) {
        marketAPI
          .getSentiment(market.symbol)
          .then((r) => setSentiments((s) => ({ ...s, [market.symbol]: r.data })))
          .catch(() => {})
      }
    } catch (err) {
      setError(friendlyError(err))
    } finally {
      setLoading(false)
    }
  }

  const addSymbol = async (raw: string) => {
    const symbol = raw.trim().toUpperCase()
    if (!symbol) return
    if (markets.some((m) => m.symbol === symbol)) {
      setError(`${symbol} is already on the board.`)
      return
    }
    try {
      setAdding(true)
      setError(null)
      // 1. Add the market (validates the symbol via live data)
      const newMarket = await marketAPI.addMarket({ symbol, name: symbol, type: 'stock' })
      setMarkets((m) => [...m, newMarket.data])
      setInput('')
      // 2. Immediately compute sentiment so the card fills in itself
      try {
        const sent = await marketAPI.computeSentiment(symbol)
        setSentiments((s) => ({ ...s, [symbol]: sent.data }))
      } catch {
        /* card will show a Load button as fallback */
      }
    } catch (err) {
      setError(friendlyError(err))
    } finally {
      setAdding(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <Header />

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-4xl font-bold text-white mb-2">Trading Sentiment</h1>
          <p className="text-slate-400">AI-powered Bull / Bear predictions · stocks, crypto, Indian NSE/BSE</p>
        </div>

        {error && (
          <div className="bg-red-900/80 text-red-100 p-4 rounded-lg mb-6 flex justify-between items-center">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-red-200 hover:text-white ml-4">✕</button>
          </div>
        )}

        {/* Add Symbol */}
        <div className="bg-slate-800 rounded-lg p-6 mb-6 border border-slate-700">
          <h2 className="text-lg font-semibold text-white mb-1">Add a Symbol</h2>
          <p className="text-sm text-slate-400 mb-4">
            Indian stocks need a suffix: <code className="text-amber-300">.NS</code> for NSE,{' '}
            <code className="text-amber-300">.BO</code> for BSE (e.g. <code className="text-amber-300">RELIANCE.NS</code>).
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              addSymbol(input)
            }}
            className="flex gap-2 mb-4"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="RELIANCE.NS, TCS.NS, AAPL, BTC-USD…"
              className="flex-1 px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={adding}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded-lg font-medium transition min-w-[90px]"
            >
              {adding ? 'Adding…' : 'Add'}
            </button>
          </form>

          {/* Quick-add examples */}
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex.symbol}
                onClick={() => addSymbol(ex.symbol)}
                disabled={adding}
                className="px-3 py-1 text-sm bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-full border border-slate-600 disabled:opacity-50"
              >
                + {ex.label}
              </button>
            ))}
          </div>
        </div>

        {/* Loading initial */}
        {loading && (
          <div className="text-center py-8 text-slate-400">Loading… (first load can take ~40s while the server wakes)</div>
        )}

        {/* Cards */}
        {!loading && markets.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {markets.map((market) => (
              <SentimentCard
                key={market.id}
                market={market}
                sentiment={sentiments[market.symbol]}
                onRefresh={() => {
                  marketAPI
                    .computeSentiment(market.symbol)
                    .then((res) => setSentiments((s) => ({ ...s, [market.symbol]: res.data })))
                    .catch((err) => setError(friendlyError(err)))
                }}
              />
            ))}
          </div>
        )}

        {!loading && markets.length === 0 && (
          <div className="text-center py-10 text-slate-400">
            No symbols yet. Tap a quick-add above or type a ticker to see its Bull/Bear signal.
          </div>
        )}
      </main>
    </div>
  )
}

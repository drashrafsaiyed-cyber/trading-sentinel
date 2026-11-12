'use client'

import { useEffect, useState } from 'react'
import { marketAPI, Market, Sentiment } from '@/lib/api'
import SentimentCard from '@/components/SentimentCard'
import Header from '@/components/Header'
import axios from 'axios'

export default function Dashboard() {
  const [markets, setMarkets] = useState<Market[]>([])
  const [sentiments, setSentiments] = useState<Record<string, Sentiment>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch markets
      const marketsRes = await marketAPI.listMarkets()
      setMarkets(marketsRes.data)

      // Fetch sentiment for each market
      const sentimentData: Record<string, Sentiment> = {}
      for (const market of marketsRes.data) {
        try {
          const sentRes = await marketAPI.getSentiment(market.symbol)
          sentimentData[market.symbol] = sentRes.data
        } catch (err) {
          console.error(`Failed to fetch sentiment for ${market.symbol}:`, err)
        }
      }
      setSentiments(sentimentData)
    } catch (err) {
      const message = axios.isAxiosError(err) ? err.message : 'Failed to load data'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const handleAddMarket = async (symbol: string) => {
    try {
      const newMarket = await marketAPI.addMarket({
        symbol,
        name: symbol.toUpperCase(),
        type: 'stock',
      })
      setMarkets([...markets, newMarket.data])
    } catch (err) {
      const message = axios.isAxiosError(err) ? err.response?.data?.detail || err.message : 'Failed to add market'
      setError(message)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <Header />

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Title */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Trading Sentiment</h1>
          <p className="text-slate-400">AI-powered Bull/Bear predictions</p>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-900 text-red-100 p-4 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Add Market Form */}
        <div className="bg-slate-800 rounded-lg p-6 mb-8 border border-slate-700">
          <h2 className="text-lg font-semibold text-white mb-4">Add Symbol to Track</h2>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              const input = (e.target as HTMLFormElement).symbol as any
              handleAddMarket(input.value.toUpperCase())
              input.value = ''
            }}
            className="flex gap-2"
          >
            <input
              type="text"
              name="symbol"
              placeholder="e.g., AAPL, BTC-USD, EURUSD"
              className="flex-1 px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-blue-500 focus:outline-none"
            />
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
            >
              Add
            </button>
          </form>
        </div>

        {/* Loading */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-slate-800 rounded-lg h-48 animate-pulse border border-slate-700" />
            ))}
          </div>
        )}

        {/* Sentiment Cards */}
        {!loading && markets.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {markets.map((market) => (
              <SentimentCard
                key={market.id}
                market={market}
                sentiment={sentiments[market.symbol]}
                onRefresh={() => {
                  marketAPI.computeSentiment(market.symbol).then((res) => {
                    setSentiments({ ...sentiments, [market.symbol]: res.data })
                  })
                }}
              />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && markets.length === 0 && (
          <div className="text-center py-12">
            <p className="text-slate-400 text-lg">No markets tracked yet. Add one to get started!</p>
          </div>
        )}
      </main>
    </div>
  )
}

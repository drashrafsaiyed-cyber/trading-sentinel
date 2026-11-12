import { Market, Sentiment } from '@/lib/api'
import clsx from 'clsx'

interface SentimentCardProps {
  market: Market
  sentiment?: Sentiment
  onRefresh: () => void
}

export default function SentimentCard({ market, sentiment, onRefresh }: SentimentCardProps) {
  if (!sentiment) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 flex items-center justify-center min-h-[250px]">
        <button
          onClick={onRefresh}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition"
        >
          Load Sentiment
        </button>
      </div>
    )
  }

  const isBull = sentiment.sentiment === 'bull'
  const sentimentColor = isBull ? 'text-bull' : 'text-bear'
  const bgColor = isBull ? 'from-bull/10 to-bull/5' : 'from-bear/10 to-bear/5'

  return (
    <div className={clsx('bg-gradient-to-br', bgColor, 'rounded-lg p-6 border', isBull ? 'border-bull/30' : 'border-bear/30')}>
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-bold text-white">{market.symbol}</h3>
          <p className="text-sm text-slate-400">{market.name}</p>
        </div>
        <button
          onClick={onRefresh}
          className="text-slate-400 hover:text-white transition"
          title="Refresh"
        >
          🔄
        </button>
      </div>

      {/* Sentiment Display */}
      <div className="mb-6">
        <div className={clsx('text-4xl font-bold mb-2', sentimentColor)}>
          {sentiment.sentiment.toUpperCase()}
        </div>
        <div className="flex gap-6 mb-3">
          <div>
            <div className="text-sm text-slate-400">Bull</div>
            <div className={clsx('text-2xl font-bold', isBull ? 'text-bull' : 'text-slate-500')}>
              {sentiment.bull_score.toFixed(0)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-slate-400">Bear</div>
            <div className={clsx('text-2xl font-bold', !isBull ? 'text-bear' : 'text-slate-500')}>
              {sentiment.bear_score.toFixed(0)}%
            </div>
          </div>
        </div>

        {/* Confidence Bar */}
        <div className="bg-slate-700 rounded-full h-2 overflow-hidden">
          <div
            className={clsx('h-full', isBull ? 'bg-bull' : 'bg-bear')}
            style={{ width: `${sentiment.confidence}%` }}
          />
        </div>
        <p className="text-xs text-slate-400 mt-1">Confidence: {sentiment.confidence.toFixed(0)}%</p>
      </div>

      {/* Reasoning */}
      <div className="mb-4">
        <p className="text-sm text-slate-300">{sentiment.reasoning}</p>
      </div>

      {/* Support/Resistance */}
      {sentiment.support && sentiment.resistance && (
        <div className="bg-slate-700 rounded p-3 text-xs text-slate-300">
          <div className="flex justify-between">
            <span>Support: ${sentiment.support.toFixed(2)}</span>
            <span>Resistance: ${sentiment.resistance.toFixed(2)}</span>
          </div>
        </div>
      )}
    </div>
  )
}

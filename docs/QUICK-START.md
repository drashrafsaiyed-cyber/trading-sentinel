# Trading Sentinel — Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Backend Setup

```bash
cd apps/api

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and set:
# DATABASE_URL=sqlite:///./test.db (for testing)
# or postgresql://user:pass@localhost/trading_sentinel (for production)

# Run server
python run_server.py
```

**Server runs at:** `http://localhost:8000`  
**API Docs:** `http://localhost:8000/docs` (Swagger UI)

### Frontend Setup

```bash
cd apps/dashboard

# Install dependencies
npm install

# Set environment
# Create .env.local with:
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Run dev server
npm run dev
```

**Dashboard runs at:** `http://localhost:3000`

---

## 🧪 Test the API

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Add a Market
```bash
curl -X POST http://localhost:8000/api/v1/markets/add \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "type": "stock",
    "exchange": "NASDAQ"
  }'
```

### 3. List Markets
```bash
curl http://localhost:8000/api/v1/markets/list
```

### 4. Get Sentiment (Bull/Bear)
```bash
curl http://localhost:8000/api/v1/markets/AAPL/sentiment
```

### 5. Compute Sentiment
```bash
curl -X POST http://localhost:8000/api/v1/markets/AAPL/compute-sentiment
```

### 6. Get Candles (OHLCV Data)
```bash
curl http://localhost:8000/api/v1/markets/AAPL/candles?limit=50
```

---

## 📊 Example Response

```json
{
  "symbol": "AAPL",
  "sentiment": "bull",
  "bull_score": 65.4,
  "bear_score": 34.6,
  "confidence": 65.4,
  "reasoning": "BULL 65% - Price above 200-MA (bullish trend) · RSI 55 · MACD positive crossover",
  "support": 182.45,
  "resistance": 195.32,
  "timestamp": "2024-11-12T19:30:00.000Z"
}
```

---

## 🔗 Key Files

| File | Purpose |
|---|---|
| `apps/api/app/main.py` | FastAPI app entry |
| `apps/api/app/core/indicators.py` | Technical indicators (RSI, MACD, etc.) |
| `apps/api/app/core/ml_sentiment.py` | Bull/Bear sentiment prediction |
| `apps/api/app/api/markets.py` | Markets endpoints |
| `apps/dashboard/src/app/page.tsx` | Main dashboard page |
| `apps/dashboard/src/components/SentimentCard.tsx` | Sentiment display card |

---

## ⚙️ Environment Variables

### Backend (`.env`)
```
DATABASE_URL=postgresql://user:password@localhost:5432/trading_sentinel
REDIS_URL=redis://localhost:6379
AI_PROVIDER=nvidia
NVIDIA_API_KEY=your_key_here
NVIDIA_MODEL=meta/llama-3.1-70b-instruct
JWT_SECRET=change-me-in-production
TELEGRAM_BOT_TOKEN=your_token_here
```

### Frontend (`.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Or use different port
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Database Connection Error
- For quick testing, use SQLite: `DATABASE_URL=sqlite:///./test.db`
- For Postgres, ensure server is running and URL is correct

### AI Provider Errors
- NVIDIA NIM API requires valid `NVIDIA_API_KEY`
- Free tier has unlimited requests
- If key invalid, sentiment still works (rule-based fallback)

---

## 📚 Next Steps

1. **Add more markets** — Try GOOGL, BTC-USD, EURUSD
2. **Build watchlist feature** — See Day 3 plan in 2-WEEK-LAUNCH-PLAN.md
3. **Add authentication** — User login/register
4. **Deploy to cloud** — Render (backend) + Vercel (frontend)

---

## 📖 API Documentation

Full auto-generated docs available at:
```
http://localhost:8000/docs
```

Interactive API playground with "Try it out" buttons.

---

**Questions?** Check the repo README or edit `docs/2-WEEK-LAUNCH-PLAN.md`

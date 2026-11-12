# Trading Sentinel — AI-Powered Trading Sentiment Analysis

Real-time Bull/Bear market predictions using AI pattern recognition.

## 🚀 Stack
- **Backend**: FastAPI + PostgreSQL + Redis
- **Frontend**: Next.js 14 + TypeScript + Tailwind
- **ML**: NVIDIA NIM + scikit-learn
- **Data**: yfinance (free), Alpaca API (optional)

## 📋 2-Week Roadmap

### **Week 1: Backend**
- [ ] Day 1-2: FastAPI scaffold + DB setup
- [ ] Day 3-4: Technical indicators + ML sentiment
- [ ] Day 5: API endpoints + WebSocket
- [ ] Day 6-7: Alerts + testing

### **Week 2: Frontend**
- [ ] Day 1-3: Dashboard scaffold + components
- [ ] Day 4-5: Charts + real-time updates
- [ ] Day 6: PWA + mobile support
- [ ] Day 7: Deploy + monitoring

## 🏃 Quick Start

**Backend:**
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_server.py
```

**Frontend:**
```bash
cd apps/dashboard
npm install
npm run dev
```

## 📊 Features (MVP)

1. **Real-time Sentiment** — Bull/Bear % + confidence
2. **Technical Analysis** — RSI, MACD, Moving Averages, Support/Resistance
3. **Watchlist** — Track symbols, set alerts
4. **Backtesting** — Test signals vs historical data
5. **Telegram Alerts** — Sentiment flip notifications

## 💰 Revenue Model

- **Free**: 5 watchlists, daily sentiment
- **Pro ₹999/mo**: Unlimited, real-time alerts, backtesting
- **API ₹5,000/mo**: Third-party integration

---

**Target Launch:** 2 weeks from now

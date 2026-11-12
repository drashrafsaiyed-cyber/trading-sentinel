# Trading Sentinel — 2-Week Launch Plan

**Target Launch Date:** 2 weeks from now  
**Status:** Day 1 — Foundation complete  
**Built:** Backend scaffold + DB schema + ML engine + Frontend scaffold

---

## 📋 Week 1: Backend Complete

### Day 1-2: Data Flow ✅
- [x] FastAPI scaffold
- [x] PostgreSQL schema
- [x] yfinance data ingestion
- [x] Technical indicators (RSI, MACD, Bollinger, SMA)
- [x] ML sentiment engine (rule-based + AI)
- [x] Markets API endpoints

**Next:** Test end-to-end
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_server.py
```

Then from another terminal:
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/markets/add \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "name": "Apple", "type": "stock"}'
```

### Day 3: Authentication & Users
- [ ] JWT login/logout endpoints
- [ ] User registration
- [ ] Password hashing (bcrypt)
- [ ] Token validation middleware
- [ ] User model CRUD

**Files to create:**
- `app/api/auth.py` — login, register, me, change-password
- `app/core/security.py` — JWT, bcrypt helpers

### Day 4: Watchlists & Alerts
- [ ] Watchlist CRUD endpoints
- [ ] Alert creation (sentiment flip, price target, stop loss)
- [ ] Alert dispatch logic (Telegram notifications)
- [ ] Telegram bot integration

**Files to create:**
- `app/api/watchlists.py`
- `app/api/alerts.py`
- `app/core/telegram.py`
- `app/jobs/alert_dispatcher.py`

### Day 5: Backtesting Engine
- [ ] Backtest strategy (buy on bull, sell on bear)
- [ ] Historical accuracy computation
- [ ] Win rate, drawdown, return % metrics
- [ ] Backtest results storage & API

**Files to create:**
- `app/core/backtesting.py`
- `app/api/backtests.py`

### Day 6-7: Testing & Polish
- [ ] Write pytest test suite (20+ tests)
- [ ] Test auth, CRUD, sentiment prediction, backtesting
- [ ] Fix bugs found
- [ ] API documentation (auto-generated from FastAPI)

---

## 📊 Week 2: Frontend Complete

### Day 1-2: Core Dashboard
- [ ] Markets list page
- [ ] Sentiment card component (with % bars, reasoning)
- [ ] Real-time updates (WebSocket optional)
- [ ] Add/remove markets UI

**Pages:**
- `/` — Dashboard (sentiment cards grid)
- `/markets/{symbol}` — Market detail (chart + history)

### Day 3: Watchlist & Charts
- [ ] Watchlist page
- [ ] Add to watchlist modal
- [ ] Chart component (Recharts candlestick)
- [ ] Entry/target/stop-loss visualization

**Pages:**
- `/watchlist` — User's watchlist

### Day 4: Alerts & Settings
- [ ] Alert history page
- [ ] User settings (API key, preferences)
- [ ] Telegram linking UI
- [ ] Subscription tier display

**Pages:**
- `/alerts` — Alert history
- `/settings` — User preferences

### Day 5: Auth Pages
- [ ] Login page
- [ ] Register page
- [ ] Auth context (Zustand store)
- [ ] Protected routes

**Pages:**
- `/login`
- `/register`

### Day 6: Mobile & PWA
- [ ] Responsive design (mobile-first Tailwind)
- [ ] PWA manifest
- [ ] Service worker (offline support)
- [ ] Install banner

### Day 7: Deploy & Launch
- [ ] Database migrations (Supabase)
- [ ] Deploy backend to Render
- [ ] Deploy frontend to Vercel
- [ ] DNS setup (trading-sentinel.com)
- [ ] Smoke tests

---

## 🔧 Tech Decisions (Locked)

| Component | Tech | Why |
|---|---|---|
| Backend | FastAPI | Fast, async, AI provider agnostic |
| Database | PostgreSQL | Time-series queries (TimescaleDB ready) |
| Cache | Redis | Real-time alerts, WebSocket state |
| ML | NVIDIA NIM (free tier) | Unlimited requests, no quota |
| Frontend | Next.js 14 | PWA, Server Components, best DX |
| Styling | Tailwind | Fast theming, dark mode native |
| Charts | Recharts | Simple candlestick charts |
| Hosting | Vercel + Render | Fast deploys, free tier works |

---

## 💰 Revenue Model (MVP)

- **Free** — 5 watchlists, daily sentiment, no alerts
- **Pro ₹999/mo** — Unlimited, real-time alerts, backtesting history
- **API ₹5,000/mo** — Programmatic access for developers

**MVP = Free tier only** (no billing yet)

---

## 📱 Minimum Viable Features

**Must Have:**
1. Sentiment prediction (Bull/Bear %)
2. Multiple watchlists
3. Alerts on sentiment flip
4. Backtest accuracy
5. Mobile-responsive UI

**Nice to Have (post-launch):**
- Live trading integration (Alpaca, TD Ameritrade)
- Social trading (share signals)
- Advanced charting (TradingView embedded)
- Machine learning model retraining pipeline
- Portfolio optimization

---

## 🚀 Launch Checklist

### Backend
- [ ] All 5 API endpoint modules complete
- [ ] 20+ unit tests passing
- [ ] Database migrations work
- [ ] Error handling + logging
- [ ] Rate limiting
- [ ] CORS configured

### Frontend
- [ ] All 7 pages complete
- [ ] Mobile responsive
- [ ] TypeScript `tsc --noEmit` passing
- [ ] Auth flow works
- [ ] API client working
- [ ] PWA manifest + service worker

### DevOps
- [ ] GitHub repo (private or public)
- [ ] Render setup (ENV vars)
- [ ] Vercel setup (ENV vars)
- [ ] Database backups enabled
- [ ] Monitoring/logging

### Marketing
- [ ] Landing page (tpadesk-website.vercel.app style)
- [ ] Privacy policy + Terms
- [ ] Twitter/LinkedIn launch post
- [ ] Product Hunt launch (optional)

---

## 📊 Success Metrics (Post-Launch)

- **Week 1:** 10 daily active users
- **Week 2:** 50 DAU
- **Week 3:** 100 DAU, first paid signup
- **Month 2:** 1,000 DAU, ₹5K MRR

---

## 🎯 This Session (Day 1)

✅ **Completed:**
- Backend scaffold (FastAPI, DB, indicators, ML)
- Frontend scaffold (Next.js, Tailwind, components)
- API endpoints (markets CRUD, sentiment)
- Data ingestion (yfinance)

**Next Sessions:**
1. **Session 2 (Day 2-3):** Test backend, auth endpoints
2. **Session 3 (Day 4-5):** Watchlists, alerts, Telegram
3. **Session 4 (Day 6-7):** Backtesting engine
4. **Session 5 (Day 8-10):** Frontend dashboard + charts
5. **Session 6 (Day 11-13):** Auth pages, PWA
6. **Session 7 (Day 14):** Deploy + launch

---

## 🔗 Repository

Clone and run:
```bash
git clone /home/user/trading-sentinel
cd trading-sentinel

# Backend (Day 2: pip install, test)
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run_server.py  # http://localhost:8000

# Frontend (Day 5: npm install, test)
cd apps/dashboard
npm install
npm run dev  # http://localhost:3000
```

---

## 💡 Notes

- **AI Provider:** Starts with NVIDIA NIM (free, unlimited). Switch to Anthropic Claude for production.
- **Database:** Use PostgreSQL locally (or Supabase free tier for multi-device sync).
- **Deployment:** Free tier Render + Vercel (paid after 1000 users).
- **Testing:** pytest for backend, Cypress for frontend (Session 4+).

# Deploy Trading Sentinel — Supabase + Render + Vercel

Order matters. Follow top to bottom. Total ~20 min.

---

## Step 1 — GitHub repo (you)

Render and Vercel both deploy from GitHub, so the code needs to live there.

1. Go to https://github.com/new
2. Name: **`trading-sentinel`**, owner **drashrafsaiyed-cyber**, **Private**.
3. **Do NOT** add a README/.gitignore/license (keep it empty).
4. Create it, then tell me — I'll push all the code to it.

---

## Step 2 — Supabase Postgres (you)

1. https://supabase.com → New Project → name `trading-sentinel`, region **Mumbai (ap-south-1)**.
2. Set a strong DB password (save it).
3. Wait for it to provision (~2 min).
4. Project → **Connect** (top bar) → **Connection string** → **Transaction pooler** tab.
   - Copy the URI. It looks like:
     `postgresql://postgres.xxxx:[PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres`
   - Replace `[PASSWORD]` with your DB password.
5. Keep this string — it's the `DATABASE_URL` for Render in Step 3.
   - **No manual SQL needed** — the backend auto-creates all tables on first boot.

> Use the **transaction pooler (port 6543)**, not the direct connection — Render's
> free tier needs it, and the code is already configured for pgbouncer.

---

## Step 3 — Render backend (you, I prep everything)

1. https://render.com → New + → **Blueprint**.
2. Connect the `trading-sentinel` repo. Render reads `render.yaml` automatically.
3. It creates **trading-sentinel-api**. Before/after first deploy, open the service →
   **Environment** → set the secrets marked "sync: false":
   - `DATABASE_URL` = the Supabase pooler string from Step 2
   - `CORS_ORIGINS` = leave blank for now (we add the Vercel URL in Step 5; the
     code already allows any `*.vercel.app` automatically)
   - `NVIDIA_API_KEY` = (optional) your NVIDIA NIM key for AI reasoning
   - `TELEGRAM_BOT_TOKEN` = (optional) for alert delivery
4. Deploy. When green, copy the service URL:
   `https://trading-sentinel-api.onrender.com`
5. Test it: open `https://trading-sentinel-api.onrender.com/health` → should show
   `{"status":"ok"}`. And `/docs` → full API.

---

## Step 4 — Vercel frontend (you + me)

1. https://vercel.com → Add New → **Project** → import `trading-sentinel`.
2. **Root Directory**: click Edit → set to **`apps/dashboard`**. (Critical — it's a monorepo.)
3. Framework preset: **Next.js** (auto-detected).
4. **Environment Variables** → add:
   - `NEXT_PUBLIC_API_URL` = `https://trading-sentinel-api.onrender.com` (from Step 3)
5. Deploy. You'll get `https://trading-sentinel.vercel.app`.

---

## Step 5 — Connect the two (you)

1. Back in **Render** → trading-sentinel-api → Environment →
   set `CORS_ORIGINS` = `https://trading-sentinel.vercel.app` (your real Vercel URL).
2. Save → Render redeploys.
3. Open your Vercel URL → add a symbol (AAPL) → you'll see live Bull/Bear sentiment. 🎉

---

## Notes

- **First Render request after idle is slow** (free tier sleeps ~15 min). Upgrade to
  Starter ($7/mo) when you get a paying customer — same lesson as TPAdesk.
- **AI is optional** — without `NVIDIA_API_KEY` the sentiment still works (rule-based
  on RSI/MACD/moving averages). Add the key later for AI-written reasoning.
- **Custom domain** — add `app.tradingsentinel.ai` in Vercel later; point `CORS_ORIGINS`
  at it too.
- **Database tables** are created automatically on backend boot — no migrations to run
  for the MVP. (RLS hardening comes in a later pass.)

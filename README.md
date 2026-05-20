# 🔗 PharmaChain

> **AI + Blockchain Pharmaceutical Supply Chain Verification & Crisis Intelligence Platform**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.136+-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat&logo=react)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat&logo=postgresql)](https://postgresql.org)
[![Ethereum](https://img.shields.io/badge/Blockchain-Sepolia-627EEA?style=flat&logo=ethereum)](https://sepolia.etherscan.io)
[![Gemini](https://img.shields.io/badge/AI-Gemini_2.5_Flash-4285F4?style=flat&logo=google)](https://aistudio.google.com)

---

## 🎯 What is PharmaChain?

PharmaChain is a **three-party attestation system** for pharmaceutical supply chains. Every shipment requires independent data submissions from the **Manufacturer**, **Supplier**, and **Hospital/NGO** — and a Hybrid AI engine cross-matches all three in real-time.

**One-line pitch:** Fraud requires simultaneous collusion across ALL three parties — recorded immutably on blockchain. No IoT hardware needed. Works in conflict zones.

**Market:** $4.4T pharma market · $180B+ lost to disruption · 1M+ deaths/year from counterfeits

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│              THREE PARTY PORTALS (React)              │
├──────────────────────────────────────────────────────┤
│  Manufacturer    │    Supplier      │   Hospital/NGO  │
│  (batch create)  │  (verification)  │ (receipt confirm)│
└────────┬─────────────────┬──────────────────┬────────┘
         └─────────────────┼──────────────────┘
                           │
                ┌──────────▼──────────┐
                │   FastAPI Backend   │
                │   + PostgreSQL      │
                │   + Redis           │
                └──────────┬──────────┘
                           │
        ┌──────────────────┼───────────────────┐
        │                  │                   │
    ┌───▼────┐      ┌──────▼──────┐    ┌───────▼─────┐
    │  Auth  │      │  Hybrid AI  │    │  Blockchain │
    │  + JWT │      │  (4 modules)│    │  Sepolia    │
    └────────┘      │             │    └─────────────┘
                    │ 1. Verif AI │
                    │ 2. Stock AI │
                    │ 3. Crisis AI│
                    │ 4. Trust Eng│
                    └─────────────┘
```

---

## 🧠 Hybrid AI System

The Verification AI runs in **two layers**:

| Layer | What it does |
|-------|-------------|
| **Layer 1 — Rule Engine** | Deterministic math: quantity deviation >15%, expiry mismatch, temperature breach. Always runs. Never blocks. |
| **Layer 2 — Gemini 2.5 Flash** | When a shipment is FLAGGED, calls Google Gemini to generate a plain-English investigation report: root cause, likely explanation, recommended action for the compliance officer. Falls back gracefully if API key missing. |

---

## ✨ Key Features

- 🔐 **JWT Authentication** — Role-based access (Manufacturer Admin / Supplier Manager / Hospital Officer)
- 🤖 **Hybrid AI Verification** — Rule engine + Gemini LLM investigator
- ⛓️ **Ethereum Blockchain** — Immutable on-chain records (Sepolia testnet, mock mode for dev)
- 📋 **Approval Audit Log** — Append-only compliance trail for every critical action (DSCSA/FMD ready)
- 📦 **Stock Intelligence** — Threshold-based alerts + auto restock requests
- 🗺️ **Crisis & Rerouting AI** — NewsAPI disruption detection + Dijkstra alternate route suggestions
- 🏅 **Trust Engine** — Entity trust scores updated after every verification
- 📱 **QR Verification** — Public shipment verification page with blockchain hash
- 🔔 **Real-time Notifications** — Redis pub/sub alerts in dashboard

---

## 🛠️ Tech Stack

**Backend:** FastAPI · SQLAlchemy 2.0 · Alembic · Pydantic v2 · python-jose · bcrypt · APScheduler

**Database:** PostgreSQL 16 · Redis 7

**Blockchain:** Ethereum Sepolia · web3.py 7 · Solidity 0.8.20

**Frontend:** React 18 · React Router v6 · Vite · Axios · Mapbox GL JS · react-qr-code

**AI/ML:** Google Gemini 2.5 Flash (LLM Investigator) · Rule Engine (Hybrid Layer 1)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- PostgreSQL 16
- Redis 7

### 1. Clone & setup environment

```bash
git clone https://github.com/yourusername/pharmachain.git
cd pharmachain
```

**Backend:**
```bash
cd backend
cp .env.example .env        # Fill in your values
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
cp .env.example .env        # Fill in your Mapbox token
npm install
```

### 2. Run database migrations

```bash
cd backend
alembic upgrade head
```

### 3. Seed demo data (optional)

```bash
cd backend
python scripts/reset_and_seed.py
```

This creates three demo accounts:

| Email | Password | Role |
|-------|----------|------|
| `manufacturer@pharmachain.com` | `PharmaChain2026!` | Manufacturer Admin |
| `supplier@pharmachain.com` | `PharmaChain2026!` | Supplier Manager |
| `hospital@pharmachain.com` | `PharmaChain2026!` | Hospital Officer |

### 4. Start servers

**Terminal 1 — Backend:**
```bash
cd backend
venv\Scripts\uvicorn main:app --reload
# Backend runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
# Frontend runs at http://localhost:5173
```

---

## 🌐 API Endpoints

| Module | Endpoints |
|--------|-----------|
| **Auth** | `POST /auth/register` · `POST /auth/login` · `POST /auth/logout` · `POST /auth/refresh` |
| **Manufacturer** | `POST /manufacturer/batches` · `GET /manufacturer/batches` · `POST /manufacturer/shipments/{id}/dispatch` |
| **Supplier** | `GET /supplier/shipments/incoming` · `POST /supplier/shipments/{id}/verify` · `GET/PUT /supplier/inventory` |
| **Hospital** | `GET /consumer/shipments/incoming` · `POST /consumer/shipments/{id}/confirm` · `POST /consumer/stock-requests` |
| **Verification AI** | `POST /verification-ai/batches/{id}/verify` · `GET /verification-ai/flags/{shipment_id}` |
| **QR / Public** | `GET /qr/shipment/{id}` · `GET /shared/shipment/{id}` |
| **Approval Logs** | `GET /approval-logs` |
| **Notifications** | `GET /notifications` |
| **Health** | `GET /health` |

Full interactive docs: `http://localhost:8000/docs`

---

## 🔑 Environment Variables

See [`backend/.env.example`](backend/.env.example) and [`frontend/.env.example`](frontend/.env.example) for all required variables.

Key variables to set:

| Variable | Where to get it |
|----------|----------------|
| `GEMINI_API_KEY` | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) — Free |
| `MAPBOX_TOKEN` / `VITE_MAPBOX_TOKEN` | [account.mapbox.com](https://account.mapbox.com) — Free |
| `NEWS_API_KEY` | [newsapi.org/register](https://newsapi.org/register) — Free |
| `ETHEREUM_RPC_URL` | [dashboard.alchemy.com](https://dashboard.alchemy.com) — Free |
| `ETHEREUM_PRIVATE_KEY` | Your MetaMask wallet private key (Sepolia testnet) |
| `CONTRACT_ADDRESS` | After deploying `contracts/PharmaChain.sol` to Sepolia |

> **Tip:** Leave all Blockchain vars empty to run in **Mock Mode** — safe for local development, no real wallet needed.

---

## 🔒 Smart Contract

The Solidity contract lives at [`contracts/PharmaChain.sol`](contracts/PharmaChain.sol).

To deploy to Sepolia testnet:
```bash
cd contracts
npm install
npx hardhat run scripts/deploy.js --network sepolia
# Copy the deployed address to CONTRACT_ADDRESS in backend/.env
```

---

## 🏆 Why PharmaChain Wins

1. **Three-party attestation** — nobody else has this angle
2. **Hybrid AI fraud detection** — deterministic rules + LLM explainability
3. **Blockchain + real use case** — not just blockchain for hype
4. **No IoT dependency** — works in war zones, conflict areas, NGO field ops
5. **Full approval audit trail** — DSCSA/FMD compliance-ready
6. **End-to-end demo** — manufacturer → supplier → hospital → flagged shipment → approval log

---

## 📁 Project Structure

```
pharmachain/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Pydantic settings (reads .env)
│   ├── models.py                  # SQLAlchemy ORM models
│   ├── auth/                      # JWT auth + role guards
│   ├── manufacturer/              # Manufacturer portal endpoints
│   ├── supplier/                  # Supplier portal endpoints
│   ├── consumer/                  # Hospital/NGO portal endpoints
│   ├── verification_ai/           # Hybrid AI verification engine
│   │   ├── engine.py              # Layer 1: Rule engine
│   │   └── llm_investigator.py    # Layer 2: Gemini LLM investigator
│   ├── inventory_ai/              # Stock threshold monitoring
│   ├── crisis_ai/                 # NewsAPI disruption + rerouting
│   ├── trust_engine/              # Entity trust score engine
│   ├── blockchain_service/        # web3.py + Sepolia integration
│   ├── notification_service/      # Redis pub/sub alerts
│   ├── approval_logs/             # Append-only audit trail
│   ├── qr_service/                # QR code generation
│   ├── shared/                    # Public shipment page API
│   ├── scripts/
│   │   └── reset_and_seed.py      # Dev DB reset + demo data seeder
│   ├── alembic/                   # Database migrations
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/                 # Role dashboards + public pages
│   │   ├── components/            # Reusable UI components
│   │   └── api/                   # Axios API clients
│   ├── package.json
│   └── .env.example
├── contracts/
│   └── PharmaChain.sol            # Solidity smart contract
├── .gitignore
└── README.md
```

---

## 🌍 Production Deployment Guide

> Deploy the full stack **for free** using Railway (backend) + Supabase (PostgreSQL) + Upstash (Redis) + Vercel (frontend).

### Overview — 4 Services

| Service | What it hosts | Free tier |
|---------|--------------|-----------|
| **[Supabase](https://supabase.com)** | PostgreSQL database | ✅ Free |
| **[Upstash](https://upstash.com)** | Redis | ✅ Free |
| **[Railway](https://railway.app)** | FastAPI backend | ✅ Free tier |
| **[Vercel](https://vercel.com)** | React frontend | ✅ Free |

---

### Step 1 — Set up Supabase (PostgreSQL)

1. Go to [supabase.com](https://supabase.com) → **New Project**
2. Choose a region close to you (e.g. South Asia)
3. Set a strong database password — **save it**
4. After the project loads → **Settings → Database**
5. Copy the **Connection String** (URI format) — looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres
   ```
6. Save this as your `DATABASE_URL`

---

### Step 2 — Set up Upstash (Redis)

1. Go to [upstash.com](https://upstash.com) → **Create Database**
2. Choose **Redis** → Region: same as Supabase
3. After creation → copy the **Redis URL** — looks like:
   ```
   rediss://default:xxxx@xxxx.upstash.io:6379
   ```
4. Save this as your `REDIS_URL`

---

### Step 3 — Deploy Backend on Railway

1. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
2. Select your PharmaChain repository
3. Set **Root Directory** to `backend`
4. Railway will auto-detect FastAPI — set the **Start Command** to:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
5. Go to **Variables** tab and add ALL your environment variables:

   ```
   DATABASE_URL          = (from Supabase Step 1)
   REDIS_URL             = (from Upstash Step 2)
   SECRET_KEY            = (generate: python -c "import secrets; print(secrets.token_hex(32))")
   ENVIRONMENT           = production
   PUBLIC_APP_URL        = https://your-vercel-app.vercel.app
   API_BASE_URL          = https://your-railway-app.railway.app
   ALLOWED_ORIGINS       = https://your-vercel-app.vercel.app
   ETHEREUM_RPC_URL      = (your Alchemy Sepolia URL)
   ETHEREUM_PRIVATE_KEY  = (your wallet private key)
   CONTRACT_ADDRESS      = (your deployed contract address)
   NEWS_API_KEY          = (your NewsAPI key)
   MAPBOX_TOKEN          = (your Mapbox token)
   GEMINI_API_KEY        = (your Gemini API key)
   ```

6. After deploy → go to **Settings → Domains** → copy your Railway URL (e.g. `https://pharmachain-backend.railway.app`)
7. Run Alembic migrations using Railway's **one-off command** feature:
   ```
   alembic upgrade head
   ```

---

### Step 4 — Deploy Frontend on Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New Project → Import from GitHub**
2. Select your repo → set **Root Directory** to `frontend`
3. Framework preset: **Vite**
4. Go to **Environment Variables** and add:
   ```
   VITE_API_URL        = https://your-railway-app.railway.app
   VITE_MAPBOX_TOKEN   = (your Mapbox public token)
   ```
5. Click **Deploy** — Vercel handles everything automatically
6. After deploy → copy your Vercel URL (e.g. `https://pharmachain.vercel.app`)
7. Go back to **Railway → Variables** and update:
   ```
   PUBLIC_APP_URL  = https://pharmachain.vercel.app
   ALLOWED_ORIGINS = https://pharmachain.vercel.app
   ```

---

### Step 5 — Verify Everything Works

Visit your Vercel URL and test end-to-end:

- [ ] `https://your-railway-app.railway.app/health` returns `{"status": "ok"}`
- [ ] Login works with demo accounts
- [ ] Manufacturer can create a batch
- [ ] Supplier can verify a shipment (AI fires)
- [ ] Hospital can confirm receipt (full 3-party verification)
- [ ] Blockchain hash appears on the public shipment page
- [ ] Gemini AI report appears on FLAGGED shipments

---

### 💡 Tips

- **CORS error?** Make sure `ALLOWED_ORIGINS` in Railway exactly matches your Vercel URL (no trailing slash)
- **DB connection error?** Supabase requires SSL — add `?sslmode=require` to the end of your `DATABASE_URL`
- **Blockchain in mock mode?** Leave `ETHEREUM_PRIVATE_KEY` and `CONTRACT_ADDRESS` empty — the app will still work, just without real on-chain records
- **Free tier limits:** Railway free tier sleeps after inactivity — upgrade to Hobby ($5/mo) for always-on

---

## 👨‍💻 Builder

Built by a **first-year B.Tech CS student at UEM Kolkata (Class of 2029)** as a hackathon MVP and internship portfolio project.

---


## 📄 License

MIT License — feel free to use, modify, and distribute.

---

*PharmaChain — Pharmaceutical supply chain integrity for the other 6 billion.*

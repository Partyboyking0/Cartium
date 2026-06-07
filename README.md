# Cartium Clone

Cartium is a modular e-commerce clone built with React + Vite and a FastAPI backend. It now implements the core buyer, seller, admin, checkout, review, and assistant flows described for the project while keeping the frontend split into pages/components and the backend split into routers/services.

## Implemented Features

### Buyer

- login, signup, logout, and demo Google OAuth role selection
- product listing with categories, search, price/rating filters through the API
- product detail page with gallery, specs, wishlist action, reviews, and ratings
- backend cart for logged-in users, with local guest-cart fallback
- checkout with address and payment step before placing the order
- payment modes: COD, UPI, card, Razorpay, Stripe, PayPal demo modes
- order history and tracking: placed, packed, shipped, delivered
- one-click reorder
- account profile, multiple addresses, saved payment methods
- wishlist and recently viewed products
- AI shopping assistant with persistent history for logged-in users and local fallback for guests

### Seller

- seller dashboard with revenue, orders count, units sold, low-stock alerts, and top products
- add product, edit product, delete product APIs
- image URL upload support through product forms/API payloads
- set price, MRP, stock, discount through price/MRP, and low-stock threshold
- auto out-of-stock visibility through stock values
- view orders for seller products
- update order item status: placed, packed, shipped, delivered
- see reviews and respond to customer reviews

### Admin

- admin dashboard with users, products, orders, payments, complaints, fraud flags, and growth stats
- view all users
- ban or activate users
- assign buyer, seller, or admin roles
- approve, reject, or suspend sellers through user moderation
- approve/reject product listings
- remove products
- platform analytics: revenue, users, orders, growth stats
- payment transaction monitoring and refund status updates
- complaint handling and fraud flag visibility

## Stack

- Frontend: React + Vite
- Backend API: FastAPI + SQLAlchemy
- Database: MySQL, including Railway MySQL support
- Deployment: Render backend blueprint in `render.yaml`

## Project Structure

```text
backend/
  app/
    core/config.py
    dependencies/auth.py
    routers/
      account.py
      admin.py
      ai.py
      auth.py
      cart.py
      catalog.py
      health.py
      orders.py
      reviews.py
      seller.py
    services/
      catalog_service.py
      commerce.py
    database.py
    main.py
    models.py
    schemas.py
    seed.py
frontend/
  src/
    components/
    pages/
    utils/
    App.jsx
    api.js
    styles.css
```

## Demo Accounts

- Buyer: `aarav.buyer@example.com` / `password123`
- Seller: `seller@example.com` / `seller123`
- Admin: `admin@cartium.com` / `admin123`

Run the seeder after changing database settings so these accounts and the demo data exist.

## Environment

Create `backend/.env` from `backend/.env.example`.

Common local MySQL example:

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/cartium_clone
APP_ENV=development
DEBUG=false
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Railway MySQL on Render example:

```env
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:PORT/DATABASE
APP_ENV=production
DEBUG=false
CORS_ALLOW_ORIGINS=https://your-frontend-domain.vercel.app,http://localhost:5173,http://127.0.0.1:5173
```

If Railway gives you `mysql://...`, the backend also normalizes it to `mysql+pymysql://...`.

## Local Run

Install backend dependencies:

```powershell
python -m pip install -r backend\requirements.txt
```

Seed MySQL:

```powershell
python -m backend.app.seed
```

Start backend from the repo root:

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Start frontend:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173/
```

## API Surface

- `GET /api/health`
- `GET /api/products`
- `GET /api/products/{id}`
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/oauth`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `GET/POST/PATCH/DELETE /api/cart`
- `GET/PATCH /api/account/profile`
- `GET/POST/PATCH/DELETE /api/account/addresses`
- `GET/POST/DELETE /api/account/payment-methods`
- `GET/POST /api/account/wishlist`
- `GET /api/account/recently-viewed`
- `POST /api/orders/checkout`
- `GET /api/orders`
- `POST /api/orders/{id}/reorder`
- `POST /api/orders/complaints`
- `GET /api/reviews/product/{id}`
- `POST /api/reviews`
- `GET/POST/DELETE /api/ai/history`
- `POST /api/ai/chat`
- `GET /api/seller/dashboard`
- `POST/PATCH/DELETE /api/seller/products`
- `PATCH /api/seller/orders/items/{id}/status`
- `POST /api/seller/reviews/{id}/response`
- `GET /api/admin/dashboard`
- `PATCH /api/admin/users/{id}`
- `PATCH /api/admin/products/{id}/moderation`
- `DELETE /api/admin/products/{id}`
- `PATCH /api/admin/transactions/{id}/refund`
- `PATCH /api/admin/complaints/{id}`

## Verification

Latest checks performed:

- `python -m compileall backend`
- FastAPI import check
- `GET /api/health` -> `200`
- `GET /api/products` -> `200` with 24 products
- `GET /api/products/1` -> `200`
- `npm run build`

Database-backed auth, checkout, seller, and admin routes require MySQL tables to be seeded with `python -m backend.app.seed`.


## Cartium AI Assistant Setup

Cartium includes a FastAPI AI assistant with three layers: prompt personalization, ChromaDB RAG, and backend actions for catalog, cart, and order workflows.

### Install AI dependencies

Add this to `backend/.env`:

```env
HUGGINGFACE_API_KEY=hf_your_token_here
AI_MODEL_NAME=microsoft/Phi-3-mini-4k-instruct
```

Then install dependencies:

```bash
python -m pip install -r backend/requirements.txt
```

Cartium uses the Hugging Face Inference Providers API for `microsoft/Phi-3-mini-4k-instruct`, so the model is not downloaded locally. Set `HUGGINGFACE_API_KEY` in `backend/.env` locally or in your Render environment variables. If the API or Chroma dependencies are unavailable, the assistant falls back to database-backed product, cart, and order actions.

### Ingest the knowledge base

Start the backend, then run:

```bash
curl -X POST http://127.0.0.1:8000/api/ai/ingest
```

This stores approved products, FAQs, and policies in `backend/chroma_db`.

### Chat endpoint

Authenticated frontend requests should call:

```http
POST /api/ai/chat
{
  "user_id": "user_001",
  "message": "Suggest sneakers under Rs 2000"
}
```

Response:

```json
{
  "reply": "...",
  "intent": "product_search",
  "sources": []
}
```

Health check:

```http
GET /api/ai/health
```

# Cartium AI Powered E-Commerce Platform

Cartium is a full-stack e-commerce platform built with React, FastAPI, MySQL, Razorpay, Google OAuth, and an AI shopping assistant powered by Hugging Face hosted inference.

The app supports buyer, seller, and admin workflows with product discovery, multi-cart shopping, secure checkout, order tracking, seller inventory tools, admin moderation, and AI-assisted shopping.

## Tech Stack

- Frontend: React + Vite
- Backend: FastAPI + SQLAlchemy
- Database: MySQL, with Railway MySQL support
- Payments: Razorpay
- Authentication: Email/password auth and Google OAuth
- AI Assistant: Hugging Face API, ChromaDB RAG, sentence-transformers embeddings
- Deployment: Vercel for frontend, Render for backend, Railway for MySQL

## Main Features

### Buyer

- Signup, login, logout, and Google OAuth
- Role-based buyer/seller onboarding for OAuth users
- Product catalog with categories, search, price filters, rating filters, and product details
- Wishlist and recently viewed products
- Multiple carts per user with create, rename, switch, delete, and active cart selection
- Razorpay-only checkout with address capture before payment
- Order history and tracking: Placed, Packed, Shipped, Delivered
- One-click reorder
- Profile, saved addresses, and saved payment method UI
- Product reviews and ratings
- AI shopping assistant with persistent chat history

### Seller

- Seller dashboard with revenue, orders, units sold, low-stock alerts, and top products
- Add, edit, and delete product listings
- Upload product image URLs
- Set price, MRP, stock, category, discount, and low-stock threshold
- Inventory tracking and out-of-stock handling
- View orders for seller products
- Update item status: Packed, Shipped, Delivered
- View customer reviews and respond to reviews

### Admin

- Admin dashboard for users, sellers, products, orders, payments, complaints, and fraud flags
- View users and activate/ban accounts
- Assign roles: buyer, seller, admin
- Approve, reject, or suspend sellers
- Approve/reject product listings
- Remove inappropriate products
- Platform analytics: users, orders, revenue, growth stats
- Payment transaction monitoring and refund status updates
- Complaint handling and fraud flag review

### AI Assistant

- Personalized prompt layer for Cartium tone and user context
- ChromaDB RAG over products, FAQs, and policies
- Backend actions for product search, product comparison, stock checks, cart actions, order status, payment help, and policies
- Hugging Face hosted model support using `microsoft/Phi-3-mini-4k-instruct`
- Fallback to grounded database answers for product, cart, order, and payment flows

## Project Structure

```text
backend/
  app/
    ai/
      chatbot_service.py
      intent.py
      model_loader.py
      prompts.py
      rag.py
    core/
      config.py
    dependencies/
      auth.py
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
      user_personalization_service.py
    database.py
    main.py
    models.py
    schemas.py
    seed.py
  data/
    faqs.json
    policies.txt
    users.json
  chroma_db/
  requirements.txt
frontend/
  src/
    components/
    pages/
    utils/
    App.jsx
    api.js
    styles.css
```

## Local Requirements

Recommended versions:

- Python 3.11 or 3.12
- Node.js 18+
- MySQL 8+ or Railway MySQL

Avoid Python 3.14 for this project because some backend packages may require native wheel builds that are not always available yet.

## Backend Environment

Create `backend/.env` from `backend/.env.example`.

Local MySQL example:

```env
APP_ENV=development
DEBUG=false
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/cartium
CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

GOOGLE_CLIENT_ID=your_google_client_id
RAZORPAY_KEY_ID=rzp_test_or_live_key
RAZORPAY_KEY_SECRET=your_razorpay_secret

HUGGINGFACE_API_KEY=hf_your_token_here
AI_MODEL_NAME=microsoft/Phi-3-mini-4k-instruct
HUGGINGFACE_CHAT_URL=https://router.huggingface.co/featherless-ai/v1/completions
HUGGINGFACE_TIMEOUT_SECONDS=90
```

Railway MySQL example for Render:

```env
APP_ENV=production
DEBUG=false
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:PORT/DATABASE
CORS_ALLOW_ORIGINS=https://your-frontend-domain.vercel.app

GOOGLE_CLIENT_ID=your_google_client_id
RAZORPAY_KEY_ID=rzp_live_or_test_key
RAZORPAY_KEY_SECRET=your_razorpay_secret

HUGGINGFACE_API_KEY=hf_your_token_here
AI_MODEL_NAME=microsoft/Phi-3-mini-4k-instruct
HUGGINGFACE_CHAT_URL=https://router.huggingface.co/featherless-ai/v1/completions
```

If Railway gives a `mysql://...` URL, the backend normalizes it to `mysql+pymysql://...`.

## Frontend Environment

Create `frontend/.env` from `frontend/.env.example`.

Local example:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_GOOGLE_CLIENT_ID=your_google_client_id
VITE_RAZORPAY_KEY_ID=rzp_test_or_live_key
```

Production example:

```env
VITE_API_BASE_URL=https://your-render-backend.onrender.com
VITE_GOOGLE_CLIENT_ID=your_google_client_id
VITE_RAZORPAY_KEY_ID=rzp_live_or_test_key
```

Never put backend secrets such as `RAZORPAY_KEY_SECRET` or `HUGGINGFACE_API_KEY` in frontend env files.

## Install And Run Locally

From the project root:

```powershell
python -m pip install -r backend\requirements.txt
```

Create database tables and seed products/accounts:

```powershell
python -m backend.app.seed
```

Start backend:

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Start frontend in a second terminal:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173/
```

## AI Knowledge Base Setup

The AI assistant uses ChromaDB for retrieved product and policy context.

After the backend is running, ingest the knowledge base:

```powershell
curl -X POST http://127.0.0.1:8000/api/ai/ingest
```

Successful response:

```json
{
  "message": "Cartium AI knowledge base ingested successfully",
  "counts": {
    "products": 24,
    "faqs": 4,
    "policies": 5
  }
}
```

AI health check:

```powershell
curl http://127.0.0.1:8000/api/ai/health
```

Direct chat endpoint:

```http
POST /api/ai/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Compare OnePlus Nord CE4 and Nothing Phone 2a"
}
```

## Seeded Local Accounts

These accounts are created by the seeder for local testing:

- Buyer: `aarav.buyer@example.com` / `password123`
- Seller: `seller@example.com` / `seller123`
- Admin: `admin@cartium.com` / `admin123`

Change these credentials before using the app outside local development.

## Important API Endpoints

### Health And Catalog

- `GET /api/health`
- `GET /api/products`
- `GET /api/products/{id}`

### Auth

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/oauth`
- `GET /api/auth/me`
- `POST /api/auth/logout`

### Cart And Checkout

- `GET /api/cart`
- `POST /api/cart`
- `PATCH /api/cart/{item_id}`
- `DELETE /api/cart/{item_id}`
- `GET /api/cart/carts`
- `POST /api/cart/carts`
- `PATCH /api/cart/carts/{cart_id}`
- `PATCH /api/cart/carts/{cart_id}/activate`
- `DELETE /api/cart/carts/{cart_id}`
- `POST /api/orders/razorpay/create`
- `POST /api/orders/razorpay/verify`
- `GET /api/orders`
- `POST /api/orders/{id}/reorder`

### Account

- `GET /api/account/profile`
- `PATCH /api/account/profile`
- `GET /api/account/addresses`
- `POST /api/account/addresses`
- `PATCH /api/account/addresses/{id}`
- `DELETE /api/account/addresses/{id}`
- `GET /api/account/wishlist`
- `POST /api/account/wishlist`
- `DELETE /api/account/wishlist/{product_id}`
- `GET /api/account/recently-viewed`

### Reviews

- `GET /api/reviews/product/{id}`
- `POST /api/reviews`

### AI

- `GET /api/ai/health`
- `POST /api/ai/ingest`
- `POST /api/ai/chat`
- `GET /api/ai/history`
- `DELETE /api/ai/history`

### Seller

- `GET /api/seller/dashboard`
- `POST /api/seller/products`
- `PATCH /api/seller/products/{id}`
- `DELETE /api/seller/products/{id}`
- `PATCH /api/seller/orders/items/{id}/status`
- `POST /api/seller/reviews/{id}/response`

### Admin

- `GET /api/admin/dashboard`
- `PATCH /api/admin/users/{id}`
- `PATCH /api/admin/products/{id}/moderation`
- `DELETE /api/admin/products/{id}`
- `PATCH /api/admin/transactions/{id}/refund`
- `PATCH /api/admin/complaints/{id}`

## Deployment Notes

Recommended deployment split:

- Frontend: Vercel
- Backend: Render
- Database: Railway MySQL

Backend build/start on Render:

```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Set Render root directory to the repository root unless your Render service is configured differently.

Add all backend environment variables in Render's Environment panel. Do not commit real `.env` files.

Frontend build on Vercel:

```bash
cd frontend
npm install
npm run build
```

Set Vercel output directory to:

```text
frontend/dist
```

## Verification Checklist

Run these before deployment:

```powershell
python -m compileall backend\app
cd frontend
npm run build
```

Then verify locally:

- `GET http://127.0.0.1:8000/api/health` returns `ok`
- `GET http://127.0.0.1:8000/api/products` returns products
- `POST http://127.0.0.1:8000/api/ai/ingest` ingests products, FAQs, and policies
- Login works with a seeded account
- Razorpay checkout opens and verifies payment
- AI chat answers product, payment, cart, and order questions without leaking prompt context

## Security Notes

- Keep `backend/.env` private.
- Keep `frontend/.env` free of secrets.
- Use HTTPS domains in production CORS settings.
- Rotate seeded local passwords before production use.
- Use Razorpay live keys only after full checkout testing.

# RentWise — Smart Real Estate Platform

Full-stack real estate rental platform with AI-powered price estimation, real-time chat, Stripe payments, and role-based dashboards for Tenants, Landlords, and Admins.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0 async |
| Frontend | React 18, Vite, Tailwind CSS, Zustand |
| SQL Database | PostgreSQL 15+ (24 tables) |
| NoSQL Database | MongoDB 6+ (Motor async) |
| Real-Time | Socket.IO (python-socketio) |
| ML | scikit-learn (GradientBoostingRegressor) |
| Auth | JWT (access + refresh tokens) |
| Payments | Stripe Payment Intents |

---

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- MongoDB 6+

---

## Backend Setup

```bash
cd backend

# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, MONGO_URI, SECRET_KEY, STRIPE keys

# 4. Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE rentwise_db;"

# 5. Run migrations (creates all 24 tables)
alembic upgrade head

# 6. Train the ML model (run once)
python -m app.ml.train

# 7. Start the server
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

## Frontend Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.example .env.local
# Set VITE_STRIPE_PUBLIC_KEY=pk_test_...

# 3. Start dev server
npm run dev
```

App available at: http://localhost:5173

---

## Stripe Webhook (local testing)

```bash
# Install Stripe CLI, then:
stripe listen --forward-to localhost:8000/api/payments/webhook
# Copy the webhook secret into .env as STRIPE_WEBHOOK_SECRET
```

---

## Data

RentWise uses **real US rental data** — the UCI *Apartment for Rent Classified* dataset
(see `backend/app/ml/data/apartments.csv`). The price model and the seeded listings are
both derived from it by `backend/app/ml/prepare_real_data.py` (no synthetic data). As a
result: cities are real US "City, ST" entries, prices are in **USD ($)**, and the
`size_m2` column carries **square feet** (the UI is labeled "sq ft").

> The companion standalone project in [`machine_learning/`](machine_learning/) explores
> the same dataset (classification + clustering) and is self-contained.

## Seeding Initial Data

After running migrations, seed roles and amenities, then run the generated seed files
(cities + real listings come from `seed_all.sql`):

```sql
-- 1) roles + amenities (generic)
INSERT INTO roles (name, description) VALUES
  ('admin',    'Full platform access'),
  ('landlord', 'Create and manage properties'),
  ('tenant',   'Search and rent properties');

INSERT INTO amenities (name, icon) VALUES
  ('WiFi', 'wifi'), ('Parking', 'car'), ('Air Conditioning', 'wind'),
  ('Gym', 'dumbbell'), ('Pool', 'droplet'), ('Balcony', 'home'),
  ('Dishwasher', 'layers'), ('Washing Machine', 'rotate-cw'),
  ('Elevator', 'arrow-up'), ('Security', 'shield');
```

```bash
# 2) regenerate seed + model from the real data (optional — committed copies exist)
cd backend && python -m app.ml.prepare_real_data   # writes seed_all.sql + seed_neighborhoods.sql
python -m app.ml.train                             # writes app/ml/model.pkl

# 3) load real US cities + listings, then neighborhoods (in psql)
\i 'backend/seed_all.sql'
\i 'backend/seed_neighborhoods.sql'
```

---

## Project Structure

```
Lab2/
├── backend/
│   ├── app/
│   │   ├── core/          # config, security, dependencies
│   │   ├── db/            # SQLAlchemy engine, Motor client, Base
│   │   ├── models/        # ORM models (24 tables across 3 files)
│   │   ├── schemas/       # Pydantic v2 schemas per domain
│   │   ├── repositories/  # Abstract base + concrete DB access
│   │   ├── services/      # Business logic per domain
│   │   ├── routers/       # FastAPI route handlers
│   │   ├── ml/            # Training script + predictor
│   │   └── websockets/    # Socket.IO event handlers
│   ├── alembic/           # DB migrations
│   ├── main.py
│   └── requirements.txt
└── frontend/
    └── src/
        ├── api/           # Axios + per-domain API modules
        ├── store/         # Zustand stores
        ├── hooks/         # useAuth, useSocket, usePriceEstimate
        ├── layouts/       # AuthLayout, DashboardLayout
        ├── pages/         # Route-level components (lazy loaded)
        └── components/    # Shared UI + heavy lazy-loaded components
```

---

## ERD (dbdiagram.io)

```
Table users {
  id int [pk, increment]
  first_name varchar(100)
  last_name varchar(100)
  email varchar(255) [unique]
  password_hash varchar(255)
  is_active bool
  created_by int [ref: > users.id]
  updated_by int [ref: > users.id]
  created_at timestamp
  updated_at timestamp
}

Table roles { id int [pk]; name varchar(50) [unique]; description text; created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table user_roles { id int [pk]; user_id int [ref: > users.id]; role_id int [ref: > roles.id]; assigned_at timestamp; created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table permissions { id int [pk]; name varchar(100) [unique]; description text; created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table role_permissions { id int [pk]; role_id int [ref: > roles.id]; permission_id int [ref: > permissions.id]; created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table refresh_tokens { id int [pk]; user_id int [ref: > users.id]; token_hash varchar(255) [unique]; expires_at timestamp; revoked_at timestamp; created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table audit_logs { id int [pk]; user_id int [ref: > users.id]; action varchar(100); entity varchar(100); entity_id int; old_value text; new_value text; ip_address varchar(45); created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table notifications { id int [pk]; user_id int [ref: > users.id]; type varchar(50); title varchar(255); message text; is_read bool; created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table settings { id int [pk]; key varchar(100) [unique]; value text; description text; created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table files { id int [pk]; entity varchar(100); entity_id int; filename varchar(255); file_path varchar(500); file_size bigint; uploaded_by int [ref: > users.id]; created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }

Table cities { id int [pk]; name varchar(100); country varchar(100); created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table neighborhoods { id int [pk]; city_id int [ref: > cities.id]; name varchar(100); latitude float; longitude float; created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table amenities { id int [pk]; name varchar(100) [unique]; icon varchar(100); created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }

Table properties {
  id int [pk, increment]
  landlord_id int [ref: > users.id]
  title varchar(255)
  description text
  price decimal(10,2)
  city_id int [ref: > cities.id]
  neighborhood_id int [ref: > neighborhoods.id]
  size_m2 decimal(8,2)
  num_rooms int
  num_bathrooms int
  is_furnished bool
  is_pet_friendly bool
  status varchar(20)
  created_by int [ref: > users.id]
  updated_by int [ref: > users.id]
  created_at timestamp
  updated_at timestamp
}

Table property_images { id int [pk]; property_id int [ref: > properties.id]; file_id int [ref: > files.id]; is_primary bool; created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table property_amenities { id int [pk]; property_id int [ref: > properties.id]; amenity_id int [ref: > amenities.id]; created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table viewing_bookings { id int [pk]; property_id int [ref: > properties.id]; tenant_id int [ref: > users.id]; scheduled_at timestamp; status varchar(20); notes text; created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table rental_applications { id int [pk]; property_id int [ref: > properties.id]; tenant_id int [ref: > users.id]; message text; status varchar(20); created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table lease_contracts { id int [pk]; property_id int [ref: > properties.id]; tenant_id int [ref: > users.id]; landlord_id int [ref: > users.id]; start_date date; end_date date; monthly_rent decimal(10,2); deposit_amount decimal(10,2); status varchar(20); created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table payments { id int [pk]; lease_id int [ref: > lease_contracts.id]; tenant_id int [ref: > users.id]; amount decimal(10,2); stripe_payment_id varchar(255) [unique]; type varchar(30); status varchar(20); created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table reviews { id int [pk]; property_id int [ref: > properties.id]; tenant_id int [ref: > users.id]; rating int; comment text; created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table saved_properties { id int [pk]; tenant_id int [ref: > users.id]; property_id int [ref: > properties.id]; saved_at timestamp; created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table price_estimation_logs { id int [pk]; property_id int [ref: > properties.id]; user_id int [ref: > users.id]; input_features json; predicted_price decimal(10,2); created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
Table maintenance_requests { id int [pk]; property_id int [ref: > properties.id]; tenant_id int [ref: > users.id]; title varchar(255); description text; priority varchar(20); status varchar(20); created_by int [ref: > users.id]; updated_by int [ref: > users.id]; created_at timestamp; updated_at timestamp }
```

Paste this at [dbdiagram.io](https://dbdiagram.io) to render the full ERD.

---

## Git Workflow

```bash
git init
git checkout -b feature/auth
# ... commit auth work ...
git checkout -b feature/property-crud
git checkout -b feature/ml-estimator
git checkout -b feature/payments
git checkout -b feature/realtime
```

## Environment Variables Reference

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL async URL (`postgresql+asyncpg://...`) |
| `MONGO_URI` | MongoDB connection string |
| `MONGO_DB_NAME` | MongoDB database name |
| `SECRET_KEY` | JWT signing key (use `openssl rand -hex 32`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL (default: 15) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL (default: 7) |
| `STRIPE_SECRET_KEY` | Stripe secret key (`sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret (`whsec_...`) |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins |
| `VITE_STRIPE_PUBLIC_KEY` | Stripe publishable key for frontend |

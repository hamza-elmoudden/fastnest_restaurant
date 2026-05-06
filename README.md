# 🍽️ Restaurant Booking API

A modular, production-ready REST API for restaurant table booking, built with **FastNest** (Python NestJS-style framework), **FastAPI**, **PostgreSQL**, and **WebSockets**.

---

## 📁 Project Structure

```
restaurant/
├── main.py                          # Entry point, CORS, error handlers
├── app_module.py                    # Root module
│
├── shared/                          # Cross-cutting concerns
│   ├── jwt.py                       # JWT sign, verify, token generation
│   ├── guards.py                    # JwtGuard
│   ├── interceptors.py              # LogInterceptor
│   └── decorators.py               # CurrentUser param decorator
│
├── config/
│   ├── config_service.py            # Reads env variables
│   └── config_module.py            # Global config module
│
├── database/
│   ├── database_service.py          # asyncpg connection pool, fetch/execute
│   └── database_module.py
│
├── auth/
│   ├── auth_dto.py                  # RegisterDto, LoginDto, RefreshDto
│   ├── auth_service.py              # Register, login, refresh, logout, me
│   ├── auth_controller.py           # POST /auth/register|login|refresh|logout, GET /auth/me
│   └── auth_module.py
│
├── tables/
│   ├── tables_dto.py                # UpdateTableDto
│   ├── tables_service.py            # find_all, find_one, update
│   ├── tables_controller.py         # GET /tables, GET /tables/:id, PATCH /tables/:id
│   └── tables_module.py
│
├── plates/
│   ├── plates_dto.py                # CreatePlateDto
│   ├── plates_service.py            # find_all, find_one, create, toggle_availability
│   ├── plates_controller.py         # GET /plates, POST /plates, PATCH /plates/:id/toggle
│   └── plates_module.py
│
├── notifications/
│   ├── notifications_service.py     # WebSocket room manager, auto-activation scheduler
│   └── notifications_module.py
│
├── bookings/
│   ├── bookings_dto.py              # CreateBookingDto
│   ├── bookings_service.py          # create, find_all, activate, cancel, complete
│   ├── bookings_controller.py       # Full CRUD + lifecycle endpoints
│   └── bookings_module.py
│
└── gateway/
    └── booking_gateway.py           # WebSocket gateway /ws/bookings
```

---

## ⚙️ Requirements

- Python 3.10+
- PostgreSQL 14+
- pip packages:

```bash
pip install fastnest asyncpg aiohttp uvicorn fastapi pydantic
```

---

## 🚀 Getting Started

### 1. Clone & set up environment

```bash
git clone <your-repo>
cd restaurant
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install fastnest asyncpg aiohttp uvicorn fastapi pydantic
```

### 2. Create the database

```bash
psql -U postgres -c "CREATE DATABASE restaurant_db;"
psql -U postgres -d restaurant_db -f schema.sql
```

### 3. Configure environment variables

Create a `.env` file or export directly:

```bash
export DB_URL=postgresql://postgres:your_password@localhost/restaurant_db
export JWT_SECRET=your-jwt-secret
export REFRESH_SECRET=your-refresh-secret
```

### 4. Run the server

```bash
uvicorn main:app --reload
```

Server starts at: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

---

## 🔐 Authentication

All protected routes require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens expire in **15 minutes**. Use the refresh endpoint to get a new one.

### Roles

| Role    | Permissions                              |
|---------|------------------------------------------|
| `user`  | Book tables, view own bookings, cancel own bookings |
| `staff` | All user permissions + activate/complete bookings, update tables |
| `admin` | All staff permissions + manage plates    |

---

## 📡 API Endpoints

### Auth — `/auth`

| Method | Endpoint          | Auth | Description             |
|--------|-------------------|------|-------------------------|
| POST   | `/auth/register`  | ❌   | Create a new account    |
| POST   | `/auth/login`     | ❌   | Login, returns tokens   |
| POST   | `/auth/refresh`   | ❌   | Refresh access token    |
| POST   | `/auth/logout`    | ❌   | Invalidate refresh token|
| GET    | `/auth/me`        | ✅   | Get current user info   |

**Register body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "secret123",
  "phone": "+1234567890"
}
```

**Login body:**
```json
{
  "email": "john@example.com",
  "password": "secret123"
}
```

**Login response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### Tables — `/tables`

| Method | Endpoint            | Auth         | Role          | Description         |
|--------|---------------------|--------------|---------------|---------------------|
| GET    | `/tables`           | ✅           | Any           | List all tables     |
| GET    | `/tables/:id`       | ✅           | Any           | Get single table    |
| PATCH  | `/tables/:id`       | ✅           | admin, staff  | Update table        |

**Query params for GET /tables:**
- `status` — filter by status: `available`, `occupied`, `maintenance`
- `location` — filter by location string

**PATCH body:**
```json
{
  "status": "available",
  "capacity": 4,
  "location": "terrace"
}
```

---

### Plates — `/plates`

| Method | Endpoint                  | Auth | Role         | Description            |
|--------|---------------------------|------|--------------|------------------------|
| GET    | `/plates`                 | ❌   | —            | List all plates        |
| GET    | `/plates/:id`             | ❌   | —            | Get single plate       |
| POST   | `/plates`                 | ✅   | admin        | Create a plate         |
| PATCH  | `/plates/:id/toggle`      | ✅   | admin, staff | Toggle availability    |

**Query params for GET /plates:**
- `category` — `starter`, `main`, `dessert`, `drink`
- `available` — `true` or `false`

**POST body:**
```json
{
  "name": "Grilled Salmon",
  "description": "Fresh Atlantic salmon with herbs",
  "price": 24.99,
  "category": "main",
  "image_url": "https://example.com/salmon.jpg"
}
```

---

### Bookings — `/bookings`

| Method | Endpoint                        | Auth | Role         | Description                  |
|--------|---------------------------------|------|--------------|------------------------------|
| GET    | `/bookings`                     | ✅   | Any          | List bookings (own or all)   |
| GET    | `/bookings/:id`                 | ✅   | Any          | Get booking details          |
| POST   | `/bookings`                     | ✅   | Any          | Create a booking             |
| PATCH  | `/bookings/:id/activate`        | ✅   | admin, staff | Manually activate booking    |
| PATCH  | `/bookings/:id/complete`        | ✅   | admin, staff | Mark booking as completed    |
| DELETE | `/bookings/:id`                 | ✅   | Any          | Cancel a booking             |

**POST body:**
```json
{
  "table_id": "uuid-of-table",
  "booked_at": "2025-06-15T19:00:00",
  "guests": 3,
  "notes": "Window seat preferred",
  "plates": [
    { "plate_id": "uuid-of-plate", "quantity": 2, "note": "No onions" }
  ]
}
```

**Booking status lifecycle:**
```
pending ──► active ──► completed
   │
   └──► cancelled
```

> ⏱️ Bookings auto-activate after **3 minutes** via a background task and notify connected WebSocket clients.

---

## 🔌 WebSocket — `/ws/bookings`

Connect to receive real-time booking events.

### Join a booking room (customer)

```json
{
  "event": "join",
  "data": {
    "token": "<access_token>",
    "booking_id": "<booking-uuid>"
  }
}
```

### Join the admin room (staff/admin)

```json
{
  "event": "join:admin",
  "data": {
    "token": "<access_token>"
  }
}
```

### Heartbeat

```json
{ "event": "ping", "data": {} }
```

### Events received

| Event               | Sent to        | Description                        |
|---------------------|----------------|------------------------------------|
| `connected`         | Client         | Connection confirmed               |
| `joined`            | Client         | Successfully joined booking room   |
| `joined:admin`      | Staff/Admin    | Successfully joined admin room     |
| `booking:created`   | Admin room     | New booking was made               |
| `booking:activated` | Both rooms     | Booking is now active              |
| `booking:cancelled` | Both rooms     | Booking was cancelled              |
| `booking:completed` | Both rooms     | Booking was completed              |
| `pong`              | Client         | Response to ping                   |
| `error`             | Client         | Auth or validation error           |

---

## 🛡️ Guards & Middleware

| Guard/Middleware  | Description                                      |
|-------------------|--------------------------------------------------|
| `JwtGuard`        | Validates Bearer token, attaches user to request |
| `RolesGuard`      | Checks `role` claim against `@Roles()` decorator |
| `LogInterceptor`  | Logs method, path, and response time (ms)        |
| `ValidationPipe`  | Validates and transforms request bodies via Pydantic |

---

## ❌ Error Responses

All errors follow a consistent structure:

```json
{
  "statusCode": 401,
  "message": "Invalid or expired token"
}
```

Validation errors (422):

```json
{
  "statusCode": 422,
  "message": "Validation failed",
  "errors": [
    { "field": "password", "message": "Min 6 characters" }
  ]
}
```

| Code | Meaning               |
|------|-----------------------|
| 400  | Bad Request           |
| 401  | Unauthorized          |
| 403  | Forbidden             |
| 404  | Not Found             |
| 409  | Conflict              |
| 422  | Validation Error      |

---

## 🧪 Quick Test with curl

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@test.com","password":"secret123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@test.com","password":"secret123"}'

# List tables (use token from login)
curl http://localhost:8000/tables \
  -H "Authorization: Bearer <access_token>"

# Create a booking
curl -X POST http://localhost:8000/bookings \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"table_id":"<table-uuid>","booked_at":"2025-06-15T19:00:00","guests":2}'
```

---

## 📝 License

MIT

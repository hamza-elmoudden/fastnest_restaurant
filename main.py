"""
main.py — Restaurant Booking API entry point

Setup:
    pip install fastnest asyncpg aiohttp

    psql -U postgres -c "CREATE DATABASE restaurant_db;"
    psql -U postgres -d restaurant_db -f schema.sql

    DB_URL=postgresql://postgres:password@localhost/restaurant_db \\
    JWT_SECRET=your-secret \\
    uvicorn main:app --reload
"""

from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from fastnest.core.factory import create_app
from app_module import AppModule


app = create_app(AppModule, debug=True, title="Restaurant Booking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = [
        {
            "field":   ".".join(str(x) for x in e["loc"] if x != "body"),
            "message": e["msg"],
        }
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"statusCode": 422, "message": "Validation failed", "errors": errors},
    )

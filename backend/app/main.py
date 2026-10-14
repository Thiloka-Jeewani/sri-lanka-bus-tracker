from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import math
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.environ.get("BUS_TRACKER_DB", ROOT / "data" / "buses.sqlite3"))
SESSION_DURATION = timedelta(hours=12)
STALE_AFTER_SECONDS = 90
PASSWORD_ITERATIONS = 310_000
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 900
EMAIL_PATTERN = re.compile(r"^[^@\s]{1,64}@[^@\s.]+(?:\.[^@\s.]+)+$")
VEHICLE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
SRI_LANKA_BOUNDS = {"minLat": 5.8, "maxLat": 10.1, "minLon": 79.5, "maxLon": 82.1}
ROUTES = [
    {
        "id": "colombo-fort-pettah",
        "name": "Colombo Fort – Pettah",
        "nameSi": "කොළඹ කොටුව – පිටකොටුව",
        "nameTa": "கொழும்பு கோட்டை – புறக்கோட்டை",
        "demo": True,
        "stops": [
            {"name": "Colombo Fort", "lat": 6.9344, "lon": 79.8428},
            {"name": "Pettah", "lat": 6.9388, "lon": 79.8500},
        ],
    }
]

_login_attempts: dict[str, list[float]] = {}
_frontend_dist = ROOT / "frontend" / "dist"

app = FastAPI(title="Bus.lk API", version="1.0.0")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS vehicles (
                vehicle_id TEXT PRIMARY KEY,
                route_id TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                accuracy REAL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                name TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('passenger', 'driver', 'operator', 'authority', 'admin')),
                status TEXT NOT NULL CHECK (status IN ('pending', 'active', 'rejected', 'suspended')),
                organization TEXT,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                csrf_token TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS fleet (
                vehicle_id TEXT PRIMARY KEY,
                route_id TEXT NOT NULL,
                operator_id TEXT NOT NULL REFERENCES users(id),
                driver_id TEXT UNIQUE REFERENCES users(id),
                created_at TEXT NOT NULL
            );
            """
        )
    bootstrap_admin()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"{PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        iterations_text, salt_text, digest_text = encoded.split("$", 2)
        iterations = int(iterations_text)
        if iterations < 1 or iterations > 2_000_000:
            return False
        expected = bytes.fromhex(digest_text)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_text), iterations)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def public_user(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "role": row["role"],
        "status": row["status"],
        "organization": row["organization"],
        "createdAt": row["created_at"],
    }


def bootstrap_admin() -> None:
    email = os.environ.get("BUS_TRACKER_ADMIN_EMAIL", "").strip().casefold()
    password = os.environ.get("BUS_TRACKER_ADMIN_PASSWORD", "")
    if not email and not password:
        return
    if not email or not password or not EMAIL_PATTERN.fullmatch(email) or not 16 <= len(password) <= 128:
        raise RuntimeError("Set both BUS_TRACKER_ADMIN_EMAIL and BUS_TRACKER_ADMIN_PASSWORD (valid email; 16–128 character password).")
    with connect() as connection:
        if connection.execute("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1").fetchone():
            return
        if connection.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            raise RuntimeError("The bootstrap admin email is already registered as a non-admin account.")
        connection.execute(
            """
            INSERT INTO users (id, email, name, role, status, password_hash, created_at)
            VALUES (?, ?, ?, 'admin', 'active', ?, ?)
            """,
            (
                str(uuid.uuid4()),
                email,
                os.environ.get("BUS_TRACKER_ADMIN_NAME", "Platform administrator")[:80],
                hash_password(password),
                utc_now(),
            ),
        )


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegisterInput(InputModel):
    name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)
    role: Literal["passenger", "driver", "operator", "authority"]
    organization: str | None = Field(default=None, max_length=120)
    consent: bool

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Enter your name.")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().casefold()
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Enter a valid email address.")
        return value

    @field_validator("organization")
    @classmethod
    def validate_organization(cls, value: str | None) -> str | None:
        return value.strip() if value else None


class LoginInput(InputModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().casefold()


class AdminSetupInput(InputModel):
    name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=16, max_length=128)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Enter your name.")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().casefold()
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Enter a valid email address.")
        return value


class FleetInput(InputModel):
    vehicleId: str = Field(min_length=1, max_length=32)
    routeId: str

    @field_validator("vehicleId")
    @classmethod
    def validate_vehicle_id(cls, value: str) -> str:
        value = value.strip()
        if not VEHICLE_ID_PATTERN.fullmatch(value):
            raise ValueError("Vehicle ID must use 1–32 letters, numbers, underscores, or hyphens.")
        return value

    @field_validator("routeId")
    @classmethod
    def validate_route(cls, value: str) -> str:
        if value not in {route["id"] for route in ROUTES}:
            raise ValueError("Choose a valid route.")
        return value


class AssignmentInput(InputModel):
    email: str = Field(min_length=3, max_length=254)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().casefold()
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Enter a valid driver email address.")
        return value


class LocationInput(InputModel):
    lat: float
    lon: float
    accuracy: float | None = Field(default=None, ge=0, le=100_000)

    @field_validator("lat")
    @classmethod
    def validate_latitude(cls, value: float) -> float:
        if not math.isfinite(value) or not SRI_LANKA_BOUNDS["minLat"] <= value <= SRI_LANKA_BOUNDS["maxLat"]:
            raise ValueError("Latitude is outside Sri Lanka.")
        return value

    @field_validator("lon")
    @classmethod
    def validate_longitude(cls, value: float) -> float:
        if not math.isfinite(value) or not SRI_LANKA_BOUNDS["minLon"] <= value <= SRI_LANKA_BOUNDS["maxLon"]:
            raise ValueError("Longitude is outside Sri Lanka.")
        return value

    @field_validator("accuracy")
    @classmethod
    def validate_accuracy(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError("Accuracy must be a finite number.")
        return value


class ReviewInput(InputModel):
    status: Literal["active", "rejected", "suspended"]


class AdminEmailInput(InputModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().casefold()
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("Enter a valid email address.")
        return value


def get_session(request: Request) -> tuple[dict, str, str] | None:
    token = request.cookies.get("buslk_session")
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with connect() as connection:
        row = connection.execute(
            """
            SELECT users.*, sessions.csrf_token, sessions.expires_at
            FROM sessions JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ?
            """,
            (token_hash,),
        ).fetchone()
    if not row or row["status"] != "active" or row["expires_at"] < utc_now():
        with connect() as connection:
            connection.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
        return None
    return public_user(row), row["csrf_token"], token


def current_session(request: Request) -> tuple[dict, str, str]:
    session = get_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="Sign in is required.")
    return session


def role_session(*roles: str):
    def dependency(
        request: Request,
        session: Annotated[tuple[dict, str, str], Depends(current_session)],
    ) -> tuple[dict, str, str]:
        if session[0]["role"] not in roles:
            raise HTTPException(status_code=403, detail="Your account role is not allowed to do this.")
        if not hmac.compare_digest(request.headers.get("X-CSRF-Token", ""), session[1]):
            raise HTTPException(status_code=403, detail="Security token is missing or invalid. Refresh and try again.")
        return session
    return dependency


def require_local_client(request: Request) -> None:
    try:
        if not ipaddress.ip_address(request.client.host).is_loopback:
            raise HTTPException(status_code=403, detail="First admin setup is only available on this computer.")
    except (ValueError, AttributeError):
        raise HTTPException(status_code=403, detail="First admin setup is only available on this computer.")


def assigned_vehicle(driver_id: str) -> sqlite3.Row | None:
    with connect() as connection:
        return connection.execute(
            """
            SELECT fleet.vehicle_id, fleet.route_id, fleet.operator_id
            FROM fleet
            JOIN users AS operators ON operators.id = fleet.operator_id
            WHERE fleet.driver_id = ? AND operators.status = 'active'
            """,
            (driver_id,),
        ).fetchone()


def public_vehicles() -> list[dict]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT vehicles.vehicle_id, vehicles.route_id, vehicles.lat, vehicles.lon,
                   vehicles.accuracy, vehicles.updated_at
            FROM vehicles
            JOIN fleet ON fleet.vehicle_id = vehicles.vehicle_id
            JOIN users AS operators ON operators.id = fleet.operator_id
            WHERE operators.status = 'active'
            """
        ).fetchall()
    now = datetime.now(timezone.utc)
    result = []
    for row in rows:
        age = max(0, int((now - datetime.fromisoformat(row["updated_at"])).total_seconds()))
        result.append({
            "vehicleId": row["vehicle_id"],
            "routeId": row["route_id"],
            "lat": row["lat"],
            "lon": row["lon"],
            "accuracy": row["accuracy"],
            "updatedAt": row["updated_at"],
            "ageSeconds": age,
            "status": "live" if age <= STALE_AFTER_SECONDS else "stale",
            "demo": True,
        })
    return result


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.middleware("http")
async def same_origin_writes(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if origin and urlparse(origin).netloc.casefold() != request.headers.get("host", "").casefold():
            return Response(
                content=json.dumps({"detail": "Cross-origin requests are not allowed."}),
                status_code=403,
                media_type="application/json",
            )
    return await call_next(request)


@app.get("/api/routes")
def get_routes():
    return {"routes": ROUTES}


@app.get("/api/vehicles")
def get_vehicles():
    return {"vehicles": public_vehicles()}


@app.get("/api/stream")
async def stream_vehicles():
    async def events():
        previous = None
        while True:
            snapshot = json.dumps({"vehicles": public_vehicles()}, separators=(",", ":"))
            if snapshot != previous:
                yield f"data: {snapshot}\n\n"
                previous = snapshot
            else:
                yield ": keep-alive\n\n"
            await __import__("asyncio").sleep(5)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )


@app.get("/api/auth/me")
def auth_me(request: Request):
    session = get_session(request)
    return {"user": session[0], "csrfToken": session[1]} if session else {"user": None}


@app.get("/api/auth/setup-status")
def setup_status(request: Request):
    require_local_client(request)
    with connect() as connection:
        available = connection.execute("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1").fetchone() is None
    return {"available": available}


def set_session_cookie(response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        "buslk_session",
        token,
        max_age=max_age,
        httponly=True,
        secure=os.environ.get("BUS_TRACKER_COOKIE_SECURE") == "1",
        samesite="strict",
        path="/",
    )


@app.post("/api/auth/register", status_code=201)
def register(body: RegisterInput):
    if not body.consent:
        raise HTTPException(status_code=400, detail="Please confirm that you understand the account and location-sharing terms.")
    organization = body.organization
    if body.role in {"operator", "authority"} and not organization:
        raise HTTPException(status_code=400, detail="Enter the organization or agency name for approval.")
    if body.role not in {"operator", "authority"}:
        organization = None
    user = {
        "id": str(uuid.uuid4()),
        "email": body.email,
        "name": body.name,
        "role": body.role,
        "status": "pending" if body.role in {"operator", "authority"} else "active",
        "organization": organization,
        "createdAt": utc_now(),
    }
    try:
        with connect() as connection:
            connection.execute(
                """
                INSERT INTO users (id, email, name, role, status, organization, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user["id"], user["email"], user["name"], user["role"], user["status"],
                 user["organization"], hash_password(body.password), user["createdAt"]),
            )
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from error
    return {"user": user}


@app.post("/api/auth/setup-admin", status_code=201)
def setup_admin(body: AdminSetupInput, request: Request, response: Response):
    require_local_client(request)
    if not EMAIL_PATTERN.fullmatch(body.email):
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    user_id = str(uuid.uuid4())
    created_at = utc_now()
    token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    with connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1").fetchone():
            raise HTTPException(status_code=409, detail="The admin account has already been set up.")
        try:
            connection.execute(
                """
                INSERT INTO users (id, email, name, role, status, password_hash, created_at)
                VALUES (?, ?, ?, 'admin', 'active', ?, ?)
                """,
                (user_id, body.email, body.name, hash_password(body.password), created_at),
            )
        except sqlite3.IntegrityError as error:
            raise HTTPException(status_code=409, detail="An account with this email already exists.") from error
        connection.execute(
            "INSERT INTO sessions (token_hash, user_id, csrf_token, expires_at) VALUES (?, ?, ?, ?)",
            (hashlib.sha256(token.encode()).hexdigest(), user_id, csrf_token,
             (datetime.now(timezone.utc) + SESSION_DURATION).isoformat(timespec="seconds")),
        )
    set_session_cookie(response, token, int(SESSION_DURATION.total_seconds()))
    return {"user": {
        "id": user_id, "email": body.email, "name": body.name, "role": "admin",
        "status": "active", "organization": None, "createdAt": created_at,
    }, "csrfToken": csrf_token}


@app.post("/api/auth/login")
def login(body: LoginInput, request: Request, response: Response):
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    attempts = [stamp for stamp in _login_attempts.get(client, []) if now - stamp < LOGIN_WINDOW_SECONDS]
    _login_attempts[client] = attempts
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many sign-in attempts. Wait 15 minutes and try again.")
    with connect() as connection:
        row = connection.execute("SELECT * FROM users WHERE email = ?", (body.email,)).fetchone()
    if not row or not verify_password(body.password, row["password_hash"]):
        attempts.append(now)
        _login_attempts[client] = attempts
        raise HTTPException(status_code=400, detail="Email or password is incorrect.")
    if row["status"] != "active":
        raise HTTPException(status_code=403, detail=f"Your {row['status']} account cannot sign in.")
    _login_attempts.pop(client, None)
    token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    with connect() as connection:
        connection.execute("DELETE FROM sessions WHERE expires_at < ?", (utc_now(),))
        connection.execute(
            "INSERT INTO sessions (token_hash, user_id, csrf_token, expires_at) VALUES (?, ?, ?, ?)",
            (hashlib.sha256(token.encode()).hexdigest(), row["id"], csrf_token,
             (datetime.now(timezone.utc) + SESSION_DURATION).isoformat(timespec="seconds")),
        )
    set_session_cookie(response, token, int(SESSION_DURATION.total_seconds()))
    return {"user": public_user(row), "csrfToken": csrf_token}


@app.post("/api/auth/logout")
def logout(
    response: Response,
    session: Annotated[tuple[dict, str, str], Depends(role_session("passenger", "driver", "operator", "authority", "admin"))],
):
    if session[0]["role"] == "driver":
        clear_driver_location(session[0]["id"])
    with connect() as connection:
        connection.execute("DELETE FROM sessions WHERE token_hash = ?", (hashlib.sha256(session[2].encode()).hexdigest(),))
    set_session_cookie(response, "", 0)
    return {"ok": True}


def clear_driver_location(driver_id: str) -> bool:
    vehicle = assigned_vehicle(driver_id)
    if not vehicle:
        return False
    with connect() as connection:
        cursor = connection.execute("DELETE FROM vehicles WHERE vehicle_id = ?", (vehicle["vehicle_id"],))
    return cursor.rowcount > 0


@app.get("/api/driver/vehicle")
def get_driver_vehicle(session: Annotated[tuple[dict, str, str], Depends(current_session)]):
    if session[0]["role"] != "driver":
        raise HTTPException(status_code=403, detail="Driver access is required.")
    vehicle = assigned_vehicle(session[0]["id"])
    return {"vehicle": {"vehicleId": vehicle["vehicle_id"], "routeId": vehicle["route_id"]} if vehicle else None}


@app.post("/api/locations", status_code=201)
def update_location(
    body: LocationInput,
    session: Annotated[tuple[dict, str, str], Depends(role_session("driver"))],
):
    vehicle = assigned_vehicle(session[0]["id"])
    if not vehicle:
        raise HTTPException(status_code=403, detail="Only a driver assigned to an operator-registered vehicle can share locations.")
    updated_at = utc_now()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO vehicles (vehicle_id, route_id, lat, lon, accuracy, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(vehicle_id) DO UPDATE SET
                route_id = excluded.route_id, lat = excluded.lat, lon = excluded.lon,
                accuracy = excluded.accuracy, updated_at = excluded.updated_at
            """,
            (vehicle["vehicle_id"], vehicle["route_id"], body.lat, body.lon, body.accuracy, updated_at),
        )
    return {"vehicle": {
        "vehicleId": vehicle["vehicle_id"], "routeId": vehicle["route_id"],
        "lat": body.lat, "lon": body.lon, "accuracy": body.accuracy,
        "updatedAt": updated_at, "demo": True,
    }}


@app.post("/api/driver/location/stop")
def stop_location(session: Annotated[tuple[dict, str, str], Depends(role_session("driver"))]):
    removed = clear_driver_location(session[0]["id"])
    return {"ok": True, "locationRemoved": removed}


@app.get("/api/operator/fleet")
def get_operator_fleet(session: Annotated[tuple[dict, str, str], Depends(current_session)]):
    if session[0]["role"] not in {"operator", "admin"}:
        raise HTTPException(status_code=403, detail="Operator access is required.")
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT fleet.vehicle_id, fleet.route_id, fleet.created_at,
                   users.id AS driver_id, users.name AS driver_name, users.email AS driver_email
            FROM fleet LEFT JOIN users ON users.id = fleet.driver_id
            WHERE fleet.operator_id = ? ORDER BY fleet.created_at
            """,
            (session[0]["id"],),
        ).fetchall()
    return {"vehicles": [{
        "vehicleId": row["vehicle_id"], "routeId": row["route_id"], "createdAt": row["created_at"],
        "driverId": row["driver_id"], "driverName": row["driver_name"], "driverEmail": row["driver_email"],
    } for row in rows]}


@app.post("/api/operator/fleet", status_code=201)
def create_fleet(
    body: FleetInput,
    session: Annotated[tuple[dict, str, str], Depends(role_session("operator", "admin"))],
):
    try:
        with connect() as connection:
            connection.execute(
                "INSERT INTO fleet (vehicle_id, route_id, operator_id, created_at) VALUES (?, ?, ?, ?)",
                (body.vehicleId, body.routeId, session[0]["id"], utc_now()),
            )
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="This vehicle ID is already registered.") from error
    return {"vehicle": {"vehicleId": body.vehicleId, "routeId": body.routeId}}


@app.post("/api/operator/fleet/{vehicle_id}/assign")
def assign_driver(
    vehicle_id: str,
    body: AssignmentInput,
    session: Annotated[tuple[dict, str, str], Depends(role_session("operator", "admin"))],
):
    with connect() as connection:
        fleet = connection.execute(
            "SELECT vehicle_id, driver_id FROM fleet WHERE vehicle_id = ? AND operator_id = ?",
            (vehicle_id, session[0]["id"]),
        ).fetchone()
        driver = connection.execute(
            "SELECT id FROM users WHERE email = ? AND role = 'driver' AND status = 'active'",
            (body.email,),
        ).fetchone()
        if not fleet:
            raise HTTPException(status_code=404, detail="Vehicle not found in your fleet.")
        if not driver:
            raise HTTPException(status_code=404, detail="No active driver account found for that email.")
        try:
            connection.execute("UPDATE fleet SET driver_id = ? WHERE vehicle_id = ?", (driver["id"], vehicle_id))
        except sqlite3.IntegrityError as error:
            raise HTTPException(status_code=409, detail="That driver is already assigned to another vehicle.") from error
        if fleet["driver_id"] and fleet["driver_id"] != driver["id"]:
            connection.execute("DELETE FROM vehicles WHERE vehicle_id = ?", (vehicle_id,))
    return {"ok": True}


def list_fleet_rows(connection: sqlite3.Connection) -> list[dict]:
    rows = connection.execute(
        """
        SELECT fleet.vehicle_id, fleet.route_id, fleet.created_at,
               operators.id AS operator_id, operators.name AS operator_name,
               operators.email AS operator_email, operators.organization,
               operators.status AS operator_status,
               drivers.id AS driver_id, drivers.name AS driver_name, drivers.email AS driver_email
        FROM fleet
        JOIN users AS operators ON operators.id = fleet.operator_id
        LEFT JOIN users AS drivers ON drivers.id = fleet.driver_id
        ORDER BY operators.organization, fleet.vehicle_id
        """
    ).fetchall()
    return [{
        "vehicleId": row["vehicle_id"], "routeId": row["route_id"], "createdAt": row["created_at"],
        "operatorId": row["operator_id"], "operatorName": row["operator_name"],
        "operatorEmail": row["operator_email"], "organization": row["organization"],
        "operatorStatus": row["operator_status"], "driverId": row["driver_id"],
        "driverName": row["driver_name"], "driverEmail": row["driver_email"],
    } for row in rows]


@app.get("/api/admin/users")
def admin_users(session: Annotated[tuple[dict, str, str], Depends(current_session)]):
    if session[0]["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access is required.")
    with connect() as connection:
        rows = connection.execute(
            "SELECT id, email, name, role, status, organization, created_at FROM users ORDER BY created_at"
        ).fetchall()
    return {"users": [public_user(row) for row in rows]}


@app.get("/api/admin/summary")
def admin_summary(session: Annotated[tuple[dict, str, str], Depends(current_session)]):
    if session[0]["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access is required.")
    live_since = (datetime.now(timezone.utc) - timedelta(seconds=STALE_AFTER_SECONDS)).isoformat(timespec="seconds")
    with connect() as connection:
        row = connection.execute(
            """
            SELECT (SELECT COUNT(*) FROM users) AS users,
                   (SELECT COUNT(*) FROM users WHERE status = 'pending') AS pending,
                   (SELECT COUNT(*) FROM fleet) AS vehicles,
                   (SELECT COUNT(*) FROM vehicles
                    JOIN fleet ON fleet.vehicle_id = vehicles.vehicle_id
                    JOIN users AS operators ON operators.id = fleet.operator_id
                    WHERE operators.status = 'active' AND vehicles.updated_at >= ?) AS live
            """,
            (live_since,),
        ).fetchone()
    return {"summary": dict(row)}


@app.get("/api/admin/fleet")
def admin_fleet(session: Annotated[tuple[dict, str, str], Depends(current_session)]):
    if session[0]["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access is required.")
    with connect() as connection:
        return {"vehicles": list_fleet_rows(connection)}


@app.post("/api/admin/users/{user_id}/status")
def update_user_status(
    user_id: str,
    body: ReviewInput,
    session: Annotated[tuple[dict, str, str], Depends(role_session("admin"))],
):
    if user_id == session[0]["id"]:
        raise HTTPException(status_code=400, detail="You cannot change your own account status.")
    with connect() as connection:
        row = connection.execute("SELECT role, status FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found.")
        if row["role"] == "admin":
            raise HTTPException(status_code=403, detail="Admin accounts cannot be changed from this screen.")
        if row["role"] not in {"operator", "authority"}:
            raise HTTPException(status_code=400, detail="Only operator/authority accounts can be reviewed.")
        if row["status"] == "rejected" and body.status != "active":
            raise HTTPException(status_code=400, detail="Rejected accounts can only be approved.")
        connection.execute("UPDATE users SET status = ? WHERE id = ?", (body.status, user_id))
        if body.status != "active":
            connection.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            if row["role"] == "operator":
                connection.execute(
                    """
                    DELETE FROM vehicles WHERE vehicle_id IN
                    (SELECT vehicle_id FROM fleet WHERE operator_id = ?)
                    """,
                    (user_id,),
                )
    return {"ok": True}


@app.post("/api/admin/account/email")
def update_admin_email(
    body: AdminEmailInput,
    session: Annotated[tuple[dict, str, str], Depends(role_session("admin"))],
):
    with connect() as connection:
        user = connection.execute(
            "SELECT * FROM users WHERE id = ? AND role = 'admin' AND status = 'active'",
            (session[0]["id"],),
        ).fetchone()
        if not user or not verify_password(body.password, user["password_hash"]):
            raise HTTPException(status_code=403, detail="Your current password is incorrect.")
        try:
            connection.execute("UPDATE users SET email = ? WHERE id = ?", (body.email, session[0]["id"]))
        except sqlite3.IntegrityError as error:
            raise HTTPException(status_code=409, detail="An account with this email already exists.") from error
        connection.execute(
            "DELETE FROM sessions WHERE user_id = ? AND token_hash != ?",
            (session[0]["id"], hashlib.sha256(session[2].encode()).hexdigest()),
        )
        updated = connection.execute("SELECT * FROM users WHERE id = ?", (session[0]["id"],)).fetchone()
    return {"user": public_user(updated)}


if _frontend_dist.is_dir():
    app.mount("/assets", StaticFiles(directory=_frontend_dist / "assets"), name="assets")


@app.get("/{path:path}", include_in_schema=False)
def serve_frontend(path: str):
    if _frontend_dist.is_dir() and (_frontend_dist / "index.html").is_file():
        return FileResponse(_frontend_dist / "index.html")
    raise HTTPException(status_code=404, detail="Frontend build not found. Run npm run build in the frontend directory.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=os.environ.get("BUS_TRACKER_HOST", "127.0.0.1"),
        port=int(os.environ.get("BUS_TRACKER_PORT", "8000")),
        reload=False,
    )

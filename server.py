"""Small, local-first API for the Sri Lanka bus-tracking MVP."""

from __future__ import annotations

import json
import hashlib
import hmac
import ipaddress
import math
import os
import queue
import re
import secrets
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import CookieError, SimpleCookie
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("BUS_TRACKER_DB", ROOT / "data" / "buses.sqlite3"))
STALE_AFTER_SECONDS = 90
MAX_REQUEST_BYTES = 8_192
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]{1,64}@[^@\s.]+(?:\.[^@\s.]+)+$")
PASSWORD_ITERATIONS = 310_000
SESSION_DURATION = timedelta(hours=12)
LOGIN_WINDOW_SECONDS = 900
LOGIN_MAX_ATTEMPTS = 5
ROLES = {"passenger", "driver", "operator", "authority", "admin"}
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

_subscribers: set[queue.Queue[str]] = set()
_subscribers_lock = threading.Lock()
_login_attempts: dict[tuple[str, str], list[float]] = {}
_login_attempts_lock = threading.Lock()


class LocationError(ValueError):
    """An incoming driver location is invalid."""


class Database:
    def __init__(self, path: Path):
        self.path = path
        self._schema_lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            self.ensure_schema(connection)
        self.ensure_bootstrap_admin()

    @staticmethod
    def ensure_schema(connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicles (
                vehicle_id TEXT PRIMARY KEY,
                route_id TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                accuracy REAL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                name TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('passenger', 'driver', 'operator', 'authority', 'admin')),
                status TEXT NOT NULL CHECK (status IN ('pending', 'active', 'rejected', 'suspended')),
                organization TEXT,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                csrf_token TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS fleet (
                vehicle_id TEXT PRIMARY KEY,
                route_id TEXT NOT NULL,
                operator_id TEXT NOT NULL REFERENCES users(id),
                driver_id TEXT UNIQUE REFERENCES users(id),
                created_at TEXT NOT NULL
            )
            """
        )

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._schema_lock:
            database_missing = not self.path.exists()
            connection = sqlite3.connect(self.path, timeout=10)
            if database_missing:
                self.ensure_schema(connection)
                connection.commit()
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_bytes(16)
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
        return f"{PASSWORD_ITERATIONS}${salt.hex()}${derived.hex()}"

    @staticmethod
    def verify_password(password: str, encoded: str) -> bool:
        try:
            iterations_text, salt_text, digest_text = encoded.split("$", 2)
            iterations = int(iterations_text)
            salt = bytes.fromhex(salt_text)
            expected = bytes.fromhex(digest_text)
        except (ValueError, TypeError):
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)

    @staticmethod
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

    def ensure_bootstrap_admin(self) -> None:
        email = os.environ.get("BUS_TRACKER_ADMIN_EMAIL", "").strip().casefold()
        password = os.environ.get("BUS_TRACKER_ADMIN_PASSWORD", "")
        if not email and not password:
            return
        if not email or not password or not EMAIL_PATTERN.fullmatch(email) or len(password) < 16:
            raise RuntimeError(
                "Set both BUS_TRACKER_ADMIN_EMAIL and BUS_TRACKER_ADMIN_PASSWORD "
                "(valid email; password at least 16 characters) to bootstrap the first admin."
            )
        with self.connect() as connection:
            existing_admin = connection.execute(
                "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
            ).fetchone()
            if existing_admin:
                return
            existing_email = connection.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()
            if existing_email:
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
                    self.hash_password(password),
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                ),
            )

    def has_admin(self) -> bool:
        with self.connect() as connection:
            return connection.execute(
                "SELECT 1 FROM users WHERE role = 'admin' LIMIT 1"
            ).fetchone() is not None

    def setup_initial_admin(self, payload: object) -> tuple[dict, str, str]:
        if not isinstance(payload, dict):
            raise ValueError("Expected a JSON object.")
        name = payload.get("name")
        email = payload.get("email")
        password = payload.get("password")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 80:
            raise ValueError("Enter your name (up to 80 characters).")
        if not isinstance(email, str) or not EMAIL_PATTERN.fullmatch(email.strip()):
            raise ValueError("Enter a valid email address.")
        email = email.strip().casefold()
        if not isinstance(password, str) or len(password) < 16 or len(password) > 128:
            raise ValueError("Admin password must be between 16 and 128 characters.")

        user_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        password_hash = self.hash_password(password)
        token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now(timezone.utc) + SESSION_DURATION).isoformat(timespec="seconds")
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1").fetchone():
                raise PermissionError("The admin account has already been set up.")
            try:
                connection.execute(
                    """
                    INSERT INTO users (id, email, name, role, status, password_hash, created_at)
                    VALUES (?, ?, ?, 'admin', 'active', ?, ?)
                    """,
                    (user_id, email, name.strip(), password_hash, created_at),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError("An account with this email already exists.") from error
            connection.execute(
                "INSERT INTO sessions (token_hash, user_id, csrf_token, expires_at) VALUES (?, ?, ?, ?)",
                (hashlib.sha256(token.encode()).hexdigest(), user_id, csrf_token, expires_at),
            )
        return {
            "id": user_id, "email": email, "name": name.strip(), "role": "admin",
            "status": "active", "organization": None, "createdAt": created_at,
        }, token, csrf_token

    def register(self, payload: object) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("Expected a JSON object.")
        name = payload.get("name")
        email = payload.get("email")
        password = payload.get("password")
        role = payload.get("role")
        organization = payload.get("organization")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 80:
            raise ValueError("Enter your name (up to 80 characters).")
        if not isinstance(email, str) or not EMAIL_PATTERN.fullmatch(email.strip()):
            raise ValueError("Enter a valid email address.")
        email = email.strip().casefold()
        if not isinstance(password, str) or len(password) < 12 or len(password) > 128:
            raise ValueError("Password must be between 12 and 128 characters.")
        if not isinstance(role, str) or role not in {"passenger", "driver", "operator", "authority"}:
            raise ValueError("Choose a supported account type. Admin accounts are provisioned separately.")
        if payload.get("consent") is not True:
            raise ValueError("Please confirm that you understand the account and location-sharing terms.")
        if role in {"operator", "authority"}:
            if not isinstance(organization, str) or not organization.strip() or len(organization.strip()) > 120:
                raise ValueError("Enter the organization or agency name for approval.")
            organization = organization.strip()
        else:
            organization = None

        status = "pending" if role in {"operator", "authority"} else "active"
        user = {
            "id": str(uuid.uuid4()),
            "email": email,
            "name": name.strip(),
            "role": role,
            "status": status,
            "organization": organization,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        try:
            with self.connect() as connection:
                connection.execute(
                    """
                    INSERT INTO users (id, email, name, role, status, organization, password_hash, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user["id"], user["email"], user["name"], user["role"], user["status"],
                        user["organization"], self.hash_password(password), user["created_at"],
                    ),
                )
        except sqlite3.IntegrityError as error:
            raise ValueError("An account with this email already exists.") from error
        return user

    def login(self, payload: object) -> tuple[dict, str, str]:
        if not isinstance(payload, dict):
            raise ValueError("Expected a JSON object.")
        email = payload.get("email")
        password = payload.get("password")
        if not isinstance(email, str) or not isinstance(password, str):
            raise ValueError("Enter your email and password.")
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE email = ?", (email.strip().casefold(),)
            ).fetchone()
        if not row or not self.verify_password(password, row["password_hash"]):
            raise ValueError("Email or password is incorrect.")
        if row["status"] != "active":
            raise PermissionError(f"Your {row['status']} account cannot sign in.")
        token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        expires_at = (datetime.now(timezone.utc) + SESSION_DURATION).isoformat(timespec="seconds")
        with self.connect() as connection:
            connection.execute("DELETE FROM sessions WHERE expires_at < ?", (datetime.now(timezone.utc).isoformat(),))
            connection.execute(
                "INSERT INTO sessions (token_hash, user_id, csrf_token, expires_at) VALUES (?, ?, ?, ?)",
                (hashlib.sha256(token.encode()).hexdigest(), row["id"], csrf_token, expires_at),
            )
        return self.public_user(row), token, csrf_token

    def update_admin_email(
        self, user_id: str, payload: object, session_token: str
    ) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("Expected a JSON object.")
        email = payload.get("email")
        password = payload.get("password")
        if not isinstance(email, str) or not EMAIL_PATTERN.fullmatch(email.strip()):
            raise ValueError("Enter a valid email address.")
        if not isinstance(password, str) or not password:
            raise ValueError("Enter your current password to confirm this change.")
        email = email.strip().casefold()
        session_hash = hashlib.sha256(session_token.encode()).hexdigest()

        with self.connect() as connection:
            user = connection.execute(
                "SELECT * FROM users WHERE id = ? AND role = 'admin' AND status = 'active'",
                (user_id,),
            ).fetchone()
            if not user or not self.verify_password(password, user["password_hash"]):
                raise PermissionError("Your current password is incorrect.")
            try:
                connection.execute("UPDATE users SET email = ? WHERE id = ?", (email, user_id))
            except sqlite3.IntegrityError as error:
                raise ValueError("An account with this email already exists.") from error
            connection.execute(
                "DELETE FROM sessions WHERE user_id = ? AND token_hash != ?",
                (user_id, session_hash),
            )
            updated_user = connection.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()

        return self.public_user(updated_user)

    def get_session(self, token: str | None) -> tuple[dict, str] | None:
        if not token:
            return None
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT users.*, sessions.csrf_token, sessions.expires_at
                FROM sessions JOIN users ON users.id = sessions.user_id
                WHERE sessions.token_hash = ?
                """,
                (token_hash,),
            ).fetchone()
        if not row or row["status"] != "active" or row["expires_at"] < datetime.now(timezone.utc).isoformat():
            self.revoke_session(token)
            return None
        return self.public_user(row), row["csrf_token"]

    def revoke_session(self, token: str | None) -> None:
        if not token:
            return
        with self.connect() as connection:
            connection.execute(
                "DELETE FROM sessions WHERE token_hash = ?",
                (hashlib.sha256(token.encode()).hexdigest(),),
            )

    def list_users(self) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, email, name, role, status, organization, created_at FROM users ORDER BY created_at"
            ).fetchall()
        return [self.public_user(row) for row in rows]

    def update_user_status(self, user_id: str, status: str, acting_user_id: str) -> None:
        if status not in {"active", "rejected", "suspended"}:
            raise ValueError("Choose active, rejected, or suspended.")
        if user_id == acting_user_id:
            raise ValueError("You cannot change your own account status.")
        with self.connect() as connection:
            row = connection.execute("SELECT role, status FROM users WHERE id = ?", (user_id,)).fetchone()
            if not row:
                raise LookupError("Account not found.")
            if row["role"] == "admin":
                raise PermissionError("Admin accounts cannot be changed from this screen.")
            if row["role"] not in {"operator", "authority"}:
                raise ValueError("Only operator/authority accounts can be reviewed.")
            if row["status"] not in {"pending", "active", "suspended", "rejected"}:
                raise ValueError("This account cannot be reviewed.")
            if row["status"] == "rejected" and status != "active":
                raise ValueError("Rejected accounts can only be approved.")
            connection.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
            if status != "active":
                connection.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))

    def list_fleet(self, operator_id: str) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT fleet.vehicle_id, fleet.route_id, fleet.created_at,
                       users.id AS driver_id, users.name AS driver_name, users.email AS driver_email
                FROM fleet LEFT JOIN users ON users.id = fleet.driver_id
                WHERE fleet.operator_id = ? ORDER BY fleet.created_at
                """,
                (operator_id,),
            ).fetchall()
        return [
            {
                "vehicleId": row["vehicle_id"], "routeId": row["route_id"],
                "createdAt": row["created_at"], "driverId": row["driver_id"],
                "driverName": row["driver_name"], "driverEmail": row["driver_email"],
            }
            for row in rows
        ]

    def list_all_fleet(self) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT fleet.vehicle_id, fleet.route_id, fleet.created_at,
                       operators.id AS operator_id, operators.name AS operator_name,
                       operators.email AS operator_email, operators.organization AS organization,
                       operators.status AS operator_status,
                       drivers.id AS driver_id, drivers.name AS driver_name, drivers.email AS driver_email
                FROM fleet
                JOIN users AS operators ON operators.id = fleet.operator_id
                LEFT JOIN users AS drivers ON drivers.id = fleet.driver_id
                ORDER BY operators.organization, fleet.vehicle_id
                """
            ).fetchall()
        return [
            {
                "vehicleId": row["vehicle_id"],
                "routeId": row["route_id"],
                "createdAt": row["created_at"],
                "operatorId": row["operator_id"],
                "operatorName": row["operator_name"],
                "operatorEmail": row["operator_email"],
                "organization": row["organization"],
                "operatorStatus": row["operator_status"],
                "driverId": row["driver_id"],
                "driverName": row["driver_name"],
                "driverEmail": row["driver_email"],
            }
            for row in rows
        ]

    def admin_summary(self) -> dict:
        with self.connect() as connection:
            counts = connection.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM users) AS users,
                    (SELECT COUNT(*) FROM users WHERE status = 'pending') AS pending,
                    (SELECT COUNT(*) FROM fleet) AS vehicles,
                    (SELECT COUNT(*) FROM vehicles
                     JOIN fleet ON fleet.vehicle_id = vehicles.vehicle_id
                     JOIN users AS operators ON operators.id = fleet.operator_id
                     WHERE operators.status = 'active'
                       AND vehicles.updated_at >= ?) AS live
                """,
                ((datetime.now(timezone.utc) - timedelta(seconds=STALE_AFTER_SECONDS)).isoformat(timespec="seconds"),),
            ).fetchone()
        return dict(counts)

    def create_fleet_vehicle(self, operator_id: str, payload: object) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("Expected a JSON object.")
        vehicle_id = payload.get("vehicleId")
        route_id = payload.get("routeId")
        if not isinstance(vehicle_id, str) or not ID_PATTERN.fullmatch(vehicle_id):
            raise ValueError("Vehicle ID must use 1–32 letters, numbers, underscores, or hyphens.")
        if not isinstance(route_id, str) or route_id not in {route["id"] for route in ROUTES}:
            raise ValueError("Choose a valid route.")
        try:
            with self.connect() as connection:
                connection.execute(
                    "INSERT INTO fleet (vehicle_id, route_id, operator_id, created_at) VALUES (?, ?, ?, ?)",
                    (vehicle_id, route_id, operator_id, datetime.now(timezone.utc).isoformat(timespec="seconds")),
                )
        except sqlite3.IntegrityError as error:
            raise ValueError("This vehicle ID is already registered.") from error
        return {"vehicleId": vehicle_id, "routeId": route_id}

    def assign_driver(self, operator_id: str, vehicle_id: str, payload: object) -> None:
        if not isinstance(payload, dict) or not isinstance(payload.get("email"), str):
            raise ValueError("Enter the driver's registered email.")
        with self.connect() as connection:
            fleet = connection.execute(
                "SELECT vehicle_id FROM fleet WHERE vehicle_id = ? AND operator_id = ?",
                (vehicle_id, operator_id),
            ).fetchone()
            driver = connection.execute(
                "SELECT id FROM users WHERE email = ? AND role = 'driver' AND status = 'active'",
                (payload["email"].strip().casefold(),),
            ).fetchone()
            if not fleet:
                raise LookupError("Vehicle not found in your fleet.")
            if not driver:
                raise LookupError("No active driver account found for that email.")
            try:
                connection.execute(
                    "UPDATE fleet SET driver_id = ? WHERE vehicle_id = ?",
                    (driver["id"], vehicle_id),
                )
            except sqlite3.IntegrityError as error:
                raise ValueError("That driver is already assigned to another vehicle.") from error

    def driver_vehicle(self, driver_id: str) -> dict | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT fleet.vehicle_id, fleet.route_id
                FROM fleet JOIN users AS operators ON operators.id = fleet.operator_id
                WHERE fleet.driver_id = ? AND operators.status = 'active'
                """,
                (driver_id,),
            ).fetchone()
        return {"vehicleId": row["vehicle_id"], "routeId": row["route_id"]} if row else None

    def save_location(self, payload: object, actor: dict) -> dict:
        if not isinstance(payload, dict):
            raise LocationError("Expected a JSON object.")

        assigned_vehicle = self.driver_vehicle(actor["id"])
        if actor["role"] != "driver" or not assigned_vehicle:
            raise PermissionError("Only a driver assigned to an operator-registered vehicle can share locations.")
        vehicle_id = assigned_vehicle["vehicleId"]
        route_id = assigned_vehicle["routeId"]

        try:
            lat = float(payload["lat"])
            lon = float(payload["lon"])
        except (KeyError, TypeError, ValueError) as error:
            raise LocationError("A valid latitude and longitude are required.") from error
        if not math.isfinite(lat) or not math.isfinite(lon):
            raise LocationError("Latitude and longitude must be finite numbers.")
        if not (SRI_LANKA_BOUNDS["minLat"] <= lat <= SRI_LANKA_BOUNDS["maxLat"]):
            raise LocationError("Latitude is outside Sri Lanka.")
        if not (SRI_LANKA_BOUNDS["minLon"] <= lon <= SRI_LANKA_BOUNDS["maxLon"]):
            raise LocationError("Longitude is outside Sri Lanka.")

        accuracy_value = payload.get("accuracy")
        accuracy = None
        if accuracy_value is not None:
            try:
                accuracy = float(accuracy_value)
            except (TypeError, ValueError) as error:
                raise LocationError("Accuracy must be a number.") from error
            if not math.isfinite(accuracy) or not 0 <= accuracy <= 100_000:
                raise LocationError("Accuracy is outside the allowed range.")

        updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO vehicles (vehicle_id, route_id, lat, lon, accuracy, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(vehicle_id) DO UPDATE SET
                    route_id = excluded.route_id,
                    lat = excluded.lat,
                    lon = excluded.lon,
                    accuracy = excluded.accuracy,
                    updated_at = excluded.updated_at
                """,
                (vehicle_id, route_id, lat, lon, accuracy, updated_at),
            )
        return {
            "vehicleId": vehicle_id,
            "routeId": route_id,
            "lat": lat,
            "lon": lon,
            "accuracy": accuracy,
            "updatedAt": updated_at,
            "demo": True,
        }

    def list_vehicles(self) -> list[dict]:
        with self.connect() as connection:
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
        vehicles = []
        for row in rows:
            updated_at = datetime.fromisoformat(row["updated_at"])
            age_seconds = max(0, int((now - updated_at).total_seconds()))
            vehicles.append(
                {
                    "vehicleId": row["vehicle_id"],
                    "routeId": row["route_id"],
                    "lat": row["lat"],
                    "lon": row["lon"],
                    "accuracy": row["accuracy"],
                    "updatedAt": row["updated_at"],
                    "ageSeconds": age_seconds,
                    "status": "live" if age_seconds <= STALE_AFTER_SECONDS else "stale",
                    "demo": True,
                }
            )
        return vehicles


database = Database(DB_PATH)


def publish_vehicles() -> None:
    message = json.dumps({"vehicles": database.list_vehicles()}, separators=(",", ":"))
    with _subscribers_lock:
        subscribers = tuple(_subscribers)
    for subscriber in subscribers:
        try:
            subscriber.put_nowait(message)
        except queue.Full:
            try:
                subscriber.get_nowait()
                subscriber.put_nowait(message)
            except (queue.Empty, queue.Full):
                pass


class Handler(BaseHTTPRequestHandler):
    server_version = "BusTracker/0.1"

    def read_json(self) -> object:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Invalid Content-Length.") from error
        if length < 1 or length > MAX_REQUEST_BYTES:
            raise ValueError("Request body must be between 1 and 8192 bytes.")
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError("Request body must be valid JSON.") from error

    def request_session(self) -> tuple[dict, str, str] | None:
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except CookieError:
            return None
        morsel = cookie.get("buslk_session")
        token = morsel.value if morsel else None
        session = database.get_session(token)
        if not session:
            return None
        return session[0], session[1], token

    def require_roles(self, *roles: str) -> tuple[dict, str, str] | None:
        session = self.request_session()
        if not session:
            self.send_json(401, {"error": "Sign in is required."})
            return None
        user = session[0]
        if user["role"] not in roles:
            self.send_json(403, {"error": "Your account role is not allowed to do this."})
            return None
        if not self.valid_csrf(session[1]):
            self.send_json(403, {"error": "Security token is missing or invalid. Refresh and try again."})
            return None
        return session

    def valid_csrf(self, expected: str) -> bool:
        supplied = self.headers.get("X-CSRF-Token", "")
        return bool(supplied) and hmac.compare_digest(supplied, expected)

    def origin_is_same(self) -> bool:
        origin = self.headers.get("Origin")
        if not origin:
            return True
        parsed = urlparse(origin)
        return parsed.netloc.casefold() == self.headers.get("Host", "").casefold()

    def is_local_client(self) -> bool:
        try:
            server_address = ipaddress.ip_address(self.server.server_address[0])
            client_address = ipaddress.ip_address(self.client_address[0])
            return server_address.is_loopback and client_address.is_loopback
        except ValueError:
            return False

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/routes":
            self.send_json(200, {"routes": ROUTES})
        elif path == "/api/vehicles":
            self.send_json(200, {"vehicles": database.list_vehicles()})
        elif path == "/api/stream":
            self.stream_vehicles()
        elif path == "/api/auth/me":
            session = self.request_session()
            self.send_json(
                200,
                {"user": session[0], "csrfToken": session[1]} if session else {"user": None},
            )
        elif path == "/api/auth/setup-status":
            if not self.is_local_client():
                self.send_json(403, {"error": "First admin setup is only available on this computer."})
            else:
                self.send_json(200, {"available": not database.has_admin()})
        elif path == "/api/admin/users":
            session = self.request_session()
            if not session:
                self.send_json(401, {"error": "Sign in is required."})
            elif session[0]["role"] != "admin":
                self.send_json(403, {"error": "Admin access is required."})
            else:
                self.send_json(200, {"users": database.list_users()})
        elif path == "/api/admin/summary":
            session = self.request_session()
            if not session:
                self.send_json(401, {"error": "Sign in is required."})
            elif session[0]["role"] != "admin":
                self.send_json(403, {"error": "Admin access is required."})
            else:
                self.send_json(200, {"summary": database.admin_summary()})
        elif path == "/api/admin/fleet":
            session = self.request_session()
            if not session:
                self.send_json(401, {"error": "Sign in is required."})
            elif session[0]["role"] != "admin":
                self.send_json(403, {"error": "Admin access is required."})
            else:
                self.send_json(200, {"vehicles": database.list_all_fleet()})
        elif path == "/api/operator/fleet":
            session = self.request_session()
            if not session:
                self.send_json(401, {"error": "Sign in is required."})
            elif session[0]["role"] not in {"operator", "admin"}:
                self.send_json(403, {"error": "Operator access is required."})
            else:
                self.send_json(200, {"vehicles": database.list_fleet(session[0]["id"])})
        elif path == "/api/driver/vehicle":
            session = self.request_session()
            if not session:
                self.send_json(401, {"error": "Sign in is required."})
            elif session[0]["role"] != "driver":
                self.send_json(403, {"error": "Driver access is required."})
            else:
                self.send_json(200, {"vehicle": database.driver_vehicle(session[0]["id"])})
        elif path == "/":
            self.serve_file(ROOT / "index.html", "text/html; charset=utf-8")
        elif path == "/admin":
            self.serve_file(ROOT / "admin.html", "text/html; charset=utf-8")
        elif path in ("/app.js", "/styles.css"):
            content_type = "text/javascript; charset=utf-8" if path.endswith(".js") else "text/css; charset=utf-8"
            self.serve_file(ROOT / path.lstrip("/"), content_type)
        elif path in ("/admin.js", "/admin.css"):
            content_type = "text/javascript; charset=utf-8" if path.endswith(".js") else "text/css; charset=utf-8"
            self.serve_file(ROOT / path.lstrip("/"), content_type)
        else:
            self.send_json(404, {"error": "Not found."})

    def do_POST(self) -> None:
        if not self.origin_is_same():
            self.send_json(403, {"error": "Cross-origin requests are not allowed."})
            return
        path = urlparse(self.path).path
        if path == "/api/auth/register":
            self.handle_register()
            return
        if path == "/api/auth/setup-admin":
            self.handle_admin_setup()
            return
        if path == "/api/auth/login":
            self.handle_login()
            return
        if path == "/api/auth/logout":
            session = self.request_session()
            if not session:
                self.send_json(401, {"error": "Sign in is required."})
                return
            if not self.valid_csrf(session[1]):
                self.send_json(403, {"error": "Security token is missing or invalid."})
                return
            database.revoke_session(session[2])
            self.send_json(200, {"ok": True}, {"Set-Cookie": self.session_cookie("", max_age=0)})
            return
        if path == "/api/admin/account/email":
            session = self.require_roles("admin")
            if not session:
                return
            try:
                user = database.update_admin_email(
                    session[0]["id"], self.read_json(), session[2]
                )
            except ValueError as error:
                self.send_json(400, {"error": str(error)})
                return
            except PermissionError as error:
                self.send_json(403, {"error": str(error)})
                return
            self.send_json(200, {"user": user})
            return
        if path == "/api/locations":
            session = self.require_roles("driver")
            if not session:
                return
            try:
                payload = self.read_json()
                vehicle = database.save_location(payload, session[0])
            except (ValueError, LocationError) as error:
                self.send_json(400, {"error": str(error)})
                return
            except PermissionError as error:
                self.send_json(403, {"error": str(error)})
                return
            publish_vehicles()
            self.send_json(201, {"vehicle": vehicle})
            return
        if path == "/api/operator/fleet":
            session = self.require_roles("operator", "admin")
            if not session:
                return
            try:
                vehicle = database.create_fleet_vehicle(session[0]["id"], self.read_json())
            except ValueError as error:
                self.send_json(400, {"error": str(error)})
                return
            self.send_json(201, {"vehicle": vehicle})
            return
        assignment = re.fullmatch(r"/api/operator/fleet/([A-Za-z0-9_-]{1,32})/assign", path)
        if assignment:
            session = self.require_roles("operator", "admin")
            if not session:
                return
            try:
                database.assign_driver(session[0]["id"], assignment.group(1), self.read_json())
            except ValueError as error:
                self.send_json(400, {"error": str(error)})
                return
            except LookupError as error:
                self.send_json(404, {"error": str(error)})
                return
            self.send_json(200, {"ok": True})
            return
        review = re.fullmatch(r"/api/admin/users/([0-9a-f-]{36})/status", path)
        if review:
            session = self.require_roles("admin")
            if not session:
                return
            try:
                payload = self.read_json()
                if not isinstance(payload, dict):
                    raise ValueError("Expected a JSON object.")
                database.update_user_status(review.group(1), payload.get("status"), session[0]["id"])
            except ValueError as error:
                self.send_json(400, {"error": str(error)})
                return
            except LookupError as error:
                self.send_json(404, {"error": str(error)})
                return
            except PermissionError as error:
                self.send_json(403, {"error": str(error)})
                return
            self.send_json(200, {"ok": True})
            return
        self.send_json(404, {"error": "Not found."})

    def handle_register(self) -> None:
        try:
            user = database.register(self.read_json())
        except ValueError as error:
            self.send_json(400, {"error": str(error)})
            return
        self.send_json(201, {"user": user})

    def handle_admin_setup(self) -> None:
        if not self.is_local_client():
            self.send_json(403, {"error": "First admin setup is only available on this computer."})
            return
        try:
            user, token, csrf_token = database.setup_initial_admin(self.read_json())
        except ValueError as error:
            self.send_json(400, {"error": str(error)})
            return
        except PermissionError as error:
            self.send_json(409, {"error": str(error)})
            return
        self.send_json(
            201,
            {"user": user, "csrfToken": csrf_token},
            {"Set-Cookie": self.session_cookie(token, int(SESSION_DURATION.total_seconds()))},
        )

    def handle_login(self) -> None:
        try:
            payload = self.read_json()
        except ValueError as error:
            self.send_json(400, {"error": str(error)})
            return
        email = payload.get("email", "").strip().casefold() if isinstance(payload, dict) and isinstance(payload.get("email"), str) else ""
        attempt_key = (self.client_address[0], email)
        now = time.monotonic()
        with _login_attempts_lock:
            attempts = [timestamp for timestamp in _login_attempts.get(attempt_key, []) if now - timestamp < LOGIN_WINDOW_SECONDS]
            _login_attempts[attempt_key] = attempts
            rate_limited = len(attempts) >= LOGIN_MAX_ATTEMPTS
        if rate_limited:
            self.send_json(429, {"error": "Too many sign-in attempts. Wait 15 minutes and try again."})
            return
        try:
            user, token, csrf_token = database.login(payload)
        except ValueError as error:
            with _login_attempts_lock:
                _login_attempts.setdefault(attempt_key, []).append(now)
            self.send_json(400, {"error": str(error)})
            return
        except PermissionError as error:
            self.send_json(403, {"error": str(error)})
            return
        with _login_attempts_lock:
            _login_attempts.pop(attempt_key, None)
        self.send_json(
            200,
            {"user": user, "csrfToken": csrf_token},
            {"Set-Cookie": self.session_cookie(token, int(SESSION_DURATION.total_seconds()))},
        )

    @staticmethod
    def session_cookie(token: str, max_age: int) -> str:
        secure = "; Secure" if os.environ.get("BUS_TRACKER_COOKIE_SECURE") == "1" else ""
        return f"buslk_session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={max_age}{secure}"

    def stream_vehicles(self) -> None:
        subscriber: queue.Queue[str] = queue.Queue(maxsize=1)
        with _subscribers_lock:
            _subscribers.add(subscriber)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        subscriber.put(json.dumps({"vehicles": database.list_vehicles()}, separators=(",", ":")))
        try:
            while True:
                try:
                    message = subscriber.get(timeout=15)
                    self.wfile.write(f"data: {message}\n\n".encode("utf-8"))
                except queue.Empty:
                    snapshot = json.dumps({"vehicles": database.list_vehicles()}, separators=(",", ":"))
                    self.wfile.write(f"data: {snapshot}\n\n".encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with _subscribers_lock:
                _subscribers.discard(subscriber)

    def serve_file(self, path: Path, content_type: str) -> None:
        try:
            body = path.read_bytes()
        except OSError:
            self.send_json(500, {"error": "The application file could not be read."})
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status: int, data: dict, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string: str, *args: object) -> None:
        print(f"{self.log_date_time_string()} {self.address_string()} {format_string % args}")


def main() -> None:
    host = os.environ.get("BUS_TRACKER_HOST", "127.0.0.1")
    port = int(os.environ.get("BUS_TRACKER_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Bus tracker MVP running at http://{host}:{port}")
    print(f"SQLite database: {DB_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping bus tracker.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

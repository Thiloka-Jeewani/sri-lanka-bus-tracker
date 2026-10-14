# Bus.lk — Sri Lanka bus tracker

A community bus-tracking pilot with a **React + TypeScript frontend** and a separate **FastAPI backend**. The backend provides validated JSON APIs, role-based access, SQLite persistence, and live location updates over Server-Sent Events.

> **Prototype, not a production transit service.** The Colombo Fort–Pettah route is illustrative, not surveyed or official. Real service data and locations are not independently verified. Do not use this prototype to make safety-critical travel decisions or expose it publicly with real location data before the production safeguards below are addressed.

## Project layout

- `frontend/` — Vite, React, TypeScript, and Leaflet web client.
- `backend/app/main.py` — FastAPI API and production static-build serving.
- `backend/requirements.txt` — Python runtime dependencies.
- `backend/tests/` — API workflow tests.
- `data/buses.sqlite3` — local SQLite database, created on first run.

## Run locally

Requires Python 3.10+ and Node.js 20+.

Install dependencies:

```powershell
python -m pip install -r backend\requirements-dev.txt
Set-Location frontend
npm ci
```

Run the backend and frontend in separate terminals from the project root:

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
Set-Location frontend
npm run dev
```

Open <http://127.0.0.1:5173>. Vite proxies `/api` requests to FastAPI. To run a production-style single server, build the frontend and start the API:

```powershell
Set-Location frontend
npm run build
Set-Location ..
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

The built React application is then served by FastAPI at <http://127.0.0.1:8000>.

Set `BUS_TRACKER_DB` to choose a database file; `BUS_TRACKER_HOST` and `BUS_TRACKER_PORT` configure the server entry point. Keep the default listen address on your own computer for development. Set `BUS_TRACKER_COOKIE_SECURE=1` behind HTTPS. For automated initial setup, set both `BUS_TRACKER_ADMIN_EMAIL` and `BUS_TRACKER_ADMIN_PASSWORD` (16–128 characters); optionally set `BUS_TRACKER_ADMIN_NAME`. Never commit these secrets. Otherwise, the first administrator can be created once from the local setup form; this setup is restricted to loopback requests.

The frontend uses OpenStreetMap tiles and Leaflet from npm. Map tiles still require network access; review provider terms and privacy implications before launch.

## Account, access, and operator workflows

- Passengers and drivers register with a valid email, a 12–128 character password, and affirmative consent. Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes.
- Operator and transport-authority signups require an organization and remain pending until an administrator approves them. Admin accounts cannot be publicly registered.
- Sessions use random server-side tokens in HttpOnly, SameSite cookies; mutating authenticated requests require a CSRF token. Login attempts are throttled in-process. Set secure cookies only when serving over HTTPS.
- Administrators can review pending stakeholder signups, reject/suspend/reactivate approved stakeholders, search accounts, inspect fleet/network summaries, and update their email after confirming the current password. Changing the admin email revokes the admin's other sessions.
- Approved operators register buses on configured routes and assign active driver accounts by email. Drivers can submit GPS only after an operator assigns them a registered vehicle; the server derives vehicle and route identity from that assignment.
- Passengers and authorities can view public live positions. Drivers start sharing explicitly from a secure browser context (HTTPS or localhost). **Stop sharing** deletes the currently published position; signing out also clears it. Closing the page attempts the same cleanup while stopping browser GPS updates.
- Coordinates are checked for finite values and Sri Lanka bounds, GPS accuracy is range-checked, vehicle IDs and route IDs are validated, and role/ownership checks are enforced by the API.

## API

- `GET /api/routes`, `GET /api/vehicles`, `GET /api/stream`
- `GET /api/auth/me`, `GET /api/auth/setup-status`
- `POST /api/auth/register`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/setup-admin`
- `GET /api/driver/vehicle`, `POST /api/locations`, `POST /api/driver/location/stop`
- `GET /api/operator/fleet`, `POST /api/operator/fleet`, `POST /api/operator/fleet/{vehicleId}/assign`
- `GET /api/admin/users`, `/api/admin/summary`, `/api/admin/fleet`
- `POST /api/admin/users/{id}/status`, `/api/admin/account/email`

Invalid request models return FastAPI validation errors. Authenticated writes require `X-CSRF-Token`; browser writes with a cross-origin `Origin` are rejected.

## Tests

```powershell
python -m unittest discover -s tests -v
python -m unittest discover -s backend\tests -v
Set-Location frontend
npm run build
```

CI runs the legacy regression tests, new FastAPI workflow tests, and a TypeScript production build.

## Before real public use

The framework migration does not make this pilot production-ready. Before collecting real users' locations:

1. Verify route shapes, stops, schedules, permits, and participating vehicles with a local operator; replace the illustrative route and clearly label any unverified data.
2. Establish consent, access, retention/deletion, support, incident-response, and location-visibility policies, with local legal/privacy review.
3. Deploy behind HTTPS with secure cookies, persistent/managed storage and tested backups. SQLite and the in-process login throttle are for a small single-instance pilot, not a multi-instance service.
4. Add verified email onboarding, account recovery, MFA for privileged roles, shared rate limiting, audit logging, monitoring, and operational recovery procedures.
5. Test with Sinhala-, Tamil-, and English-speaking riders and drivers, assistive technologies, weak networks, and low-end phones.

The service currently stores only each vehicle's latest fix, but does not have an automatic retention/expiry job. Explicitly stopping or ending a driver session removes the public latest fix; inactive location rows otherwise remain stored until a later driver update or operator/admin action. Locations are visible to anyone who can reach the app. Do not collect real location data until a retention and deployment policy is in place.

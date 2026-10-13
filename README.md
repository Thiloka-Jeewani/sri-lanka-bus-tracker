# Bus.lk — Sri Lanka bus tracker MVP

A small, community-first prototype for sharing bus positions. It includes a passenger map, role-based accounts for passengers, drivers, bus operators, transport authorities, and platform administrators, a SQLite-backed location API, and live map updates with Server-Sent Events.

**This is a prototype, not an official or production-ready Sri Lankan transit service.** The only route is a short Colombo Fort–Pettah demo corridor. Its route line connects two illustrative stops; it is not a surveyed road route or an official bus service. Locations come only from people who choose to share them, are marked as demo data, and do not currently verify that a device is on a bus.

## Run locally

Requirements: Python 3.10 or later; no package installation required.

### Set up the first administrator

On a fresh database, simply start the server:

```powershell
python server.py
```

Open <http://127.0.0.1:8000>. The first run creates `data/buses.sqlite3`. Set `BUS_TRACKER_DB` to choose another database file; `BUS_TRACKER_HOST` and `BUS_TRACKER_PORT` configure the listen address and port. Keep the default host on your own computer for development. Set `BUS_TRACKER_COOKIE_SECURE=1` when deployed behind HTTPS.

The Accounts panel shows **Set up the first administrator** until an admin exists. Fill in your name, the one admin email you will use to sign in, and a unique password of at least 16 characters. Creating the account signs you in and opens the admin dashboard. First-time setup is limited to requests from this computer and protected by a database transaction; it automatically closes once the first admin exists. Save the password safely. Admin self-registration is not offered after setup.

The optional `BUS_TRACKER_ADMIN_EMAIL` and `BUS_TRACKER_ADMIN_PASSWORD` environment variables can still provision an initial admin for automated deployments; they are not required for local setup.

If the server reports `sqlite3.OperationalError: unable to open database file`, stop it with Ctrl+C and restart it from the project folder. The server recreates a missing `data` directory and database schema, but a deleted database cannot restore its previous accounts, fleet assignments, or locations; restore a backup if you have one. If the first-admin setup appears again, the current database has no administrator account.

### Account and role workflow

- Passengers and drivers can register and sign in. Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes; sessions use random, server-side, expiring tokens in HttpOnly, SameSite cookies. Mutating authenticated requests require a session CSRF token.
- Bus operators and transport authorities provide an organization/agency name. Their accounts stay pending and cannot sign in until an admin approves them. Rejected/suspended accounts cannot use an existing session.
- The admin reviews pending operator/authority accounts in the account panel. The initial admin is created once through the local first-run setup screen; admin accounts cannot be publicly registered.
- Admins can open the separate `/admin` dashboard from the main Accounts panel. It provides network summary cards, stakeholder approvals, searchable accounts with suspend/reactivate controls, and a cross-operator fleet table. Admin data/actions are protected by role checks; other roles are redirected from the dashboard.
- The dashboard's **Admin account** tab lets the signed-in administrator change their sign-in email after confirming the current password. The new email must be unique; other active sessions for that admin are signed out. This prototype does not verify email ownership, so use an address you control.
- An approved operator can register vehicles and assign each vehicle to a driver's registered email. A driver can share GPS only after signing in and receiving a registered vehicle assignment. Vehicle ID and route are derived on the server from that assignment; drivers cannot claim another bus by changing the browser request.
- Passengers browse the map without signing in. Authorities have a read-only view of the route and public live map. This MVP does not yet provide an authority data-submission or route-verification workflow.
- Driver sharing requires a secure browser context: localhost works for development; a deployed site must use HTTPS. Sign in as an assigned driver, grant location permission, and press **Start sharing location**. Keep the page open while sharing. Press **Stop sharing location** when finished.

Run the focused tests with:

```powershell
python -m unittest discover -s tests -v
```

## API

- `GET /api/routes` — available routes and stops.
- `GET /api/vehicles` — last known vehicle positions and freshness status.
- `GET /api/stream` — Server-Sent Events containing updated vehicle snapshots.
- `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me` — accounts and sessions.
- `GET /api/admin/users`, `POST /api/admin/users/{id}/status` — admin-only stakeholder review.
- `GET /api/admin/summary`, `GET /api/admin/fleet` — admin dashboard overview and fleet data.
- `POST /api/admin/account/email` — change the signed-in admin's email after current-password confirmation.
- `GET /api/operator/fleet`, `POST /api/operator/fleet`, `POST /api/operator/fleet/{vehicleId}/assign` — approved operator fleet management.
- `GET /api/driver/vehicle` — vehicle assigned to the signed-in driver.
- `POST /api/locations` — authenticated driver location update. JSON body includes `lat`, `lon`, and optional `accuracy`; vehicle and route come from the driver's server-side fleet assignment.

Positions older than 90 seconds are shown as **Last seen**, not live. Locations are saved in SQLite and remain there after the server stops; this prototype has no retention/expiry job.

## Before a real public launch

This MVP demonstrates the technical flow; it cannot create verified route or vehicle data on its own. Plan a small, human-led pilot before expanding:

1. **Find a local pilot partner.** Talk with a bus owner/association, depot manager, and a few drivers about a single route. Explain the benefit, who can see the locations, expected phone/battery/data use, and that sharing is voluntary. Agree who handles questions and removal requests.
2. **Survey and verify the route.** Ride it with a local person. Record the actual direction, stop names and coordinates, route/permit identifiers where appropriate, and variations by time/day. Ask the operator to verify every published route. Replace the illustrative geometry before advertising any ETA.
3. **Recruit participating drivers.** Obtain informed, written participation consent and confirm the vehicle ID and route. Test on the driver's own phone, in sunlight, with patchy mobile data; agree how to pause tracking at terminals, breaks, or after a shift.
4. **Verify accounts and add production safeguards before internet exposure.** This prototype has role checks, operator assignment, and a per-process sign-in throttle for its demo workflow, but not email verification, password recovery, MFA, distributed rate controls, audit logging, or an enterprise identity provider. Use HTTPS, distributed rate limits, monitoring, backups, stronger account recovery, and a security review. Do not expose this development server directly to the public internet.
5. **Set privacy and operating policies.** Consult Sri Lankan legal/privacy professionals about applicable requirements before collecting real people's location data. Document purpose, consent, visibility, retention/deletion, contact details, incident response, and how drivers can stop/delete sharing. Minimize retained location data; the current app stores only each vehicle's latest fix but has no automatic expiry.
6. **Test with riders and accessibility in all three languages.** Ask Sinhala-, Tamil-, and English-speaking people to test route names, stop spelling, map usability, low-end Android phones, screen readers, and low-bandwidth conditions. The current interface has translated labels, but demo route/stop content needs review by fluent local speakers.
7. **Add realistic arrival information only after gathering evidence.** For predictions, collect operator-verified route shapes, stop sequences, and consented timestamped trips; measure GPS quality and traffic variance. Compare estimated arrivals against observed arrivals before publishing them, and label uncertainty clearly. Never present a demo estimate as an official schedule.
8. **Pilot, measure, iterate.** Start with one operator and one corridor. Track location freshness, opt-outs, position accuracy, rider-reported usefulness, data costs, and support issues. Fix reliability and consent problems before adding routes or operators.

### Production engineering still needed

Move from the single-process, SQLite prototype to a supported deployment architecture before a multi-operator launch: durable scalable storage, HTTPS hosting with secure cookies, verified operator/driver onboarding, automated backups, retention/deletion controls, operational monitoring, and recovery procedures. Add email verification, account recovery, MFA for privileged roles, rate limiting, audit logging, and formal privacy/consent terms; test reconnects, stale GPS, duplicate vehicle IDs, and weak connectivity. Map tiles and fonts are served by third parties; check their terms, availability, and privacy implications, or choose a suitable local/managed map provider.

## Data and privacy notes

- Driver location is requested only after a driver presses **Start sharing location**; this app does not request passenger location.
- Stop sharing or close the page to stop browser updates. This prototype does not offer background tracking.
- The browser sends the latest GPS fix at most once every four seconds. Vehicle positions are visible to anyone who can reach the app and are retained in the local SQLite file until manually deleted.
- Keep this prototype on localhost. It is not suitable for collecting real public GPS data until authentication, operating policy, deployment controls, and local legal review are complete.

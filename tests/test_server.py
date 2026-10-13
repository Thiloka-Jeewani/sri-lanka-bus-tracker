import json
import shutil
import threading
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer
from http.cookiejar import CookieJar

import server as bus_server
from server import Database, Handler, LocationError


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "test.sqlite3")
        self.driver = self.database.register({
            "name": "Test Driver", "email": "driver@example.com", "password": "long-test-password",
            "role": "driver", "consent": True,
        })
        self.operator = self.database.register({
            "name": "Test Operator", "email": "operator@example.com", "password": "long-test-password",
            "role": "operator", "organization": "Test Buses", "consent": True,
        })
        self.database.update_user_status(self.operator["id"], "active", "test-admin-id")
        self.database.create_fleet_vehicle(self.operator["id"], {
            "vehicleId": "BUS-1", "routeId": "colombo-fort-pettah",
        })
        self.database.assign_driver(self.operator["id"], "BUS-1", {"email": "driver@example.com"})

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_saves_and_lists_a_location(self):
        result = self.database.save_location({
            "lat": 6.9344,
            "lon": 79.8428,
            "accuracy": 18,
        }, self.driver)
        vehicle = self.database.list_vehicles()[0]

        self.assertEqual(result["vehicleId"], "BUS-1")
        self.assertEqual(result["routeId"], "colombo-fort-pettah")
        self.assertEqual(vehicle["status"], "live")
        self.assertAlmostEqual(vehicle["lat"], 6.9344)
        self.assertTrue(vehicle["demo"])

    def test_new_location_updates_existing_vehicle(self):
        first = {"vehicleId": "BUS-1", "routeId": "colombo-fort-pettah", "lat": 6.9344, "lon": 79.8428}
        self.database.save_location(first, self.driver)
        updated = {**first, "lat": 6.9388, "lon": 79.85}

        self.database.save_location(updated, self.driver)

        vehicles = self.database.list_vehicles()
        self.assertEqual(len(vehicles), 1)
        self.assertAlmostEqual(vehicles[0]["lat"], 6.9388)

    def test_suspending_operator_hides_and_stops_assigned_vehicle(self):
        self.database.save_location({"lat": 6.9344, "lon": 79.8428}, self.driver)
        self.database.update_user_status(self.operator["id"], "suspended", "test-admin-id")

        self.assertIsNone(self.database.driver_vehicle(self.driver["id"]))
        self.assertEqual(self.database.list_vehicles(), [])
        with self.assertRaises(PermissionError):
            self.database.save_location({"lat": 6.935, "lon": 79.843}, self.driver)

    def test_recreates_database_folder_and_schema_if_removed(self):
        shutil.rmtree(self.temp_dir.name)

        self.assertEqual(self.database.list_vehicles(), [])
        self.assertTrue(self.database.path.parent.is_dir())

    def test_rejects_invalid_or_out_of_country_locations(self):
        payload = {"vehicleId": "BUS-1", "routeId": "colombo-fort-pettah", "lat": 6.9, "lon": 79.8}
        for invalid in (
            {**payload, "lat": 0},
            {**payload, "lon": 0},
            {**payload, "lat": float("nan")},
            {**payload, "accuracy": float("nan")},
            None,
        ):
            with self.subTest(invalid=invalid), self.assertRaises(LocationError):
                self.database.save_location(invalid, self.driver)


class APITests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_database = bus_server.database
        bus_server.database = Database(Path(self.temp_dir.name) / "api.sqlite3")
        self.admin_password = "admin-test-password-123"
        admin_hash = bus_server.database.hash_password(self.admin_password)
        with bus_server.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO users (id, email, name, role, status, password_hash, created_at)
                VALUES ('test-admin-id', 'admin@example.com', 'Test Admin', 'admin', 'active', ?, '2026-01-01T00:00:00+00:00')
                """,
                (admin_hash,),
            )
        self.driver_password = "driver-test-password"
        self.driver = bus_server.database.register({
            "name": "Test Driver", "email": "driver@example.com", "password": self.driver_password,
            "role": "driver", "consent": True,
        })
        operator = bus_server.database.register({
            "name": "Test Operator", "email": "operator@example.com", "password": "operator-test-password",
            "role": "operator", "organization": "Test Buses", "consent": True,
        })
        bus_server.database.update_user_status(operator["id"], "active", "test-admin-id")
        bus_server.database.create_fleet_vehicle(operator["id"], {
            "vehicleId": "PILOT-1", "routeId": "colombo-fort-pettah",
        })
        bus_server.database.assign_driver(operator["id"], "PILOT-1", {"email": "driver@example.com"})
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.httpd.server_port}"

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()
        bus_server.database = self.original_database
        self.temp_dir.cleanup()

    def opener(self):
        return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def post_json(self, opener, path, payload, csrf_token=None):
        headers = {"Content-Type": "application/json"}
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with opener.open(request) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            try:
                return error.code, json.load(error)
            finally:
                error.close()

    def login(self, email, password):
        opener = self.opener()
        status, result = self.post_json(opener, "/api/auth/login", {"email": email, "password": password})
        self.assertEqual(status, 200)
        with opener.open(f"{self.base_url}/api/auth/me") as response:
            session = json.load(response)
        return opener, session["csrfToken"]

    def test_routes_and_location_api(self):
        with urllib.request.urlopen(f"{self.base_url}/api/routes") as response:
            routes = json.load(response)["routes"]
        self.assertEqual(routes[0]["id"], "colombo-fort-pettah")

        status, _ = self.post_json(self.opener(), "/api/locations", {"lat": 6.9344, "lon": 79.8428})
        self.assertEqual(status, 401)
        driver, csrf = self.login("driver@example.com", self.driver_password)
        status, result = self.post_json(
            driver, "/api/locations", {"lat": 6.9344, "lon": 79.8428, "accuracy": 20}, csrf,
        )
        self.assertEqual(status, 201)
        self.assertEqual(result["vehicle"]["vehicleId"], "PILOT-1")
        with urllib.request.urlopen(f"{self.base_url}/api/vehicles") as response:
            vehicles = json.load(response)["vehicles"]
        self.assertEqual(vehicles[0]["vehicleId"], "PILOT-1")

    def test_invalid_location_is_rejected_by_api(self):
        driver, csrf = self.login("driver@example.com", self.driver_password)
        status, result = self.post_json(
            driver, "/api/locations", {"lat": 0, "lon": 79.8428}, csrf,
        )
        self.assertEqual(status, 400)
        self.assertIn("Latitude", result["error"])

    def test_operator_and_authority_accounts_require_admin_approval(self):
        status, result = self.post_json(self.opener(), "/api/auth/register", {
            "name": "Transit Agency", "email": "authority@example.com",
            "password": "authority-password-123", "role": "authority",
            "organization": "Regional Transit Office", "consent": True,
        })
        self.assertEqual(status, 201)
        self.assertEqual(result["user"]["status"], "pending")
        status, result = self.post_json(self.opener(), "/api/auth/login", {
            "email": "authority@example.com", "password": "authority-password-123",
        })
        self.assertEqual(status, 403)

        admin, csrf = self.login("admin@example.com", self.admin_password)
        with admin.open(f"{self.base_url}/api/admin/users") as response:
            users = json.load(response)["users"]
        account = next(user for user in users if user["email"] == "authority@example.com")
        status, _ = self.post_json(
            admin, f"/api/admin/users/{account['id']}/status", {"status": "active"}, csrf,
        )
        self.assertEqual(status, 200)
        authority, _ = self.login("authority@example.com", "authority-password-123")
        with authority.open(f"{self.base_url}/api/auth/me") as response:
            self.assertEqual(json.load(response)["user"]["role"], "authority")

    def test_admin_dashboard_data_requires_admin_role(self):
        admin, _ = self.login("admin@example.com", self.admin_password)
        with admin.open(f"{self.base_url}/api/admin/summary") as response:
            summary = json.load(response)["summary"]
        self.assertEqual(summary["users"], 3)
        self.assertEqual(summary["vehicles"], 1)
        with admin.open(f"{self.base_url}/api/admin/fleet") as response:
            fleet = json.load(response)["vehicles"]
        self.assertEqual(fleet[0]["vehicleId"], "PILOT-1")
        self.assertEqual(fleet[0]["operatorEmail"], "operator@example.com")

        driver, _ = self.login("driver@example.com", self.driver_password)
        request = urllib.request.Request(f"{self.base_url}/api/admin/summary")
        with self.assertRaises(urllib.error.HTTPError) as error:
            driver.open(request)
        try:
            self.assertEqual(error.exception.code, 403)
        finally:
            error.exception.close()

        with urllib.request.urlopen(f"{self.base_url}/admin") as response:
            self.assertIn("Admin dashboard", response.read().decode("utf-8"))

    def test_admin_can_suspend_and_reactivate_stakeholder_accounts(self):
        operator, csrf = self.login("admin@example.com", self.admin_password)
        with operator.open(f"{self.base_url}/api/admin/users") as response:
            users = json.load(response)["users"]
        operator_user = next(user for user in users if user["role"] == "operator")
        for status in ("suspended", "active"):
            response_status, _ = self.post_json(
                operator,
                f"/api/admin/users/{operator_user['id']}/status",
                {"status": status},
                csrf,
            )
            self.assertEqual(response_status, 200)
            current = next(user for user in bus_server.database.list_users() if user["id"] == operator_user["id"])
            self.assertEqual(current["status"], status)

    def test_admin_can_change_email_after_confirming_current_password(self):
        admin, csrf = self.login("admin@example.com", self.admin_password)
        other_session, _ = self.login("admin@example.com", self.admin_password)

        status, result = self.post_json(
            admin,
            "/api/admin/account/email",
            {"email": "new-admin@example.com", "password": "incorrect-password"},
            csrf,
        )
        self.assertEqual(status, 403)
        self.assertIn("current password", result["error"])

        status, result = self.post_json(
            admin,
            "/api/admin/account/email",
            {"email": "operator@example.com", "password": self.admin_password},
            csrf,
        )
        self.assertEqual(status, 400)
        self.assertIn("already exists", result["error"])

        status, result = self.post_json(
            admin,
            "/api/admin/account/email",
            {"email": " New-Admin@Example.com ", "password": self.admin_password},
            csrf,
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["user"]["email"], "new-admin@example.com")
        with admin.open(f"{self.base_url}/api/auth/me") as response:
            current_session = json.load(response)
        self.assertEqual(current_session["user"]["email"], "new-admin@example.com")
        with other_session.open(f"{self.base_url}/api/auth/me") as response:
            self.assertIsNone(json.load(response)["user"])

        status, result = self.post_json(
            self.opener(),
            "/api/auth/login",
            {"email": "admin@example.com", "password": self.admin_password},
        )
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "Email or password is incorrect.")
        status, result = self.post_json(
            self.opener(),
            "/api/auth/login",
            {"email": "new-admin@example.com", "password": self.admin_password},
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["user"]["email"], "new-admin@example.com")

    def test_registration_rejects_invalid_roles_and_unapproved_admin_signup(self):
        for role in ([], "admin"):
            status, result = self.post_json(self.opener(), "/api/auth/register", {
                "name": "Invalid Account", "email": "invalid@example.lk",
                "password": "long-invalid-password", "role": role, "consent": True,
            })
            self.assertEqual(status, 400)
            self.assertIn("account type", result["error"])

    def test_first_admin_can_be_created_once_from_local_setup(self):
        with bus_server.database.connect() as connection:
            connection.execute("DELETE FROM users WHERE role = 'admin'")

        browser = self.opener()
        with browser.open(f"{self.base_url}/api/auth/setup-status") as response:
            self.assertTrue(json.load(response)["available"])

        status, result = self.post_json(browser, "/api/auth/setup-admin", {
            "name": "First Admin", "email": "first-admin@example.com",
            "password": "one-time-admin-password-123",
        })
        self.assertEqual(status, 201)
        self.assertEqual(result["user"]["role"], "admin")
        with browser.open(f"{self.base_url}/api/auth/me") as response:
            session = json.load(response)
        self.assertEqual(session["user"]["email"], "first-admin@example.com")

        status, result = self.post_json(browser, "/api/auth/setup-admin", {
            "name": "Second Admin", "email": "second-admin@example.com",
            "password": "one-time-admin-password-456",
        })
        self.assertEqual(status, 409)
        self.assertIn("already been set up", result["error"])
        self.assertTrue(bus_server.database.has_admin())

    def test_operator_can_register_fleet_and_assign_driver(self):
        operator, csrf = self.login("operator@example.com", "operator-test-password")
        status, result = self.post_json(
            operator, "/api/operator/fleet",
            {"vehicleId": "BUS-2", "routeId": "colombo-fort-pettah"}, csrf,
        )
        self.assertEqual(status, 201)
        self.assertEqual(result["vehicle"]["vehicleId"], "BUS-2")
        status, _ = self.post_json(
            operator, "/api/operator/fleet/BUS-2/assign",
            {"email": "driver@example.com"}, csrf,
        )
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()

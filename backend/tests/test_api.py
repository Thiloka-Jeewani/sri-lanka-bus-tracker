import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import backend.app.main as api


class ApiWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_override = patch.object(api, "DB_PATH", Path(self.temp_dir.name) / "test.sqlite3")
        self.database_override.start()
        self.client = TestClient(api.app, base_url="http://127.0.0.1")
        self.client.__enter__()
        self.admin_password = "secure-test-admin-password"
        with api.connect() as connection:
            connection.execute(
                """
                INSERT INTO users (id, email, name, role, status, password_hash, created_at)
                VALUES (?, ?, ?, 'admin', 'active', ?, ?)
                """,
                ("test-admin", "admin@example.com", "Test Admin", api.hash_password(self.admin_password), api.utc_now()),
            )

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.database_override.stop()
        self.temp_dir.cleanup()

    def login(self, email, password):
        response = self.client.post("/api/auth/login", json={"email": email, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        self.csrf = response.json()["csrfToken"]
        return response.json()["user"]

    def post_protected(self, path, payload):
        return self.client.post(path, json=payload, headers={"X-CSRF-Token": self.csrf})

    def test_operator_approval_fleet_assignment_location_and_stop_workflow(self):
        operator_response = self.client.post("/api/auth/register", json={
            "name": "Transit Operator",
            "email": "operator@example.com",
            "password": "operator-test-password",
            "role": "operator",
            "organization": "Test Buses",
            "consent": True,
        })
        self.assertEqual(operator_response.status_code, 201, operator_response.text)
        operator_user = operator_response.json()["user"]
        self.assertEqual(operator_user["status"], "pending")
        pending_login = self.client.post("/api/auth/login", json={
            "email": operator_user["email"], "password": "operator-test-password",
        })
        self.assertEqual(pending_login.status_code, 403)

        self.login("admin@example.com", self.admin_password)
        users = self.client.get("/api/admin/users")
        target = next(account for account in users.json()["users"] if account["id"] == operator_user["id"])
        approval = self.post_protected(f"/api/admin/users/{target['id']}/status", {"status": "active"})
        self.assertEqual(approval.status_code, 200, approval.text)

        driver_response = self.client.post("/api/auth/register", json={
            "name": "Test Driver",
            "email": "driver@example.com",
            "password": "driver-test-password",
            "role": "driver",
            "consent": True,
        })
        self.assertEqual(driver_response.status_code, 201, driver_response.text)

        self.login("operator@example.com", "operator-test-password")
        denied = self.client.post("/api/operator/fleet", json={
            "vehicleId": "BUS-1", "routeId": "colombo-fort-pettah",
        })
        self.assertEqual(denied.status_code, 403)
        created = self.post_protected("/api/operator/fleet", {
            "vehicleId": "BUS-1", "routeId": "colombo-fort-pettah",
        })
        self.assertEqual(created.status_code, 201, created.text)
        assignment = self.post_protected("/api/operator/fleet/BUS-1/assign", {"email": "driver@example.com"})
        self.assertEqual(assignment.status_code, 200, assignment.text)

        self.login("driver@example.com", "driver-test-password")
        location = self.post_protected("/api/locations", {"lat": 6.9344, "lon": 79.8428, "accuracy": 15})
        self.assertEqual(location.status_code, 201, location.text)
        self.assertEqual(location.json()["vehicle"]["vehicleId"], "BUS-1")
        self.assertEqual(len(self.client.get("/api/vehicles").json()["vehicles"]), 1)

        stopped = self.post_protected("/api/driver/location/stop", {})
        self.assertEqual(stopped.status_code, 200, stopped.text)
        self.assertTrue(stopped.json()["locationRemoved"])
        self.assertEqual(self.client.get("/api/vehicles").json()["vehicles"], [])

    def test_registration_and_location_validation(self):
        bad_role = self.client.post("/api/auth/register", json={
            "name": "Not an Admin",
            "email": "not-admin@example.com",
            "password": "some-valid-password",
            "role": "admin",
            "consent": True,
        })
        self.assertEqual(bad_role.status_code, 422)

        self.client.post("/api/auth/register", json={
            "name": "Test Driver",
            "email": "driver@example.com",
            "password": "driver-test-password",
            "role": "driver",
            "consent": True,
        })
        self.login("driver@example.com", "driver-test-password")
        invalid_location = self.post_protected("/api/locations", {"lat": 0, "lon": 79.8428})
        self.assertEqual(invalid_location.status_code, 422)

    def test_admin_account_email_change_reauthenticates_and_invalidates_other_sessions(self):
        self.login("admin@example.com", self.admin_password)
        old_token = self.client.cookies.get("buslk_session")
        other_browser = TestClient(api.app, base_url="http://127.0.0.1")
        other_browser.__enter__()
        other_login = other_browser.post("/api/auth/login", json={
            "email": "admin@example.com", "password": self.admin_password,
        })
        self.assertEqual(other_login.status_code, 200)
        changed = self.post_protected("/api/admin/account/email", {
            "email": "new-admin@example.com", "password": "incorrect-password",
        })
        self.assertEqual(changed.status_code, 403)
        changed = self.post_protected("/api/admin/account/email", {
            "email": "new-admin@example.com", "password": self.admin_password,
        })
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(changed.json()["user"]["email"], "new-admin@example.com")
        self.assertEqual(self.client.cookies.get("buslk_session"), old_token)
        self.assertIsNone(other_browser.get("/api/auth/me").json()["user"])
        other_browser.__exit__(None, None, None)


if __name__ == "__main__":
    unittest.main()

import os
import sys
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch


CORE_DIR = Path(__file__).resolve().parents[1]
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

os.environ.setdefault("AUTO_MIGRATE_ON_STARTUP", "0")
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret")

from config.app import create_app  # noqa: E402
from apps.tasks.views import _format_dashboard_date  # noqa: E402


def _period_key(start, end):
    if isinstance(start, datetime) and isinstance(end, datetime):
        delta_days = (end - start).days
        if delta_days <= 1:
            return "day"
        if delta_days <= 7:
            return "week"
        return "month"

    if isinstance(start, date) and isinstance(end, date):
        delta_days = (end - start).days
        if delta_days <= 7:
            return "week"
        return "month"

    return "day"


class FakeDashboardCursor:
    def __init__(self):
        self.last_query = ""
        self.params = ()

    def execute(self, query, params=None):
        self.last_query = " ".join(str(query).split())
        self.params = params or ()

    def fetchone(self):
        if "SELECT menu_key, can_view FROM role_menu_permissions" in self.last_query:
            return None

        period = _period_key(self.params[1], self.params[2])
        totals = {
            "day": {"budgets": 2, "waiting": 1, "approved": 1, "clients": 3},
            "week": {"budgets": 5, "waiting": 2, "approved": 3, "clients": 4},
            "month": {"budgets": 9, "waiting": 4, "approved": 6, "clients": 8},
        }[period]

        if "FROM budgets" in self.last_query and "status) = 'sent'" in self.last_query:
            return {"total": totals["waiting"]}
        if "FROM budgets" in self.last_query and "status) = 'approved'" in self.last_query:
            return {"total": totals["approved"]}
        if "FROM budgets" in self.last_query:
            return {"total": totals["budgets"]}
        if "FROM clients" in self.last_query:
            return {"total": totals["clients"]}
        return {"total": 0}

    def fetchall(self):
        if "SELECT menu_key, can_view FROM role_menu_permissions" in self.last_query:
            return []
        return []


class FakeDashboardConnection:
    def cursor(self, dictionary=False):
        return FakeDashboardCursor()

    def close(self):
        return None

    def commit(self):
        return None

    def rollback(self):
        return None


class DashboardTests(unittest.TestCase):
    def test_format_dashboard_date_uses_portuguese_month_name(self):
        self.assertEqual(_format_dashboard_date(datetime(2026, 4, 20, 10, 0, 0)), "20 de abril de 2026")

    @classmethod
    def setUpClass(cls):
        cls.tasks_db_patcher = patch("apps.tasks.views.get_db_connection", return_value=FakeDashboardConnection())
        cls.menu_db_patcher = patch("config.app.get_db_connection", return_value=FakeDashboardConnection())
        cls.tasks_db_patcher.start()
        cls.menu_db_patcher.start()

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.tasks_db_patcher.stop()
        cls.menu_db_patcher.stop()

    def setUp(self):
        with self.client.session_transaction() as session:
            session["id"] = 1
            session["role"] = "admin"

    def test_dashboard_embeds_period_stats_and_subtitle_updates(self):
        response = self.client.get("/dashboard")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('data-key="budgets">2<', html)
        self.assertIn('"month": {"approved": 6, "budgets": 9, "clients": 8, "waiting": 4}', html)
        self.assertIn("updateStatSubtitles(period)", html)
        self.assertIn("Clientes cadastrados no mes", html)
        self.assertIn("20 de abril de 2026", html)


if __name__ == "__main__":
    unittest.main()

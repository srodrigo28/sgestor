import os
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch


CORE_DIR = Path(__file__).resolve().parents[1]
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

os.environ.setdefault("AUTO_MIGRATE_ON_STARTUP", "0")
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret")

from config.app import create_app  # noqa: E402


class FakeCursor:
    def __init__(self):
        self.last_query = ""

    def execute(self, query, params=None):
        self.last_query = " ".join(str(query).split())

    def fetchone(self):
        if "SELECT COUNT(*) as total FROM financial_income" in self.last_query:
            return {"total": 1}
        if "SELECT COUNT(*) as total FROM financial_expenses" in self.last_query:
            return {"total": 1}
        return {}

    def fetchall(self):
        if "SELECT menu_key, can_view FROM role_menu_permissions" in self.last_query:
            return []

        if "SELECT * FROM financial_income" in self.last_query:
            return [{
                "id": 1,
                "description": "Contrato mensal",
                "amount": 1200.0,
                "category": "serviço",
                "payment_type": "pix",
                "status": "received",
                "entry_date": date(2026, 4, 10),
                "category_id": 1,
                "category_icon": "🛠️",
                "category_color": "#8b5cf6",
            }]

        if "SELECT * FROM financial_expenses" in self.last_query:
            return [{
                "id": 2,
                "description": "Internet",
                "amount": 199.9,
                "category": "Operacional",
                "payment_type": "boleto",
                "status": "pending",
                "due_date": date(2026, 4, 15),
                "category_id": 2,
                "category_icon": "🏭",
                "category_color": "#f97316",
            }]

        return []

    def close(self):
        return None


class FakeConnection:
    def cursor(self, dictionary=False):
        return FakeCursor()

    def close(self):
        return None

    def commit(self):
        return None

    def rollback(self):
        return None


class FinancialFilterTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_db_patcher = patch("apps.financial.views.get_db_connection", return_value=FakeConnection())
        cls.menu_db_patcher = patch("config.app.get_db_connection", return_value=FakeConnection())
        cls.categories_patcher = patch(
            "apps.financial.views._fetch_financial_categories",
            side_effect=lambda cursor, user_id, kind: [{
                "id": 1 if kind == "income" else 2,
                "name": "serviço" if kind == "income" else "Operacional",
                "icon": "🛠️" if kind == "income" else "🏭",
                "color": "#8b5cf6" if kind == "income" else "#f97316",
                "usage_count": 1,
            }],
        )
        cls.attach_meta_patcher = patch("apps.financial.views._attach_category_meta", side_effect=lambda records, categories_by_name: None)
        cls.income_stats_patcher = patch(
            "apps.financial.views._income_stats",
            return_value={"total_month": 1200.0, "received_month": 1200.0, "pending_month": 0.0, "avg_daily_month": 120.0},
        )
        cls.expense_stats_patcher = patch(
            "apps.financial.views._expense_stats",
            return_value={"total_month": 199.9, "paid_month": 0.0, "pending_month": 199.9, "avg_daily_month": 20.0},
        )
        cls.income_charts_patcher = patch(
            "apps.financial.views._income_charts",
            return_value=(
                {"labels": ["01/04"], "values": [1200.0]},
                {"labels": ["Serviço"], "values": [1200.0]},
            ),
        )
        cls.expense_charts_patcher = patch(
            "apps.financial.views._expense_charts",
            return_value=(
                {"labels": ["01/04"], "values": [199.9]},
                {"labels": ["Operacional"], "values": [199.9]},
            ),
        )

        for patcher in [
            cls.client_db_patcher,
            cls.menu_db_patcher,
            cls.categories_patcher,
            cls.attach_meta_patcher,
            cls.income_stats_patcher,
            cls.expense_stats_patcher,
            cls.income_charts_patcher,
            cls.expense_charts_patcher,
        ]:
            patcher.start()

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        for patcher in [
            cls.expense_charts_patcher,
            cls.income_charts_patcher,
            cls.expense_stats_patcher,
            cls.income_stats_patcher,
            cls.attach_meta_patcher,
            cls.categories_patcher,
            cls.menu_db_patcher,
            cls.client_db_patcher,
        ]:
            patcher.stop()

    def setUp(self):
        with self.client.session_transaction() as session:
            session["id"] = 1
            session["role"] = "admin"

    def test_income_filters_do_not_apply_on_search_blur(self):
        response = self.client.get("/financial/income?month=2026-04")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('onblur="applyFilters()"', html)
        self.assertIn('<select id="monthFilter" onchange="applyFilters()"', html)
        self.assertIn('<select id="historyMonthSelect" onchange="updateCharts()"', html)
        self.assertIn('<option value="2026-04" selected>Apr/26</option>'.replace("Apr", "Abr"), html)

    def test_expense_filters_do_not_apply_on_search_blur(self):
        response = self.client.get("/financial/expenses?month=2026-04")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('onblur="applyExpenseFilters()"', html)
        self.assertIn('<select id="monthFilter" onchange="applyExpenseFilters()"', html)
        self.assertIn('<select id="expenseHistoryMonthSelect" onchange="updateExpenseCharts()"', html)
        self.assertIn('<option value="2026-04" selected>Abr/26</option>', html)


if __name__ == "__main__":
    unittest.main()

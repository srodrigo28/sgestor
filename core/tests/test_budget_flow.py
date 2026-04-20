import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


CORE_DIR = Path(__file__).resolve().parents[1]
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

os.environ.setdefault("AUTO_MIGRATE_ON_STARTUP", "0")
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret")

from config.app import create_app  # noqa: E402
from apps.budgets.views import _build_status_update_fields, _resolve_status_transition  # noqa: E402


class FakeBudgetCursor:
    def __init__(self):
        self.last_query = ""
        self.params = ()
        self.lastrowid = 77

    def execute(self, query, params=None):
        self.last_query = " ".join(str(query).split())
        self.params = params or ()

    def fetchone(self):
        query = self.last_query

        if "SELECT id, name FROM clients WHERE id = %s AND user_id = %s" in query:
            client_id = int(self.params[0])
            if client_id == 1:
                return {"id": 1, "name": "Cliente Teste"}
            return None

        if "SELECT name, quantity FROM products WHERE id = %s AND user_id = %s" in query:
            return {"name": "Pastilha", "quantity": 1}

        return None

    def fetchall(self):
        if "SELECT menu_key, can_view FROM role_menu_permissions" in self.last_query:
            return []
        return []


class FakeBudgetConnection:
    def cursor(self, dictionary=False):
        return FakeBudgetCursor()

    def commit(self):
        return None

    def rollback(self):
        return None

    def close(self):
        return None


class BudgetFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.budget_db_patcher = patch("apps.budgets.views.get_db_connection", return_value=FakeBudgetConnection())
        cls.menu_db_patcher = patch("config.app.get_db_connection", return_value=FakeBudgetConnection())
        cls.budget_db_patcher.start()
        cls.menu_db_patcher.start()

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.budget_db_patcher.stop()
        cls.menu_db_patcher.stop()

    def setUp(self):
        with self.client.session_transaction() as session:
            session["id"] = 1
            session["role"] = "admin"

    def test_budget_requires_existing_selected_client(self):
        response = self.client.post(
            "/budgets/save",
            json={
                "client_name": "Cliente Avulso",
                "approval_status": "sent",
                "budget_date": "2026-04-20",
                "vehicle_plate": "ABC1234",
                "items": [{"desc": "Servico", "qty": 1, "price": 100, "total": 100, "is_service": True}],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("cliente já cadastrado", response.get_json()["error"])

    def test_budget_blocks_insufficient_stock_on_approval(self):
        response = self.client.post(
            "/budgets/save",
            json={
                "client_id": 1,
                "client_name": "Cliente Teste",
                "approval_status": "approved",
                "budget_date": "2026-04-20",
                "vehicle_plate": "ABC1234",
                "items": [{"desc": "Pastilha", "qty": 2, "price": 50, "total": 100, "product_id": 3}],
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Estoque insuficiente", response.get_json()["error"])

    def test_status_transition_blocks_delivery_without_pickup(self):
        approval, stage, error = _resolve_status_transition("approved", "budget", "approved", "delivered")

        self.assertIsNone(approval)
        self.assertIsNone(stage)
        self.assertIn("Retirada", error)

    def test_status_update_fields_clear_old_timestamps_when_returning_to_budget(self):
        fields, params = _build_status_update_fields("sent", "budget", "2026-04-20 10:00:00")

        self.assertEqual(fields[:3], ["status = %s", "approval_status = %s", "stage_status = %s"])
        self.assertEqual(params[:3], ["sent", "sent", "budget"])
        self.assertEqual(params[3], None)
        self.assertEqual(params[4], None)
        self.assertEqual(params[5], None)
        self.assertEqual(params[6], None)


if __name__ == "__main__":
    unittest.main()

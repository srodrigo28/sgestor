import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch


CORE_DIR = Path(__file__).resolve().parents[1]
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

os.environ.setdefault("AUTO_MIGRATE_ON_STARTUP", "0")
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret")

from config.app import create_app  # noqa: E402


CLIENT_COLUMNS = [
    "id",
    "user_id",
    "name",
    "legal_name",
    "trade_name",
    "sector",
    "contract_start_date",
    "cpf",
    "phone1",
    "phone2",
    "cep",
    "address",
    "address_number",
    "complement",
    "neighborhood",
    "city",
    "state",
    "created_at",
]


class FakeCursor:
    def __init__(self):
        self.last_query = ""

    def execute(self, query, params=None):
        self.last_query = " ".join(str(query).split())

    def fetchall(self):
        query = self.last_query

        if "SHOW COLUMNS FROM clients" in query:
            return [{"Field": column} for column in CLIENT_COLUMNS]

        if "SELECT menu_key, can_view FROM role_menu_permissions" in query:
            return []

        if "SELECT DISTINCT sector FROM clients" in query:
            return [{"sector": "Residencial"}]

        if "SELECT DATE(created_at) as date, COUNT(*) as count" in query:
            return []

        if "SELECT sector, COUNT(*) as count FROM clients" in query:
            return [{"sector": "Residencial", "count": 1}]

        if "FROM clients WHERE user_id = %s" in query and "ORDER BY created_at DESC" in query:
            return [
                {
                    "id": 1,
                    "name": "Ana Maria",
                    "legal_name": "Ana Maria LTDA",
                    "trade_name": "Ana Maria Store",
                    "sector": "Residencial",
                    "contract_start_date": "2026-03-10",
                    "cpf": "123.456.789-00",
                    "phone1": "(62) 99999-0000",
                    "phone2": "(62) 3333-4444",
                    "cep": "74000-000",
                    "address": "Rua Central",
                    "address_number": "123",
                    "complement": "Sala 2",
                    "neighborhood": "Centro",
                    "city": "Goiania",
                    "state": "GO",
                    "created_at": datetime(2026, 3, 10),
                }
            ]

        return []

    def fetchone(self):
        query = self.last_query

        if "COUNT(*) as total FROM clients" in query:
            return {"total": 1}

        return None


class FakeConnection:
    def cursor(self, dictionary=False):
        return FakeCursor()

    def commit(self):
        return None

    def rollback(self):
        return None

    def close(self):
        return None


class ClientsFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_db_patcher = patch("apps.clients.views.get_db_connection", return_value=FakeConnection())
        cls.menu_db_patcher = patch("config.app.get_db_connection", return_value=FakeConnection())
        cls.client_db_patcher.start()
        cls.menu_db_patcher.start()

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.client_db_patcher.stop()
        cls.menu_db_patcher.stop()

    def setUp(self):
        with self.client.session_transaction() as session:
            session["id"] = 1
            session["role"] = "admin"

    def test_clients_form_renders_expected_names_and_placeholders(self):
        response = self.client.get("/clients")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Complementar", html)
        self.assertIn('name="legal_name"', html)
        self.assertIn('placeholder="Ex: Empresa Silva LTDA"', html)
        self.assertIn('name="trade_name"', html)
        self.assertIn('placeholder="Ex: Silva Auto Pecas"', html)
        self.assertIn('name="contract_start_date"', html)
        self.assertIn("Razão Social", html)
        self.assertIn("Nome Fantasia", html)
        self.assertIn("Início do Contrato", html)

    def test_clients_form_keeps_existing_registration_fields(self):
        response = self.client.get("/clients")
        html = response.get_data(as_text=True)

        self.assertIn('name="name"', html)
        self.assertIn('placeholder="Ex: Joao da Silva"', html)
        self.assertIn('name="cpf"', html)
        self.assertIn('placeholder="000.000.000-00"', html)
        self.assertIn('id="cnpjInput"', html)
        self.assertIn('placeholder="00.000.000/0000-00"', html)
        self.assertIn('name="phone1"', html)
        self.assertIn('placeholder="(XX) XXXXX-XXXX"', html)
        self.assertNotIn('name="sector"', html)

    def test_edit_buttons_include_company_fields_for_modal_population(self):
        response = self.client.get("/clients")
        html = response.get_data(as_text=True)

        self.assertIn('data-legal-name="Ana Maria LTDA"', html)
        self.assertIn('data-trade-name="Ana Maria Store"', html)
        self.assertIn('data-contract-start-date="2026-03-10"', html)


if __name__ == "__main__":
    unittest.main()

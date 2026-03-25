from flask import Flask

from apps.admin.views import admin_bp
from apps.auth.views import auth_bp
from apps.budgets.views import budgets_bp
from apps.clients.views import clients_bp
from apps.db_manager.views import db_bp
from apps.financial.views import financial_bp
from apps.mechanics.views import mechanics_bp
from apps.products.views import products_bp
from apps.schedule.views import schedule_bp
from apps.services.views import services_bp
from apps.tasks.views import tasks_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(financial_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(db_bp)
    app.register_blueprint(mechanics_bp)

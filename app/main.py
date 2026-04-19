from __future__ import annotations

import logging
import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api import ad_copy, auth, customer, products, reset, session, trend
from app.config import load_settings
from app.data.repositories.ai_generation_log_repository import AIGenerationLogRepository
from app.data.repositories.customer_repository import CustomerRepository
from app.data.repositories.product_repository import ProductRepository
from app.data.sql_client import SqlClient
from app.middleware.error_handler import install_error_handlers
from app.state import AppState

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

templates = Jinja2Templates(directory="app/templates")


def create_app() -> FastAPI:
    settings = load_settings()
    app = FastAPI(title="AI Commercial Assistant POC", version="0.1.0")
    sql_client = None if settings.is_test else SqlClient(settings)
    app.state.container = AppState(
        settings=settings,
        product_repository=ProductRepository(sql_client),
        customer_repository=CustomerRepository(sql_client, settings),
        ai_log_repository=AIGenerationLogRepository(sql_client),
    )
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    install_error_handlers(app)
    app.include_router(auth.router)
    app.include_router(session.router)
    app.include_router(products.router)
    app.include_router(customer.router)
    app.include_router(trend.router)
    app.include_router(ad_copy.router)
    app.include_router(reset.router)

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        return templates.TemplateResponse("main.html", {"request": request})

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("WEB_APP_PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)

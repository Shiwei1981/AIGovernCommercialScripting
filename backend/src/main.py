from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.middleware.request_context import RequestContextMiddleware
from src.api.routes import audit_trace, generation_details, generation_history, generations
from src.config.settings import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.app_base_url],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.add_middleware(RequestContextMiddleware)

app.include_router(generations.router, prefix=settings.api_prefix)
app.include_router(generation_history.router, prefix=settings.api_prefix)
app.include_router(generation_details.router, prefix=settings.api_prefix)
app.include_router(audit_trace.router, prefix=settings.api_prefix)


@app.get('/healthz')
def healthz() -> dict[str, str]:
    return {'status': 'ok'}


frontend_dist_dir = Path(__file__).resolve().parents[2] / 'frontend_dist'
if frontend_dist_dir.exists():
    # Mount frontend static build only when dist assets are present.
    app.mount('/', StaticFiles(directory=str(frontend_dist_dir), html=True), name='frontend')

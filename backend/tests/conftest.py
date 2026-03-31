import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault('ENTRA_TENANT_ID', 'tenant-1234')
os.environ.setdefault('ENTRA_CLIENT_ID', 'client-1234')
os.environ.setdefault('ENTRA_AUTHORITY', 'https://login.microsoftonline.com/tenant-1234')
os.environ.setdefault('ENTRA_REDIRECT_URI', 'https://localhost/auth/callback')
os.environ.setdefault('AZURE_OPENAI_ENDPOINT', 'https://example.openai.azure.com')
os.environ.setdefault('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini')
os.environ.setdefault('AZURE_OPENAI_API_VERSION', '2024-10-21')
os.environ.setdefault('AI_SEARCH_ENDPOINT', 'https://example.search.windows.net')
os.environ.setdefault('AI_SEARCH_INDEX_NAME', 'commercialscripting-news')
os.environ.setdefault('AI_SEARCH_ALLOWLIST_PATH', str(ROOT / 'docs' / 'validation' / 'allowlist.txt'))
os.environ.setdefault('AZURE_SQL_CONNECTIONSTRING', 'Server=tcp:example.database.windows.net;Authentication=ActiveDirectoryDefault;Encrypt=yes;')
os.environ.setdefault('GOVERNANCE_SQL_SCHEMA', 'governance_history')
os.environ.setdefault('APP_BASE_URL', 'https://localhost')
os.environ.setdefault('API_BASE_URL', 'https://localhost/api')
os.environ.setdefault('TLS_CERT_PATH', '')
os.environ.setdefault('TLS_KEY_PATH', '')
os.environ.setdefault('AUDIT_CONTRACT_VERSION', '0.1.0')

(Path(ROOT / 'docs' / 'validation' / 'allowlist.txt')).write_text('news.example.com\n', encoding='utf-8')

from src.main import app  # noqa: E402


def _claims_token() -> str:
    return 'eyJhbGciOiJub25lIn0.eyJhdWQiOiJjbGllbnQtMTIzNCIsImlzcyI6Imh0dHBzOi8vbG9naW4ubWljcm9zb2Z0b25saW5lLmNvbS90ZW5hbnQtMTIzNC92Mi4wIiwidGlkIjoidGVuYW50LTEyMzQiLCJvaWQiOiJ1c2VyLTEyMyIsIm5hbWUiOiJUZXN0IFVzZXIifQ.'


def auth_headers() -> dict[str, str]:
    return {'Authorization': f'Bearer {_claims_token()}'}


import pytest


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def bearer_headers():
    return auth_headers()

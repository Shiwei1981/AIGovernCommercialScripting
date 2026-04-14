from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'CommercialScripting API'
    api_prefix: str = '/api'

    entra_tenant_id: str = Field(..., alias='ENTRA_TENANT_ID')
    entra_client_id: str = Field(..., alias='ENTRA_CLIENT_ID')
    entra_authority: str = Field(..., alias='ENTRA_AUTHORITY')
    entra_redirect_uri: str = Field(..., alias='ENTRA_REDIRECT_URI')

    azure_openai_endpoint: str = Field(..., alias='AZURE_OPENAI_ENDPOINT')
    azure_openai_deployment: str = Field(..., alias='AZURE_OPENAI_DEPLOYMENT')
    azure_openai_api_version: str = Field(..., alias='AZURE_OPENAI_API_VERSION')
    azure_openai_api_key: str = Field('', alias='AZURE_OPENAI_API_KEY')

    ai_search_endpoint: str = Field(..., alias='AI_SEARCH_ENDPOINT')
    ai_search_index_name: str = Field(..., alias='AI_SEARCH_INDEX_NAME')
    ai_search_allowlist_path: str = Field(..., alias='AI_SEARCH_ALLOWLIST_PATH')
    ai_search_api_key: str = Field('', alias='AI_SEARCH_API_KEY')

    azure_sql_connectionstring: str = Field(..., alias='AZURE_SQL_CONNECTIONSTRING')
    governance_sql_schema: str = Field('governance_history', alias='GOVERNANCE_SQL_SCHEMA')

    app_base_url: str = Field(..., alias='APP_BASE_URL')
    api_base_url: str = Field(..., alias='API_BASE_URL')
    tls_cert_path: str = Field('', alias='TLS_CERT_PATH')
    tls_key_path: str = Field('', alias='TLS_KEY_PATH')

    audit_contract_version: str = Field('0.1.0', alias='AUDIT_CONTRACT_VERSION')


@lru_cache
def get_settings() -> Settings:
    return Settings()

from __future__ import annotations

from azure.identity import ClientSecretCredential
from openai import AzureOpenAI

from app.config import Settings


def create_azure_openai_client(settings: Settings) -> AzureOpenAI:
    credential = ClientSecretCredential(
        tenant_id=settings.azure_tenant_id,
        client_id=settings.azure_client_id,
        client_secret=settings.azure_client_secret,
    )

    def token_provider() -> str:
        return credential.get_token("https://cognitiveservices.azure.com/.default").token

    return AzureOpenAI(
        azure_endpoint=settings.openai_endpoint,
        api_version=settings.openai_api_version,
        azure_ad_token_provider=token_provider,
    )


def invoke_model(settings: Settings, prompt: str, model_name: str | None = None) -> str:
    client = create_azure_openai_client(settings)
    deployment = model_name or settings.openai_deployment
    response = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return (response.choices[0].message.content or "").strip()

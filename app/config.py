"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""

    api_key: str = "default-api-key"
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4.1"
    azure_openai_api_version: str = "2024-05-01-preview"
    basic_auth_username: str = "admin"
    basic_auth_password: str = "password"

    entra_id_tenant_id: str = ""
    entra_id_client_id: str = ""
    entra_id_authorized_upns: str = ""
    entra_id_authorized_app_ids: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}

    def get_authorized_upns(self) -> list[str]:
        """Parse comma-separated UPNs into a list."""
        if not self.entra_id_authorized_upns:
            return []
        return [u.strip() for u in self.entra_id_authorized_upns.split(",") if u.strip()]

    def get_authorized_app_ids(self) -> list[str]:
        """Parse comma-separated app IDs into a list."""
        if not self.entra_id_authorized_app_ids:
            return []
        return [a.strip() for a in self.entra_id_authorized_app_ids.split(",") if a.strip()]


settings = Settings()

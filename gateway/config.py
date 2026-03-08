import logging
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Runtime configuration for the MyFortress service."""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8100)
    log_level: str = Field(default="info")

    # Service auth/rate limiting
    api_key: Optional[str] = Field(
        default=None, description="Static API key required for requests (optional)"
    )
    request_timeout: float = Field(default=5.0, description="Default HTTP timeout")
    max_retries: int = Field(default=2, description="HTTP retry attempts for upstreams")
    structured_logging: bool = Field(default=False, description="Emit JSON logs if true")
    rate_limit_per_minute: int = Field(default=120, description="Requests per minute per client")
    rate_limit_window_seconds: int = Field(default=60, description="Rate limit window in seconds")

    # Home Merlin
    home_assistant_url: Optional[str] = Field(default=None)
    home_assistant_token: Optional[str] = Field(default=None)
    home_assistant_entities: List[str] = Field(default_factory=list)
    home_assistant_timeout: float = Field(default=5.0)
    home_assistant_verify_ssl: bool = Field(default=True)

    # Frigate
    frigate_url: Optional[str] = Field(default=None)
    frigate_api_key: Optional[str] = Field(default=None)
    frigate_cameras: List[str] = Field(default_factory=list)
    frigate_timeout: float = Field(default=5.0)

    # Caching / telemetry
    snapshot_cache_ttl: float = Field(default=10.0, description="Seconds")

    # AAS Intelligence Integration
    aas_hub_url: Optional[str] = Field(
        default="http://localhost:8000",
        description="URL of the AAS Hub for intelligence services",
    )

    @field_validator("home_assistant_url", "frigate_url", mode="after")
    @classmethod
    def validate_urls(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    def check_upstreams(self):
        """Log warnings if critical upstreams are missing."""
        if not self.home_assistant_url:
            logger.warning("HOMEGATEWAY_HOME_ASSISTANT_URL is not set")
        if not self.frigate_url:
            logger.warning("HOMEGATEWAY_FRIGATE_URL is not set")

    model_config = SettingsConfigDict(
        env_prefix="HOMEGATEWAY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()

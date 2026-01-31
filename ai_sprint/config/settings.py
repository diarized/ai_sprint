"""Configuration settings using Pydantic."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GeneralSettings(BaseSettings):
    """General application settings."""

    database_path: str = Field(default="~/.ai-sprint/beads.db")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    log_file: str = Field(default="~/.ai-sprint/logs/ai-sprint.log")


class AgentSettings(BaseSettings):
    """Agent configuration settings."""

    max_developers: int = Field(default=3, ge=1, le=10)
    max_testers: int = Field(default=3, ge=1, le=10)
    polling_interval_seconds: int = Field(default=30, ge=1)


class TimeoutSettings(BaseSettings):
    """Timeout configuration settings."""

    agent_heartbeat_seconds: int = Field(default=60, ge=10)
    agent_hung_seconds: int = Field(default=300, ge=60)
    task_max_duration_seconds: int = Field(default=7200, ge=60)
    merge_timeout_seconds: int = Field(default=300, ge=30)


class QualitySettings(BaseSettings):
    """Quality gate threshold settings."""

    coverage_threshold: int = Field(default=80, ge=0, le=100)
    mutation_threshold: int = Field(default=80, ge=0, le=100)
    complexity_flag: int = Field(default=10, ge=1)
    complexity_max: int = Field(default=15, ge=1)


class SecuritySettings(BaseSettings):
    """Security threshold settings."""

    critical_cve_max: int = Field(default=0, ge=0)
    high_cve_max: int = Field(default=0, ge=0)
    medium_cve_max: int = Field(default=5, ge=0)


class ModelSettings(BaseSettings):
    """AI model selection settings."""

    manager: Literal["haiku", "sonnet", "opus"] = Field(default="haiku")
    cab: Literal["haiku", "sonnet", "opus"] = Field(default="haiku")
    refinery: Literal["haiku", "sonnet", "opus"] = Field(default="sonnet")
    librarian: Literal["haiku", "sonnet", "opus"] = Field(default="sonnet")
    developer: Literal["haiku", "sonnet", "opus"] = Field(default="sonnet")
    tester: Literal["haiku", "sonnet", "opus"] = Field(default="haiku")


class Settings(BaseSettings):
    """Complete AI Sprint configuration."""

    model_config = SettingsConfigDict(
        env_prefix="AI_SPRINT_",
        env_nested_delimiter="__",
        toml_file="~/.ai-sprint/ai-sprint.toml",
        extra="ignore",
    )

    general: GeneralSettings = Field(default_factory=GeneralSettings)
    agents: AgentSettings = Field(default_factory=AgentSettings)
    timeouts: TimeoutSettings = Field(default_factory=TimeoutSettings)
    quality: QualitySettings = Field(default_factory=QualitySettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    models: ModelSettings = Field(default_factory=ModelSettings)

    @classmethod
    def load(cls, config_path: str | None = None) -> "Settings":
        """
        Load settings from TOML file or environment variables.

        Args:
            config_path: Optional path to TOML config file

        Returns:
            Settings instance with loaded configuration
        """
        if config_path:
            path = Path(config_path).expanduser()
            if path.exists():
                return cls(_env_file=str(path))  # type: ignore
        return cls()

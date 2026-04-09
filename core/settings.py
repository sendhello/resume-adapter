from logging import config as logging_config
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

from core.logger import LOGGING

logging_config.dictConfig(LOGGING)

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def _load_yaml_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


_config = _load_yaml_config()


class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    debug: bool = False

    # API keys (from .env only)
    openai_api_key: SecretStr = Field(validation_alias="OPENAI_API_KEY")
    openai_organization_id: str = Field(validation_alias="OPENAI_ORGANIZATION_ID")
    openai_project_id: str = Field(validation_alias="OPENAI_PROJECT_ID")
    anthropic_api_key: Optional[SecretStr] = Field(None, validation_alias="ANTHROPIC_API_KEY")

    # Personal (from config.yaml)
    personal_name: str = _config["personal"]["name"]
    personal_phone: str = _config["personal"]["phone"]
    personal_email: str = _config["personal"]["email"]
    personal_linkedin: str = _config["personal"]["linkedin"]
    personal_github: str = _config["personal"].get("github", "")
    personal_location: str = _config["personal"]["location"]
    personal_work_rights: str = _config["personal"]["work_rights"]
    personal_sponsorship_note: str = _config["personal"].get("sponsorship_note", "")

    # Paths (from config.yaml)
    output_dir: str = _config["paths"]["output_dir"]
    vacancy_file: str = _config["paths"].get("vacancy_file", "vacancy.txt")

    # AI (from config.yaml, overridable via CLI)
    default_provider: str = _config["ai"]["default_provider"]
    openai_model: str = _config["ai"]["openai_model"]
    claude_model: str = _config["ai"]["claude_model"]

    # Resume templates (from config.yaml)
    default_resume_type: str = _config["resume"]["default_type"]
    resume_templates: dict[str, str] = _config["resume"]["templates"]

    def get_resume_path(self, resume_type: str) -> str:
        if resume_type not in self.resume_templates:
            available = ", ".join(self.resume_templates.keys())
            raise ValueError(f"Unknown resume type '{resume_type}'. Available: {available}")
        return self.resume_templates[resume_type]


settings = Settings()

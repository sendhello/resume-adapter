from logging import config as logging_config
from typing import Optional

from pydantic import AliasChoices, Field, RedisDsn, SecretStr
from pydantic_settings import BaseSettings
from openai.types.shared.chat_model import ChatModel
from core.logger import LOGGING

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)


class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    debug: bool = False

    openai_api_key: SecretStr = Field(validation_alias="OPENAI_API_KEY")
    openai_organization_id: str = Field(validation_alias="OPENAI_ORGANIZATION_ID")
    openai_project_id: str = Field(validation_alias="OPENAI_PROJECT_ID")
    ai_model: ChatModel = Field("gpt-5.2", validation_alias="AI_MODEL")

    anthropic_api_key: Optional[SecretStr] = Field(None, validation_alias="ANTHROPIC_API_KEY")
    claude_model: str = Field("claude-opus-4-6", validation_alias="CLAUDE_MODEL")


settings = Settings()

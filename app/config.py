from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    vk_group_token: str = Field(alias="VK_GROUP_TOKEN")
    vk_group_id: int = Field(alias="VK_GROUP_ID")
    default_style: str = Field(default="classic", alias="DEFAULT_STYLE")
    max_forward_count: int = Field(default=5, alias="MAX_FORWARD_COUNT")
    superadmin_id: int = Field(alias="SUPERADMIN_ID")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

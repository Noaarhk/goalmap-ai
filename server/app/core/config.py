from typing import List, Union

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "GoalMap AI Server"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Gemini
    # Support both VITE_GEMINI_API_KEY (frontend legacy) and GOOGLE_API_KEY (standard)
    VITE_GEMINI_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None

    @property
    def GEMINI_API_KEY(self) -> str:
        key = self.GOOGLE_API_KEY or self.VITE_GEMINI_API_KEY
        if not key:
            raise ValueError("GEMINI_API_KEY is not set")
        return key

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra env vars (like typical frontend vars)
    )


settings = Settings()

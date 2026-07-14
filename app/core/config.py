from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수(.env)에서 로드되는 애플리케이션 설정."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "경비처리 API"
    environment: str = "dev"  # dev | prod

    database_url: str = "sqlite:///./dev.db"

    jwt_secret: str = "change-me-please"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    upload_dir: str = "storage/uploads"
    export_dir: str = "storage/exports"

    # 프론트엔드 CORS 허용 오리진 (콤마로 구분)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Naver CLOVA OCR (Receipt) — 두 값이 모두 있으면 실연동, 없으면 스텁
    clova_ocr_invoke_url: str = ""
    clova_ocr_secret: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def clova_ocr_enabled(self) -> bool:
        return bool(self.clova_ocr_invoke_url and self.clova_ocr_secret)

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def is_dev(self) -> bool:
        return self.environment == "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

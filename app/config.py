"""
Application configuration.
Loads settings from environment variables / .env file.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self) -> None:
        self.APP_ENV: str = os.getenv("APP_ENV", "development")
        self.DEBUG: bool = self.APP_ENV == "development"
        self.DATABASE_URL: str = os.getenv(
            "DATABASE_URL", "sqlite:///dividend_genie.db"
        )
        self.TELEGRAM_BOT_TOKEN: str = os.getenv(
            "TELEGRAM_BOT_TOKEN", os.getenv("BOT_TOKEN", "")
        )
        self.ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.SESSION_SECRET: str = os.getenv("SESSION_SECRET", "")

    def validate(self) -> None:
        errors: list[str] = []
        if not self.SESSION_SECRET:
            errors.append("SESSION_SECRET must be set in the environment.")
        elif self.SESSION_SECRET in {"change-me", "changeme", "secret", "password"}:
            errors.append(
                "SESSION_SECRET is set to a known insecure default value. "
                "Please generate a strong random secret."
            )
        if self.APP_ENV == "production":
            if not self.TELEGRAM_BOT_TOKEN:
                errors.append("TELEGRAM_BOT_TOKEN must be set in production.")
            if not self.ALPHA_VANTAGE_API_KEY:
                errors.append("ALPHA_VANTAGE_API_KEY must be set in production.")
        if errors:
            detail = "; ".join(errors)
            raise ValueError(
                f"Invalid configuration ({len(errors)} error(s)): {detail}"
            )


config = Config()

# Convenience alias used by bot modules
BOT_TOKEN = config.TELEGRAM_BOT_TOKEN

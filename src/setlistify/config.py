"""Configuration module for Setlistify.

Handles loading environment variables and application settings.
"""

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import os


# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration settings."""

    # Spotify OAuth
    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    SPOTIFY_REDIRECT_URI: str = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
    SPOTIFY_PLAYLIST_ID: str = os.getenv("SPOTIFY_PLAYLIST_ID", "")

    # Setlist.fm API
    SETLISTFM_API_KEY: str = os.getenv("SETLISTFM_API_KEY", "")

    # Application
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    CACHE_DB: str = os.getenv("CACHE_DB", ".cache/setlistify.db")

    # Derived paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    CACHE_DIR: Path = PROJECT_ROOT / ".cache"
    DATA_DIR: Path = PROJECT_ROOT / "data"

    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """Validate required configuration.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors: list[str] = []

        if not cls.SPOTIFY_CLIENT_ID:
            errors.append("SPOTIFY_CLIENT_ID not configured")
        if not cls.SPOTIFY_CLIENT_SECRET:
            errors.append("SPOTIFY_CLIENT_SECRET not configured")
        if not cls.SPOTIFY_PLAYLIST_ID:
            errors.append("SPOTIFY_PLAYLIST_ID not configured")
        if not cls.SETLISTFM_API_KEY:
            errors.append("SETLISTFM_API_KEY not configured")

        return len(errors) == 0, errors

    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)

"""Setlistify - Automated Spotify playlist management with setlist.fm concert setlists."""

__version__ = "0.1.0"

from .config import Config
from .logging_config import setup_logging, get_logger
from .models import Song, Setlist, CacheEntry, ArtistHistory, SyncResult, PlaylistStats

__all__ = [
    "Config",
    "setup_logging",
    "get_logger",
    "Song",
    "Setlist",
    "CacheEntry",
    "ArtistHistory",
    "SyncResult",
    "PlaylistStats",
]


"""Utility functions for Setlistify.

Common helper functions used across modules.
"""

from typing import Optional
import re


def normalize_song_name(name: str) -> str:
    """Normalize song name for comparison.

    Removes special characters, live indicators, etc.

    Args:
        name: Original song name

    Returns:
        Normalized song name
    """
    # Remove common live/demo indicators
    name = re.sub(r'\s*\(live[^)]*\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\[live[^\]]*\]', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(acoustic[^)]*\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\[acoustic[^\]]*\]', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(demo[^)]*\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(.*remaster.*\)', '', name, flags=re.IGNORECASE)

    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name).strip()

    return name


def normalize_artist_name(name: str) -> str:
    """Normalize artist name for comparison.

    Args:
        name: Original artist name

    Returns:
        Normalized artist name
    """
    # Remove common suffixes
    name = re.sub(r'\s*\(.*\)$', '', name)
    name = re.sub(r'\s+$', '', name)
    return name.strip()


def is_live_album(album_name: str) -> bool:
    """Check if album name indicates a live recording.

    Args:
        album_name: Album name to check

    Returns:
        True if album appears to be live
    """
    live_indicators = [
        'live',
        'at the',
        'recorded at',
        'live in',
        'live at',
    ]

    album_lower = album_name.lower()
    return any(indicator in album_lower for indicator in live_indicators)


def is_tribute_or_cover(album_name: str) -> bool:
    """Check if album is a tribute or cover compilation.

    Args:
        album_name: Album name to check

    Returns:
        True if album appears to be tribute/cover
    """
    indicators = ['tribute', 'covers', 'covered by']
    album_lower = album_name.lower()
    return any(indicator in album_lower for indicator in indicators)


def parse_uri_id(uri: str) -> Optional[str]:
    """Extract ID from Spotify URI.

    Args:
        uri: Spotify URI (e.g., 'spotify:track:123')

    Returns:
        Extracted ID or None
    """
    if ':' not in uri:
        return None
    parts = uri.split(':')
    return parts[-1] if parts else None

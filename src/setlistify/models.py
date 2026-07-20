"""Data models for Setlistify application.

Defines core domain objects as dataclasses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Song:
    """Represents a song from a setlist."""

    name: str
    artist: str
    setlist_id: Optional[str] = None  # ID from setlist.fm
    spotify_uri: Optional[str] = None  # Spotify URI when found
    album: Optional[str] = None
    popularity: int = 0

    def __hash__(self) -> int:
        """Make Song hashable for deduplication."""
        return hash((self.name.lower(), self.artist.lower()))

    def __eq__(self, other: object) -> bool:
        """Compare songs by name and artist."""
        if not isinstance(other, Song):
            return NotImplemented
        return (
            self.name.lower() == other.name.lower()
            and self.artist.lower() == other.artist.lower()
        )


@dataclass
class Setlist:
    """Represents a concert setlist."""

    artist_name: str
    event_date: str
    venue_name: str
    venue_city: str
    setlist_id: str
    setlist_url: str
    songs: list[Song] = field(default_factory=list)

    @property
    def song_count(self) -> int:
        """Get number of songs in setlist."""
        return len(self.songs)


@dataclass
class CacheEntry:
    """Represents a cached song search result."""

    artist: str
    song_name: str
    spotify_uri: str
    album: str
    popularity: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ArtistHistory:
    """Tracks artist information for update/remove operations."""

    artist_name: str
    added_at: datetime = field(default_factory=datetime.now)
    last_updated: Optional[datetime] = None
    song_count: int = 0
    setlist_id: Optional[str] = None


@dataclass
class SyncResult:
    """Result of syncing songs to Spotify."""

    artist: str
    total_songs: int
    added: int = 0
    skipped: int = 0  # Already in playlist
    not_found: int = 0  # Not found on Spotify
    errors: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_songs == 0:
            return 0.0
        return (self.added / self.total_songs) * 100


@dataclass
class PlaylistStats:
    """Statistics about the playlist."""

    total_songs: int
    unique_artists: int
    total_artists_tracked: int
    last_update: Optional[datetime]
    artists: list[str] = field(default_factory=list)

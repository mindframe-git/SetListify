"""SQLite cache for storing search results and artist information.

Avoids repeated API calls for known songs.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .config import Config
from .models import Song, CacheEntry, ArtistHistory


logger = logging.getLogger(__name__)


class Cache:
    """SQLite-based cache for Spotify search results and artist history."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize cache.

        Args:
            db_path: Path to SQLite database (uses Config.CACHE_DB if None)
        """
        self.db_path = db_path or Path(Config.CACHE_DB)
        self.conn: Optional[sqlite3.Connection] = None
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database tables."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()

            # Song cache table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS song_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artist TEXT NOT NULL,
                    song_name TEXT NOT NULL,
                    spotify_uri TEXT NOT NULL,
                    album TEXT,
                    popularity INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(artist, song_name)
                )
                """
            )

            # Artist history table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS artist_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artist_name TEXT UNIQUE NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP,
                    song_count INTEGER DEFAULT 0,
                    setlist_id TEXT
                )
                """
            )

            # Create indices for faster queries
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_artist_song ON song_cache(artist, song_name)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_artist_history ON artist_history(artist_name)"
            )

            self.conn.commit()
            logger.info(f"✓ Cache initialized at {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def get_song(self, artist: str, song_name: str) -> Optional[Song]:
        """Get a cached song.

        Args:
            artist: Artist name
            song_name: Song name

        Returns:
            Song object if found in cache, None otherwise
        """
        if not self.conn:
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM song_cache WHERE artist = ? AND song_name = ?",
                (artist, song_name),
            )
            row = cursor.fetchone()

            if row:
                return Song(
                    name=row["song_name"],
                    artist=row["artist"],
                    spotify_uri=row["spotify_uri"],
                    album=row["album"],
                    popularity=row["popularity"],
                )
            return None

        except sqlite3.Error as e:
            logger.error(f"Cache query error: {e}")
            return None

    def cache_song(self, song: Song) -> bool:
        """Cache a song.

        Args:
            song: Song object to cache

        Returns:
            True if successful, False otherwise
        """
        if not self.conn or not song.spotify_uri:
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO song_cache
                (artist, song_name, spotify_uri, album, popularity, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (song.artist, song.name, song.spotify_uri, song.album, song.popularity),
            )
            self.conn.commit()
            return True

        except sqlite3.Error as e:
            logger.error(f"Cache insert error: {e}")
            return False

    def cache_songs_batch(self, songs: list[Song]) -> int:
        """Cache multiple songs in a batch.

        Args:
            songs: List of Song objects to cache

        Returns:
            Number of successfully cached songs
        """
        if not self.conn:
            return 0

        cached = 0
        try:
            cursor = self.conn.cursor()

            for song in songs:
                if not song.spotify_uri:
                    continue

                try:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO song_cache
                        (artist, song_name, spotify_uri, album, popularity, updated_at)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (song.artist, song.name, song.spotify_uri, song.album, song.popularity),
                    )
                    cached += 1
                except sqlite3.Error:
                    continue

            self.conn.commit()
            return cached

        except sqlite3.Error as e:
            logger.error(f"Batch cache error: {e}")
            return cached

    def add_artist(
        self,
        artist_name: str,
        song_count: int = 0,
        setlist_id: Optional[str] = None,
    ) -> bool:
        """Add an artist to history.

        Args:
            artist_name: Name of the artist
            song_count: Number of songs added
            setlist_id: ID of the setlist used

        Returns:
            True if successful
        """
        if not self.conn:
            return False

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO artist_history
                (artist_name, last_updated, song_count, setlist_id)
                VALUES (?, CURRENT_TIMESTAMP, ?, ?)
                """,
                (artist_name, song_count, setlist_id),
            )
            self.conn.commit()
            return True

        except sqlite3.Error as e:
            logger.error(f"Artist history insert error: {e}")
            return False

    def get_artist_history(self, artist_name: str) -> Optional[ArtistHistory]:
        """Get artist history.

        Args:
            artist_name: Name of the artist

        Returns:
            ArtistHistory object if found, None otherwise
        """
        if not self.conn:
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM artist_history WHERE artist_name = ?",
                (artist_name,),
            )
            row = cursor.fetchone()

            if row:
                return ArtistHistory(
                    artist_name=row["artist_name"],
                    added_at=datetime.fromisoformat(row["added_at"]),
                    last_updated=datetime.fromisoformat(row["last_updated"]) if row["last_updated"] else None,
                    song_count=row["song_count"],
                    setlist_id=row["setlist_id"],
                )
            return None

        except sqlite3.Error as e:
            logger.error(f"Artist history query error: {e}")
            return None

    def get_all_artists(self) -> list[str]:
        """Get all tracked artists.

        Returns:
            List of artist names
        """
        if not self.conn:
            return []

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT artist_name FROM artist_history ORDER BY added_at DESC")
            rows = cursor.fetchall()
            return [row["artist_name"] for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Query error: {e}")
            return []

    def remove_artist(self, artist_name: str) -> bool:
        """Remove an artist and their cached songs.

        Args:
            artist_name: Name of the artist to remove

        Returns:
            True if successful
        """
        if not self.conn:
            return False

        try:
            cursor = self.conn.cursor()

            # Remove from history
            cursor.execute(
                "DELETE FROM artist_history WHERE artist_name = ?",
                (artist_name,),
            )

            # Remove cached songs from this artist
            cursor.execute(
                "DELETE FROM song_cache WHERE artist = ?",
                (artist_name,),
            )

            self.conn.commit()
            return True

        except sqlite3.Error as e:
            logger.error(f"Delete error: {e}")
            return False

    def clear_old_cache(self, days: int = 30) -> int:
        """Clear cache entries older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of entries deleted
        """
        if not self.conn:
            return 0

        try:
            cursor = self.conn.cursor()
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute(
                "DELETE FROM song_cache WHERE updated_at < ?",
                (cutoff_date,),
            )

            deleted = cursor.rowcount
            self.conn.commit()

            logger.info(f"Cleared {deleted} old cache entries (older than {days} days)")
            return deleted

        except sqlite3.Error as e:
            logger.error(f"Cache cleanup error: {e}")
            return 0

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.debug("Cache connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

"""Tests for the cache module."""

import pytest
from pathlib import Path
import tempfile

from src.setlistify.models import Song, ArtistHistory
from src.setlistify.cache import Cache


@pytest.fixture
def temp_cache():
    """Create temporary cache for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_cache.db"
        cache = Cache(db_path=db_path)
        yield cache
        cache.close()


class TestCaching:
    """Test cache functionality."""

    def test_cache_song(self, temp_cache):
        """Test caching a song."""
        song = Song(
            name="Ride the Lightning",
            artist="Metallica",
            spotify_uri="spotify:track:123",
            album="Ride the Lightning",
            popularity=85,
        )

        result = temp_cache.cache_song(song)
        assert result is True

        # Retrieve it
        cached = temp_cache.get_song("Metallica", "Ride the Lightning")
        assert cached is not None
        assert cached.spotify_uri == "spotify:track:123"
        assert cached.popularity == 85

    def test_cache_multiple_songs(self, temp_cache):
        """Test batch caching."""
        songs = [
            Song(name=f"Song {i}", artist="Artist", spotify_uri=f"spotify:track:{i}")
            for i in range(5)
        ]

        cached_count = temp_cache.cache_songs_batch(songs)
        assert cached_count == 5

    def test_artist_history(self, temp_cache):
        """Test artist history tracking."""
        result = temp_cache.add_artist("Metallica", song_count=10, setlist_id="abc123")
        assert result is True

        history = temp_cache.get_artist_history("Metallica")
        assert history is not None
        assert history.artist_name == "Metallica"
        assert history.song_count == 10
        assert history.setlist_id == "abc123"

    def test_get_all_artists(self, temp_cache):
        """Test retrieving all artists."""
        artists = ["Metallica", "Iron Maiden", "Helloween"]
        for artist in artists:
            temp_cache.add_artist(artist)

        all_artists = temp_cache.get_all_artists()
        assert len(all_artists) == 3
        assert "Metallica" in all_artists

    def test_remove_artist(self, temp_cache):
        """Test removing an artist."""
        temp_cache.add_artist("Metallica", song_count=5)
        song = Song(
            name="Song",
            artist="Metallica",
            spotify_uri="spotify:track:123",
        )
        temp_cache.cache_song(song)

        # Remove artist
        result = temp_cache.remove_artist("Metallica")
        assert result is True

        # Verify removed
        history = temp_cache.get_artist_history("Metallica")
        assert history is None

        cached = temp_cache.get_song("Metallica", "Song")
        assert cached is None

    def test_cache_unique_constraint(self, temp_cache):
        """Test that duplicate artist/song combinations are updated."""
        song1 = Song(
            name="Ride",
            artist="Metallica",
            spotify_uri="spotify:track:123",
            popularity=80,
        )
        song2 = Song(
            name="Ride",
            artist="Metallica",
            spotify_uri="spotify:track:456",  # Different URI
            popularity=90,
        )

        temp_cache.cache_song(song1)
        temp_cache.cache_song(song2)

        # Should return the updated one
        cached = temp_cache.get_song("Metallica", "Ride")
        assert cached.spotify_uri == "spotify:track:456"
        assert cached.popularity == 90

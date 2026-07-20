"""Integration tests for Setlistify CLI and core flows."""

import pytest
from pathlib import Path
import tempfile

from src.setlistify.config import Config
from src.setlistify.models import Song, Setlist
from src.setlistify.cache import Cache


class TestIntegration:
    """Integration tests for core workflows."""

    def test_config_directories_created(self):
        """Test that configuration creates necessary directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override config paths
            original_logs = Config.LOGS_DIR
            original_cache_dir = Config.CACHE_DIR
            original_data = Config.DATA_DIR

            try:
                Config.LOGS_DIR = Path(tmpdir) / "logs"
                Config.CACHE_DIR = Path(tmpdir) / ".cache"
                Config.DATA_DIR = Path(tmpdir) / "data"

                Config.ensure_directories()

                assert Config.LOGS_DIR.exists()
                assert Config.CACHE_DIR.exists()
                assert Config.DATA_DIR.exists()

            finally:
                Config.LOGS_DIR = original_logs
                Config.CACHE_DIR = original_cache_dir
                Config.DATA_DIR = original_data

    def test_full_sync_workflow(self):
        """Test complete sync workflow: setlist -> cache -> search."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create cache
            cache_path = Path(tmpdir) / "test.db"
            cache = Cache(db_path=cache_path)

            # Create a setlist
            songs = [
                Song(name="Song 1", artist="Test Artist", spotify_uri="spotify:track:1"),
                Song(name="Song 2", artist="Test Artist", spotify_uri="spotify:track:2"),
            ]
            setlist = Setlist(
                artist_name="Test Artist",
                event_date="2024-11-09",
                venue_name="Test Venue",
                venue_city="Test City",
                setlist_id="test123",
                setlist_url="http://test",
                songs=songs,
            )

            # Cache the songs
            cache.cache_songs_batch(setlist.songs)

            # Verify they're cached
            for song in setlist.songs:
                cached = cache.get_song(song.artist, song.name)
                assert cached is not None
                assert cached.spotify_uri == song.spotify_uri

            # Add artist to history
            cache.add_artist(setlist.artist_name, len(setlist.songs), setlist.setlist_id)

            # Verify artist is tracked
            history = cache.get_artist_history(setlist.artist_name)
            assert history is not None
            assert history.song_count == 2

            cache.close()

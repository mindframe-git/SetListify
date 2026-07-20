"""Tests for models."""

import pytest
from datetime import datetime

from src.setlistify.models import (
    Song,
    Setlist,
    SyncResult,
    PlaylistStats,
    ArtistHistory,
)


class TestSongModel:
    """Test Song dataclass."""

    def test_song_creation(self):
        """Test creating a song."""
        song = Song(
            name="Enter Sandman",
            artist="Metallica",
            spotify_uri="spotify:track:123",
            album="The Black Album",
            popularity=90,
        )

        assert song.name == "Enter Sandman"
        assert song.artist == "Metallica"
        assert song.spotify_uri == "spotify:track:123"

    def test_song_equality(self):
        """Test song equality (name and artist based)."""
        song1 = Song(name="One", artist="Metallica")
        song2 = Song(name="One", artist="Metallica", spotify_uri="different")

        # Should be equal based on name and artist
        assert song1 == song2

    def test_song_inequality(self):
        """Test song inequality."""
        song1 = Song(name="One", artist="Metallica")
        song2 = Song(name="One", artist="Iron Maiden")

        assert song1 != song2

    def test_song_hashable(self):
        """Test that songs are hashable."""
        song1 = Song(name="One", artist="Metallica")
        song2 = Song(name="One", artist="Metallica")

        # Should be able to use in set
        song_set = {song1, song2}
        assert len(song_set) == 1  # Duplicates removed


class TestSetlist:
    """Test Setlist model."""

    def test_setlist_creation(self):
        """Test creating a setlist."""
        songs = [
            Song(name="Song 1", artist="Artist"),
            Song(name="Song 2", artist="Artist"),
        ]

        setlist = Setlist(
            artist_name="Metallica",
            event_date="2024-11-09",
            venue_name="The Fillmore",
            venue_city="San Francisco",
            setlist_id="abc123",
            setlist_url="https://setlist.fm/...",
            songs=songs,
        )

        assert setlist.artist_name == "Metallica"
        assert setlist.song_count == 2

    def test_setlist_empty(self):
        """Test setlist with no songs."""
        setlist = Setlist(
            artist_name="Artist",
            event_date="2024-11-09",
            venue_name="Venue",
            venue_city="City",
            setlist_id="id",
            setlist_url="url",
        )

        assert setlist.song_count == 0


class TestSyncResult:
    """Test SyncResult model."""

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = SyncResult(
            artist="Metallica",
            total_songs=10,
            added=8,
            skipped=2,
            not_found=0,
        )

        assert result.success_rate == 80.0

    def test_success_rate_zero(self):
        """Test success rate when no songs total."""
        result = SyncResult(
            artist="Artist",
            total_songs=0,
            added=0,
        )

        assert result.success_rate == 0.0


class TestArtistHistory:
    """Test ArtistHistory model."""

    def test_artist_history_creation(self):
        """Test creating artist history."""
        history = ArtistHistory(
            artist_name="Metallica",
            song_count=15,
            setlist_id="id123",
        )

        assert history.artist_name == "Metallica"
        assert history.song_count == 15
        assert isinstance(history.added_at, datetime)


class TestPlaylistStats:
    """Test PlaylistStats model."""

    def test_stats_creation(self):
        """Test creating playlist stats."""
        stats = PlaylistStats(
            total_songs=100,
            unique_artists=5,
            total_artists_tracked=5,
            last_update=datetime.now(),
            artists=["Metallica", "Iron Maiden"],
        )

        assert stats.total_songs == 100
        assert stats.unique_artists == 5

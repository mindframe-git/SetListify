"""Tests for utility functions."""

import pytest
from src.setlistify.utils import (
    normalize_song_name,
    normalize_artist_name,
    is_live_album,
    is_tribute_or_cover,
    parse_uri_id,
)


class TestNameNormalization:
    """Test name normalization functions."""

    def test_normalize_song_live_removal(self):
        """Test removing live indicators."""
        assert normalize_song_name("Song (Live at Venue)") == "Song"
        assert normalize_song_name("Song [Live]") == "Song"
        assert normalize_song_name("Song (Acoustic)") == "Song"

    def test_normalize_song_remaster(self):
        """Test removing remaster indicators."""
        assert normalize_song_name("Song (2009 Remaster)") == "Song"
        assert normalize_song_name("Song (Remastered)") == "Song"

    def test_normalize_artist_parentheses(self):
        """Test removing parenthetical info from artist."""
        assert normalize_artist_name("Band (Original)") == "Band"
        assert normalize_artist_name("Artist (Solo)") == "Artist"

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        assert normalize_song_name("Song   With  Extra   Spaces") == "Song With Extra Spaces"


class TestAlbumDetection:
    """Test album type detection."""

    def test_live_album_detection(self):
        """Test detecting live albums."""
        assert is_live_album("Album Live in Concert")
        assert is_live_album("Live at the Fillmore")
        assert is_live_album("Recorded at Venue")
        assert not is_live_album("The Album")

    def test_tribute_detection(self):
        """Test detecting tribute albums."""
        assert is_tribute_or_cover("Tribute to Artist")
        assert is_tribute_or_cover("Greatest Covers")
        assert is_tribute_or_cover("Covered by Others")
        assert not is_tribute_or_cover("Greatest Hits")


class TestURIParsing:
    """Test Spotify URI parsing."""

    def test_parse_track_uri(self):
        """Test parsing track URI."""
        uri = "spotify:track:11dFghVXANMlKmJXsNCQvb"
        track_id = parse_uri_id(uri)
        assert track_id == "11dFghVXANMlKmJXsNCQvb"

    def test_parse_artist_uri(self):
        """Test parsing artist URI."""
        uri = "spotify:artist:0oSGJ1PdQeyaqgtVzN9IZ9"
        artist_id = parse_uri_id(uri)
        assert artist_id == "0oSGJ1PdQeyaqgtVzN9IZ9"

    def test_parse_invalid_uri(self):
        """Test parsing invalid URI."""
        result = parse_uri_id("not-a-uri")
        assert result is None

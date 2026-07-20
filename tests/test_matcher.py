"""Tests for the matcher module."""

import pytest
from src.setlistify.models import Song
from src.setlistify.matcher import SongMatcher


class TestFuzzyMatching:
    """Test fuzzy matching functionality."""

    def test_exact_match(self):
        """Test exact song match."""
        song1 = Song(name="Ride the Lightning", artist="Metallica")
        song2 = Song(name="Ride the Lightning", artist="Metallica")

        score = SongMatcher.fuzzy_match_song(song1, song2)
        assert score > 90  # Should be very high for exact match

    def test_minor_differences(self):
        """Test matching with minor differences."""
        song1 = Song(name="Dr Stein", artist="Helloween")
        song2 = Song(name="Dr. Stein", artist="Helloween")

        score = SongMatcher.fuzzy_match_song(song1, song2)
        assert score > SongMatcher.MIN_SIMILARITY

    def test_live_version_excluded(self):
        """Test that live versions are properly handled."""
        song1 = Song(name="One", artist="Metallica")
        song2 = Song(name="One (Live)", artist="Metallica")

        # After normalization, should match
        score = SongMatcher.fuzzy_match_song(song1, song2)
        assert score > SongMatcher.MIN_SIMILARITY

    def test_no_match_below_threshold(self):
        """Test that dissimilar songs return 0."""
        song1 = Song(name="Bohemian Rhapsody", artist="Queen")
        song2 = Song(name="Stairway to Heaven", artist="Led Zeppelin")

        score = SongMatcher.fuzzy_match_song(song1, song2)
        assert score < SongMatcher.MIN_SIMILARITY or score == 0

    def test_best_match_extraction(self):
        """Test extracting best match from candidates."""
        query = Song(name="One", artist="Metallica")
        candidates = [
            Song(name="Enter Sandman", artist="Metallica"),
            Song(name="One", artist="Metallica"),
            Song(name="Sad But True", artist="Metallica"),
        ]

        result = SongMatcher.extract_best_match(query, candidates)
        assert result is not None
        best_song, score = result
        # Should match the exact name "One"
        assert best_song.name == "One"

    def test_artist_mismatch_handles_gracefully(self):
        """Test that artist mismatch is handled."""
        song1 = Song(name="One", artist="Metallica")
        song2 = Song(name="One", artist="U2")

        score = SongMatcher.fuzzy_match_song(song1, song2)
        # Should be low due to artist mismatch
        assert score < 80  # With current weighting, artist difference matters


class TestEdgeCases:
    """Test edge cases in matching."""

    def test_empty_candidates(self):
        """Test matching with empty candidate list."""
        query = Song(name="Phantom of the Opera", artist="The Phantom")
        result = SongMatcher.extract_best_match(query, [])
        assert result is None

    def test_unicode_handling(self):
        """Test handling of unicode characters in names."""
        song1 = Song(name="Müller's Song", artist="Künstler")
        song2 = Song(name="Müller's Song", artist="Künstler")

        score = SongMatcher.fuzzy_match_song(song1, song2)
        assert score > 90

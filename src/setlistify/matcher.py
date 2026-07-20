"""Song matching engine using RapidFuzz for fuzzy string matching.

Handles matching setlist songs to Spotify tracks with intelligent scoring.
"""

import logging
from typing import Optional
from rapidfuzz import fuzz, process

from .models import Song
from .utils import normalize_song_name, normalize_artist_name


logger = logging.getLogger(__name__)


class SongMatcher:
    """Matches setlist songs to Spotify tracks."""

    # Fuzzy match threshold (0-100)
    MIN_SIMILARITY = 80

    @staticmethod
    def fuzzy_match_song(
        setlist_song: Song,
        spotify_song: Song,
        threshold: int = MIN_SIMILARITY,
    ) -> float:
        """Calculate fuzzy match score between setlist and Spotify song.

        Args:
            setlist_song: Song from setlist
            spotify_song: Song from Spotify search result
            threshold: Minimum similarity score (0-100)

        Returns:
            Match score (0-100), 0 if below threshold
        """
        # Normalize names for comparison
        setlist_name = normalize_song_name(setlist_song.name)
        spotify_name = normalize_song_name(spotify_song.name)

        setlist_artist = normalize_artist_name(setlist_song.artist)
        spotify_artist = normalize_artist_name(spotify_song.artist)

        # Song name similarity
        name_ratio = fuzz.token_set_ratio(setlist_name, spotify_name)

        # Artist similarity
        artist_ratio = fuzz.token_set_ratio(setlist_artist, spotify_artist)

        # Combined score (weighted)
        # Name match is more important than artist (artist might be feat. variations)
        combined_score = (name_ratio * 0.7) + (artist_ratio * 0.3)

        if combined_score < threshold:
            logger.debug(
                f"Fuzzy match below threshold: "
                f"'{setlist_name}' vs '{spotify_name}' ({combined_score:.1f})"
            )
            return 0

        return combined_score

    @staticmethod
    def extract_best_match(
        query_song: Song,
        candidates: list[Song],
        threshold: int = MIN_SIMILARITY,
    ) -> Optional[tuple[Song, float]]:
        """Extract the best matching song from candidates using fuzzy matching.

        Args:
            query_song: Song to match (from setlist)
            candidates: List of candidate songs (from Spotify)
            threshold: Minimum similarity score

        Returns:
            Tuple of (best_match, score) or None if no good match found
        """
        if not candidates:
            return None

        best_match = None
        best_score = 0

        for candidate in candidates:
            score = SongMatcher.fuzzy_match_song(
                query_song,
                candidate,
                threshold,
            )

            if score > best_score:
                best_score = score
                best_match = candidate

        if best_match is None:
            logger.debug(f"No matching song found for: {query_song.name}")
            return None

        return best_match, best_score

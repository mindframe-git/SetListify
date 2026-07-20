"""Spotify client for interacting with Spotify Web API.

Handles OAuth authentication, token management, and API operations.
"""

import json
import webbrowser
from pathlib import Path
from typing import Optional, Any
import logging

import spotipy
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth

from .config import Config
from .models import Song
from .utils import parse_uri_id, is_live_album, is_tribute_or_cover


logger = logging.getLogger(__name__)


class SpotifyRateLimitError(RuntimeError):
    """Raised when Spotify rejects a request with a retry delay."""

    def __init__(self, retry_after: Optional[str] = None):
        self.retry_after = retry_after
        message = "Spotify rate limit reached."
        if retry_after:
            message += f" Retry after {retry_after} seconds."
        super().__init__(message)


class SpotifyClient:
    """Client for Spotify Web API operations."""

    CACHE_PATH = Config.CACHE_DIR / ".spotify_token"
    SCOPES = [
        "playlist-modify-public",
        "playlist-modify-private",
        "playlist-read-private",
    ]

    def __init__(self):
        """Initialize Spotify client with OAuth."""
        self.sp: Optional[spotipy.Spotify] = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Spotify using OAuth."""
        if not Config.SPOTIFY_CLIENT_ID or not Config.SPOTIFY_CLIENT_SECRET:
            raise ValueError(
                "Spotify credentials not configured. "
                "Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET"
            )

        Config.ensure_directories()

        auth_manager = SpotifyOAuth(
            client_id=Config.SPOTIFY_CLIENT_ID,
            client_secret=Config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=Config.SPOTIFY_REDIRECT_URI,
            scope=self.SCOPES,
            cache_path=str(self.CACHE_PATH),
            show_dialog=False,
        )

        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        logger.info("✓ Spotify authentication successful")

    @staticmethod
    def _raise_if_rate_limited(error: SpotifyException) -> None:
        """Translate a Spotify 429 response into an actionable error."""
        if error.http_status != 429:
            return

        headers = getattr(error, "headers", None) or {}
        retry_after = headers.get("Retry-After") or headers.get("retry-after")
        raise SpotifyRateLimitError(retry_after) from error

    def get_current_user(self) -> dict[str, Any]:
        """Get current user information.

        Returns:
            User data dictionary

        Raises:
            RuntimeError: If not authenticated
        """
        if not self.sp:
            raise RuntimeError("Not authenticated with Spotify")

        user = self.sp.current_user()
        return user

    def search_track(
        self,
        track_name: str,
        artist_name: str,
        strict_artist: bool = False,
    ) -> Optional[Song]:
        """Search for a track on Spotify.

        Args:
            track_name: Name of the track
            artist_name: Name of the artist
            strict_artist: If True, require exact artist match

        Returns:
            Song object with Spotify URI if found, None otherwise
        """
        if not self.sp:
            raise RuntimeError("Not authenticated with Spotify")

        # Build search query
        query = f"track:{track_name} artist:{artist_name}"

        try:
            results = self.sp.search(q=query, type="track", limit=9)
        except SpotifyException as e:
            self._raise_if_rate_limited(e)
            logger.error(f"Spotify search error for '{track_name}' by '{artist_name}': {e}")
            return None
        except Exception as e:
            logger.error(f"Spotify search error for '{track_name}' by '{artist_name}': {e}")
            return None

        if not results["tracks"]["items"]:
            logger.debug(f"No tracks found for: {track_name} by {artist_name}")
            return None

        # Score and filter tracks
        best_track = self._score_and_filter_results(
            results["tracks"]["items"],
            track_name,
            artist_name,
            strict_artist,
        )

        if best_track:
            song = Song(
                name=best_track["name"],
                artist=", ".join([a["name"] for a in best_track["artists"]]),
                spotify_uri=best_track["uri"],
                album=best_track["album"]["name"],
                popularity=best_track.get("popularity", 0),
            )
            return song

        return None

    def _score_and_filter_results(
        self,
        tracks: list[dict[str, Any]],
        track_name: str,
        artist_name: str,
        strict_artist: bool,
    ) -> Optional[dict[str, Any]]:
        """Score and filter search results based on criteria.

        Prioritizes:
        1. Exact artist match
        2. Studio album (not live)
        3. Not tribute/cover
        4. Name match
        5. Popularity

        Args:
            tracks: List of track results from Spotify
            track_name: Original track name
            artist_name: Original artist name
            strict_artist: If True, only return exact artist matches

        Returns:
            Best matching track or None
        """
        filtered_tracks = []

        for track in tracks:
            # Check if artist matches
            track_artists = [a["name"].lower() for a in track["artists"]]
            artist_match = artist_name.lower() in track_artists

            if strict_artist and not artist_match:
                continue

            # Skip live albums
            album_name = track["album"]["name"]
            if is_live_album(album_name):
                logger.debug(f"Skipping live album: {album_name}")
                continue

            # Skip tribute/cover albums
            if is_tribute_or_cover(album_name):
                logger.debug(f"Skipping tribute/cover album: {album_name}")
                continue

            # Score this track
            score = self._score_track(
                track,
                track_name,
                artist_name,
                artist_match,
            )

            filtered_tracks.append((score, track))

        if not filtered_tracks:
            return None

        # Return highest scored track
        filtered_tracks.sort(key=lambda x: x[0], reverse=True)
        return filtered_tracks[0][1]

    @staticmethod
    def _score_track(
        track: dict[str, Any],
        track_name: str,
        artist_name: str,
        artist_match: bool,
    ) -> float:
        """Score a track for relevance.

        Args:
            track: Track data from Spotify
            track_name: Original track name
            artist_name: Original artist name
            artist_match: Whether artist matches

        Returns:
            Score (higher is better)
        """
        score = 0.0

        # Artist match (high priority)
        if artist_match:
            score += 1000

        # Name match
        if track["name"].lower() == track_name.lower():
            score += 500
        elif track_name.lower() in track["name"].lower():
            score += 250

        # Popularity (lower value given)
        score += track.get("popularity", 0) * 0.1

        return score

    def get_playlist(self, playlist_id: str) -> dict[str, Any]:
        """Get playlist information.

        Args:
            playlist_id: Spotify playlist ID

        Returns:
            Playlist data

        Raises:
            RuntimeError: If not authenticated
        """
        if not self.sp:
            raise RuntimeError("Not authenticated with Spotify")

        try:
            playlist = self.sp.playlist(playlist_id)
            return playlist
        except Exception as e:
            logger.error(f"Error fetching playlist {playlist_id}: {e}")
            raise

    def get_playlist_tracks(self, playlist_id: str) -> list[dict[str, Any]]:
        """Get all tracks in a playlist.

        Args:
            playlist_id: Spotify playlist ID

        Returns:
            List of track objects

        Raises:
            RuntimeError: If not authenticated
        """
        if not self.sp:
            raise RuntimeError("Not authenticated with Spotify")

        tracks = []
        try:
            results = self.sp.playlist_tracks(playlist_id)

            while results:
                tracks.extend(results["items"])
                if results["next"]:
                    results = self.sp.next(results)
                else:
                    break
        except SpotifyException as e:
            self._raise_if_rate_limited(e)
            raise

        return tracks

    def get_playlist_track_ids(self, playlist_id: str) -> set[str]:
        """Return all available track IDs in a playlist with one fetch."""
        track_ids = set()
        for item in self.get_playlist_tracks(playlist_id):
            track = item.get("track")
            if not track or not track.get("uri"):
                continue
            track_ids.add(parse_uri_id(track["uri"]))
        return track_ids

    def track_exists_in_playlist(
        self,
        playlist_id: str,
        song: Song,
    ) -> bool:
        """Check if a song already exists in playlist.

        Args:
            playlist_id: Spotify playlist ID
            song: Song to check

        Returns:
            True if song exists in playlist
        """
        if not song.spotify_uri:
            return False

        tracks = self.get_playlist_tracks(playlist_id)
        song_id = parse_uri_id(song.spotify_uri)

        for item in tracks:
            track = item.get("track")
            if not track or not track.get("uri"):
                logger.debug("Ignoring unavailable or removed playlist item")
                continue

            if parse_uri_id(track["uri"]) == song_id:
                return True

        return False

    def add_tracks_to_playlist(
        self,
        playlist_id: str,
        songs: list[Song],
        skip_duplicates: bool = True,
    ) -> tuple[int, int, list[Song]]:
        """Add tracks to a playlist.

        Args:
            playlist_id: Spotify playlist ID
            songs: List of songs to add
            skip_duplicates: If True, skip songs already in playlist

        Returns:
            Tuple of (added_count, skipped_count, not_found_songs)

        Raises:
            RuntimeError: If not authenticated
        """
        if not self.sp:
            raise RuntimeError("Not authenticated with Spotify")

        track_uris = []
        not_found = []
        skipped_count = 0
        existing_track_ids = (
            self.get_playlist_track_ids(playlist_id) if skip_duplicates else set()
        )

        for song in songs:
            if not song.spotify_uri:
                not_found.append(song)
                continue

            song_id = parse_uri_id(song.spotify_uri)
            if skip_duplicates and song_id in existing_track_ids:
                logger.debug(f"Track already in playlist: {song.name}")
                skipped_count += 1
                continue

            track_uris.append(song.spotify_uri)
            existing_track_ids.add(song_id)

        if not track_uris:
            logger.info("No new tracks to add")
            return 0, skipped_count, not_found

        # Add tracks in batches of 100 (Spotify API limit)
        added = 0
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i : i + 100]
            try:
                self.sp.playlist_add_items(playlist_id, batch)
                added += len(batch)
                logger.info(f"Added {len(batch)} tracks to playlist")
            except SpotifyException as e:
                self._raise_if_rate_limited(e)
                logger.error(f"Error adding tracks to playlist: {e}")
                raise
            except Exception as e:
                logger.error(f"Error adding tracks to playlist: {e}")
                raise

        return added, skipped_count, not_found

    def verify_credentials(self) -> bool:
        """Verify that credentials are configured and valid.

        Returns:
            True if credentials are valid
        """
        try:
            user = self.get_current_user()
            logger.info(f"✓ Connected as: {user.get('display_name', 'User')}")
            return True
        except Exception as e:
            logger.error(f"Failed to verify credentials: {e}")
            return False

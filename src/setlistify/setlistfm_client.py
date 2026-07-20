"""Setlist.fm API client for retrieving concert setlists.

Uses the official setlist.fm REST API to fetch concert information.
Implements rate limiting to respect API constraints (2.0 req/sec, 1440/day).
"""

import logging
import time
from math import ceil
from typing import Optional
import requests

from .config import Config
from .models import Song, Setlist


logger = logging.getLogger(__name__)


class SetlistFmClient:
    """Client for setlist.fm API.
    
    Rate limiting:
    - Max 2.0 requests per second (we use 0.6 for safety margin)
    - Max 1440 requests per day
    - Implements automatic throttling to stay well below limits
    """

    BASE_URL = "https://api.setlist.fm/rest/1.0"
    HEADERS_TEMPLATE = {
        "Accept": "application/json",
        "x-api-key": "",
    }

    # Rate limiting (setlist.fm allows 2.0/sec, we use 0.6 for safety)
    MIN_REQUEST_INTERVAL = 1.67  # ~0.6 requests per second (safe margin)
    _last_request_time = 0
    _request_count_today = 0
    _request_count_start_time = None

    # Song element types to ignore
    IGNORED_ELEMENTS = {
        "Intro",
        "Speech",
        "Solo",
        "Interlude",
        "Video",
        "Tape",
        "Break",
        "Encore Break",
    }

    def __init__(self):
        """Initialize Setlist.fm client with API key."""
        if not Config.SETLISTFM_API_KEY:
            raise ValueError(
                "Setlist.fm API key not configured. "
                "Please set SETLISTFM_API_KEY environment variable"
            )

        self.api_key = Config.SETLISTFM_API_KEY
        self.headers = self.HEADERS_TEMPLATE.copy()
        self.headers["x-api-key"] = self.api_key
        
        # Initialize rate limit tracking
        self._last_request_time = time.time()
        self._request_count_today = 0
        self._request_count_start_time = time.time()

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting to stay under setlist.fm limits.
        
        Sleeps if necessary to maintain max 0.6 req/sec (well below 2.0 limit).
        """
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self.MIN_REQUEST_INTERVAL:
            sleep_time = self.MIN_REQUEST_INTERVAL - time_since_last_request
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()

    def _track_request(self) -> None:
        """Track daily request count and warn if approaching limit.
        
        Warns when approaching 1440 requests/day limit.
        """
        # Reset daily counter if 24 hours have passed
        if time.time() - self._request_count_start_time > 86400:
            self._request_count_today = 0
            self._request_count_start_time = time.time()
        
        self._request_count_today += 1
        
        # Warn at different thresholds
        if self._request_count_today == 1200:
            logger.warning(
                f"setlist.fm: 1200/1440 daily requests used (83%). "
                f"Consider caching results."
            )
        elif self._request_count_today == 1350:
            logger.warning(
                f"setlist.fm: 1350/1440 daily requests used (94%). "
                f"Approaching daily limit!"
            )
        elif self._request_count_today >= 1440:
            logger.error(
                f"setlist.fm: Daily limit (1440 requests) reached! "
                f"Current: {self._request_count_today}"
            )

    def _make_request(
        self,
        endpoint: str,
        params: Optional[dict] = None,
    ) -> Optional[dict]:
        """Make a rate-limited request to setlist.fm API.
        
        Args:
            endpoint: Full API endpoint URL
            params: Query parameters
            
        Returns:
            JSON response or None if error
        """
        # Enforce rate limit before making request
        self._enforce_rate_limit()
        
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                params=params,
                timeout=10,
            )
            
            # Handle rate limit error
            if response.status_code == 429:
                logger.error(
                    "setlist.fm rate limit exceeded! "
                    "Waiting 60 seconds before retry..."
                )
                time.sleep(60)
                return self._make_request(endpoint, params)
            
            response.raise_for_status()
            self._track_request()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            return None
        except requests.RequestException as e:
            logger.error(f"Request error: {e}")
            return None

    def search_artist(self, artist_name: str) -> Optional[dict]:
        """Search for an artist by name.

        Args:
            artist_name: Name of the artist to search for

        Returns:
            Artist data with MBID if found, None otherwise
        """
        artists, _ = self.search_artists_page(artist_name)
        return artists[0] if artists else None

    def search_artists_page(
        self,
        artist_name: str,
        page: int = 1,
    ) -> tuple[list[dict], int]:
        """Search artists and return one paginated result page."""
        endpoint = f"{self.BASE_URL}/search/artists"
        data = self._make_request(endpoint, {"artistName": artist_name, "p": page})
        if not data:
            return [], 0

        artists = data.get("artist", [])
        if isinstance(artists, dict):
            artists = [artists]

        try:
            total = int(data.get("total", len(artists)))
            items_per_page = int(data.get("itemsPerPage", len(artists) or 1))
        except (TypeError, ValueError):
            total = len(artists)
            items_per_page = len(artists) or 1
        return artists, max(1, ceil(total / items_per_page))

    def get_artist_setlists(
        self,
        artist_mbid: str,
        page: int = 1,
        limit: int = 1,
    ) -> list[dict]:
        """Get recent setlists for an artist.

        Args:
            artist_mbid: MusicBrainz ID of the artist
            page: Page number (1-indexed)
            limit: Number of results per page

        Returns:
            List of setlist data
        """
        setlists, _ = self.get_artist_setlists_page(artist_mbid, page)
        return setlists[:limit]

    def get_artist_setlists_page(
        self,
        artist_mbid: str,
        page: int = 1,
    ) -> tuple[list[dict], int]:
        """Get one paginated page of an artist's setlists.

        Returns the setlists for the requested page and the total number of
        pages reported by setlist.fm. The API controls the page size.
        """
        endpoint = f"{self.BASE_URL}/artist/{artist_mbid}/setlists"
        data = self._make_request(endpoint, {"p": page})

        if not data:
            return [], 0

        setlists = data.get("setlist", [])
        if isinstance(setlists, dict):
            setlists = [setlists]

        try:
            total = int(data.get("total", len(setlists)))
            items_per_page = int(data.get("itemsPerPage", len(setlists) or 1))
        except (TypeError, ValueError):
            total = len(setlists)
            items_per_page = len(setlists) or 1

        return setlists, max(1, ceil(total / items_per_page))

    def get_setlist(self, setlist_id: str) -> Optional[Setlist]:
        """Get a specific setlist.

        Args:
            setlist_id: ID of the setlist

        Returns:
            Setlist object with songs, or None if error
        """
        endpoint = f"{self.BASE_URL}/setlist/{setlist_id}"

        data = self._make_request(endpoint)

        if not data:
            return None

        try:
            setlist = self._parse_setlist(data)
            return setlist
        except Exception as e:
            logger.error(f"Error parsing setlist data: {e}")
            return None

    def _parse_setlist(self, data: dict) -> Setlist:
        """Parse setlist data from API response.

        Args:
            data: Raw setlist data from API

        Returns:
            Setlist object

        Raises:
            KeyError: If required fields are missing
        """
        artist_name = data["artist"]["name"]
        event_date = data.get("eventDate", "Unknown")
        venue_info = data.get("venue", {})
        venue_name = venue_info.get("name", "Unknown")
        venue_city = venue_info.get("city", {}).get("name", "Unknown")
        setlist_id = data["id"]
        setlist_url = data["url"]

        # Parse songs
        songs = []
        sets = data.get("sets", {})

        if isinstance(sets, dict):
            set_list = sets.get("set", [])
        else:
            set_list = sets

        if not isinstance(set_list, list):
            set_list = [set_list]

        for set_data in set_list:
            songs.extend(self._parse_set(set_data, artist_name))

        return Setlist(
            artist_name=artist_name,
            event_date=event_date,
            venue_name=venue_name,
            venue_city=venue_city,
            setlist_id=setlist_id,
            setlist_url=setlist_url,
            songs=songs,
        )

    def _parse_set(self, set_data: dict, artist_name: str) -> list[Song]:
        """Parse songs from a set.

        Args:
            set_data: Set data from setlist
            artist_name: Name of the artist

        Returns:
            List of Song objects
        """
        songs = []
        songs_data = set_data.get("song", [])

        if not isinstance(songs_data, list):
            songs_data = [songs_data]

        for song_data in songs_data:
            # Skip non-song elements
            if isinstance(song_data, dict) and "name" in song_data:
                song_name = song_data["name"]

                # Check if this is a song or special element
                if any(ignored in song_name for ignored in self.IGNORED_ELEMENTS):
                    logger.debug(f"Skipping non-song element: {song_name}")
                    continue

                song = Song(
                    name=song_name,
                    artist=artist_name,
                    setlist_id=song_data.get("setlistfmId"),
                )
                songs.append(song)

        return songs

    def get_latest_setlist(self, artist_name: str) -> Optional[Setlist]:
        """Get the most recent setlist for an artist.

        This is the main entry point for fetching a current setlist.

        Args:
            artist_name: Name of the artist

        Returns:
            Setlist object with songs, or None if not found

        Steps:
            1. Search for artist to get MBID
            2. Get recent setlists
            3. Return the first (most recent) setlist
        """
        # Search for artist
        artist = self.search_artist(artist_name)
        if not artist:
            logger.error(f"Could not find artist: {artist_name}")
            return None

        mbid = artist.get("mbid")
        if not mbid:
            logger.error(f"No MBID for artist: {artist_name}")
            return None

        logger.info(f"Found artist: {artist.get('name')} (MBID: {mbid})")

        # Get recent setlists (requesting just 1)
        setlists = self.get_artist_setlists(mbid, page=1, limit=1)

        if not setlists:
            logger.warning(f"No setlists found for artist: {artist_name}")
            return None

        setlist_data = setlists[0]
        setlist_id = setlist_data.get("id")

        if not setlist_id:
            logger.error("Setlist ID not found in data")
            return None

        logger.info(f"Found latest setlist ID: {setlist_id}")

        # Get full setlist details
        return self.get_setlist(setlist_id)

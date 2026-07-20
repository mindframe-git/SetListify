from src.setlistify.models import Song
from src.setlistify.spotify_client import SpotifyClient, SpotifyRateLimitError


class FakeSpotify:
    def playlist_add_items(self, playlist_id, uris):
        self.playlist_id = playlist_id
        self.uris = uris


def test_add_tracks_reports_skipped_and_unresolved_songs():
    client = object.__new__(SpotifyClient)
    client.sp = FakeSpotify()
    existing = Song("Existing", "Artist", spotify_uri="spotify:track:existing")
    new = Song("New", "Artist", spotify_uri="spotify:track:new")
    unresolved = Song("Unresolved", "Artist")
    fetches = []

    def get_existing_track_ids(_):
        fetches.append(True)
        return {"existing"}

    client.get_playlist_track_ids = get_existing_track_ids

    added, skipped, not_found = client.add_tracks_to_playlist(
        "playlist-id", [existing, new, unresolved]
    )

    assert added == 1
    assert skipped == 1
    assert not_found == [unresolved]
    assert client.sp.uris == ["spotify:track:new"]
    assert len(fetches) == 1


def test_track_exists_ignores_unavailable_playlist_items():
    client = object.__new__(SpotifyClient)
    client.get_playlist_tracks = lambda _: [
        {"track": None},
        {},
        {"track": {"uri": "spotify:track:other"}},
    ]

    song = Song("Song", "Artist", spotify_uri="spotify:track:target")

    assert client.track_exists_in_playlist("playlist-id", song) is False


def test_rate_limit_error_keeps_retry_after_value():
    error = type(
        "RateLimitResponse",
        (),
        {"http_status": 429, "headers": {"Retry-After": "1206"}},
    )()

    try:
        SpotifyClient._raise_if_rate_limited(error)
    except SpotifyRateLimitError as rate_limit_error:
        assert rate_limit_error.retry_after == "1206"
        assert "1206" in str(rate_limit_error)
    else:
        assert False, "Expected SpotifyRateLimitError"

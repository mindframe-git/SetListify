from src.setlistify.models import Song
from src.setlistify.spotify_client import SpotifyClient


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
    client.track_exists_in_playlist = lambda _, song: song is existing

    added, skipped, not_found = client.add_tracks_to_playlist(
        "playlist-id", [existing, new, unresolved]
    )

    assert added == 1
    assert skipped == 1
    assert not_found == [unresolved]
    assert client.sp.uris == ["spotify:track:new"]


def test_track_exists_ignores_unavailable_playlist_items():
    client = object.__new__(SpotifyClient)
    client.get_playlist_tracks = lambda _: [
        {"track": None},
        {},
        {"track": {"uri": "spotify:track:other"}},
    ]

    song = Song("Song", "Artist", spotify_uri="spotify:track:target")

    assert client.track_exists_in_playlist("playlist-id", song) is False

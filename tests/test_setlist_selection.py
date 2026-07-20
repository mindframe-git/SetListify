from src.setlistify import cli
from src.setlistify.models import Setlist
from src.setlistify.setlistfm_client import SetlistFmClient


def test_get_artist_setlists_page_returns_api_pagination():
    client = object.__new__(SetlistFmClient)
    client._make_request = lambda _, __: {
        "total": 45,
        "itemsPerPage": 20,
        "setlist": [{"id": "one"}, {"id": "two"}],
    }

    setlists, total_pages = client.get_artist_setlists_page("artist-id", page=2)

    assert [item["id"] for item in setlists] == ["one", "two"]
    assert total_pages == 3


def test_search_artists_page_returns_api_pagination():
    client = object.__new__(SetlistFmClient)
    client._make_request = lambda _, __: {
        "total": 31,
        "itemsPerPage": 30,
        "artist": [{"name": "First"}, {"name": "Second"}],
    }

    artists, total_pages = client.search_artists_page("slaughter", page=1)

    assert [artist["name"] for artist in artists] == ["First", "Second"]
    assert total_pages == 2


def test_setlist_song_count_counts_songs_from_all_sets():
    setlist = {
        "sets": {
            "set": [
                {"song": [{"name": "One"}, {"name": "Two"}]},
                {"song": {"name": "Encore"}},
            ]
        }
    }

    assert cli.setlist_song_count(setlist) == "3"


def test_playlist_artist_names_ignores_unavailable_items():
    items = [
        {"track": None},
        {},
        {"track": {"artists": [{"name": "Artist A"}, {"name": "Artist B"}]}},
        {"track": {"artists": [{"name": "Artist A"}]}},
    ]

    assert cli.playlist_artist_names(items) == {"Artist A", "Artist B"}


def test_playlist_track_count_falls_back_to_loaded_items():
    assert cli.playlist_track_count({"name": "Playlist"}, [{}, {}, {}]) == 3
    assert cli.playlist_track_count({"tracks": {"total": 12}}, [{}]) == 12


def test_choose_artist_can_move_to_next_page(monkeypatch):
    class FakeSetlistClient:
        def search_artists_page(self, _, page):
            return ([{"name": f"Artist {page}", "mbid": f"artist-{page}"}], 2)

    answers = iter(["n", "1"])
    monkeypatch.setattr(cli.typer, "prompt", lambda _: next(answers))

    assert cli.choose_artist(FakeSetlistClient(), "Artist") == {
        "name": "Artist 2",
        "mbid": "artist-2",
    }


def test_choose_artist_raises_cancellation_exception(monkeypatch):
    class FakeSetlistClient:
        def search_artists_page(self, _, page):
            return ([{"name": "Artist", "mbid": "artist-id"}], 2)

    monkeypatch.setattr(cli.typer, "prompt", lambda _: "q")

    try:
        cli.choose_artist(FakeSetlistClient(), "Artist")
    except cli.SelectionCancelled:
        pass
    else:
        assert False, "Expected SelectionCancelled"


def test_choose_setlist_uses_the_selected_artist(monkeypatch):
    selected_setlist = Setlist(
        artist_name="Artist 2",
        event_date="2026-01-02",
        venue_name="Venue 2",
        venue_city="City",
        setlist_id="selected",
        setlist_url="https://example.test",
    )

    class FakeSetlistClient:
        def get_artist_setlists_page(self, _, page):
            return ([{"id": f"id-{page}", "eventDate": "2026-01-02", "venue": {"name": "Venue", "city": {"name": "City"}}}], 2)

        def get_setlist(self, setlist_id):
            assert setlist_id == "id-2"
            return selected_setlist

    answers = iter(["n", "1"])
    monkeypatch.setattr(cli.typer, "prompt", lambda _: next(answers))

    assert cli.choose_setlist(
        FakeSetlistClient(), {"name": "Artist", "mbid": "artist-id"}
    ) is selected_setlist

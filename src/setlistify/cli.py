"""CLI interface for Setlistify using Typer.

Provides commands for managing Spotify playlists with setlist.fm data.
"""

import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich import box

from .config import Config
from .logging_config import setup_logging, get_logger
from .spotify_client import SpotifyClient
from .setlistfm_client import SetlistFmClient
from .cache import Cache
from .models import Song, Setlist, SyncResult, PlaylistStats


app = typer.Typer(help="Setlistify - Sync Spotify playlists with concert setlists")
console = Console()
logger = get_logger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def ensure_authenticated() -> tuple[SpotifyClient, Cache]:
    """Ensure Spotify authentication is configured.

    Returns:
        Tuple of (spotify_client, cache)

    Raises:
        typer.Exit: If authentication fails
    """
    try:
        spotify = SpotifyClient()
        cache = Cache()
        return spotify, cache
    except Exception as e:
        console.print(f"[red]✗ Authentication failed: {e}[/red]")
        raise typer.Exit(1)


def display_sync_summary(result: SyncResult) -> None:
    """Display sync operation summary.

    Args:
        result: SyncResult object
    """
    console.print()
    console.print("[bold cyan]Sync Summary[/bold cyan]")
    console.print(f"Artist: [bold]{result.artist}[/bold]")
    console.print(f"Total songs: {result.total_songs}")
    console.print(f"[green]Added: {result.added}[/green]")
    console.print(f"[yellow]Skipped (already in playlist): {result.skipped}[/yellow]")
    console.print(f"[red]Not found: {result.not_found}[/red]")
    success_rate = result.success_rate
    console.print(f"Success rate: [bold]{success_rate:.1f}%[/bold]")
    console.print()


def choose_artist(setlist_client: SetlistFmClient, artist_name: str) -> Optional[dict]:
    """Let the user select a matching artist from paginated results."""
    page = 1
    while True:
        candidates, total_pages = setlist_client.search_artists_page(artist_name, page)
        if not candidates:
            return None

        if len(candidates) == 1 and total_pages == 1:
            return candidates[0]

        table = Table(
            title=f"Artist matches for {artist_name} (page {page}/{total_pages})",
            box=box.ROUNDED,
        )
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Artist", style="magenta")
        table.add_column("Description", style="yellow")
        for index, candidate in enumerate(candidates, start=1):
            table.add_row(
                str(index),
                candidate.get("name", "Unknown"),
                candidate.get("disambiguation") or "-",
            )
        console.print(table)

        selection = typer.prompt(
            "Choose an artist number, [n]ext, [p]revious, or [q]uit"
        ).strip().lower()
        if selection == "q":
            return None
        if selection == "n":
            if page < total_pages:
                page += 1
            else:
                console.print("[yellow]Already on the last page.[/yellow]")
            continue
        if selection == "p":
            if page > 1:
                page -= 1
            else:
                console.print("[yellow]Already on the first page.[/yellow]")
            continue
        try:
            return candidates[int(selection) - 1]
        except (ValueError, IndexError):
            console.print("[red]Enter a listed number, n, p, or q.[/red]")


def setlist_song_count(setlist: dict) -> str:
    """Return the number of songs included in a setlist search result."""
    sets = setlist.get("sets", {})
    set_groups = sets.get("set", []) if isinstance(sets, dict) else sets
    if not isinstance(set_groups, list):
        set_groups = [set_groups]

    count = 0
    for set_group in set_groups:
        if not isinstance(set_group, dict):
            continue
        songs = set_group.get("song", [])
        count += len(songs) if isinstance(songs, list) else int(bool(songs))

    return str(count) if set_groups else "-"


def choose_setlist(setlist_client: SetlistFmClient, artist: dict) -> Optional[Setlist]:
    """Let the user select one of an artist's setlists, page by page.

    A full setlist is fetched only after the user selects a result.
    """
    if not artist.get("mbid"):
        logger.error("Selected artist has no MusicBrainz ID")
        return None

    page = 1
    while True:
        candidates, total_pages = setlist_client.get_artist_setlists_page(
            artist["mbid"], page
        )
        if not candidates:
            return None

        # Preserve the old non-interactive flow when setlist.fm has one result.
        if len(candidates) == 1 and total_pages == 1:
            selected = candidates[0]
            break

        table = Table(
            title=f"Setlists for {artist.get('name', 'artist')} (page {page}/{total_pages})",
            box=box.ROUNDED,
        )
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Venue", style="magenta")
        table.add_column("City", style="yellow")
        table.add_column("Songs", justify="right", style="cyan")
        table.add_column("Tour")

        for index, candidate in enumerate(candidates, start=1):
            venue = candidate.get("venue", {})
            city = venue.get("city", {}).get("name", "Unknown")
            table.add_row(
                str(index),
                candidate.get("eventDate", "Unknown"),
                venue.get("name", "Unknown"),
                city,
                setlist_song_count(candidate),
                candidate.get("tour", {}).get("name", "—"),
            )

        console.print(table)
        selection = typer.prompt(
            "Choose a venue number, [n]ext, [p]revious, or [q]uit"
        ).strip().lower()

        if selection == "q":
            return None
        if selection == "n":
            if page < total_pages:
                page += 1
            else:
                console.print("[yellow]Already on the last page.[/yellow]")
            continue
        if selection == "p":
            if page > 1:
                page -= 1
            else:
                console.print("[yellow]Already on the first page.[/yellow]")
            continue

        try:
            selected = candidates[int(selection) - 1]
        except (ValueError, IndexError):
            console.print("[red]Enter a listed number, n, p, or q.[/red]")
            continue
        break

    setlist_id = selected.get("id")
    if not setlist_id:
        logger.error("Setlist ID not found in selected result")
        return None
    return setlist_client.get_setlist(setlist_id)


# ============================================================================
# COMMANDS
# ============================================================================


@app.command()
def auth() -> None:
    """Authenticate with Spotify.

    Sets up OAuth credentials for accessing Spotify.
    """
    setup_logging()
    console.print("[cyan]Authenticating with Spotify...[/cyan]")

    try:
        spotify, _ = ensure_authenticated()
        user = spotify.get_current_user()
        console.print(f"[green]✓ Successfully authenticated as: {user.get('display_name', 'User')}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Authentication failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def config() -> None:
    """Check configuration status.

    Displays which environment variables are configured.
    """
    setup_logging()
    console.print("[bold]Configuration Status[/bold]")

    # Check configuration
    is_valid, errors = Config.validate()

    # Display settings
    table = Table(box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Value", style="green")

    settings = [
        ("SPOTIFY_CLIENT_ID", Config.SPOTIFY_CLIENT_ID[:10] + "..." if Config.SPOTIFY_CLIENT_ID else "NOT SET"),
        ("SPOTIFY_CLIENT_SECRET", "***" if Config.SPOTIFY_CLIENT_SECRET else "NOT SET"),
        ("SPOTIFY_REDIRECT_URI", Config.SPOTIFY_REDIRECT_URI),
        ("SPOTIFY_PLAYLIST_ID", Config.SPOTIFY_PLAYLIST_ID if Config.SPOTIFY_PLAYLIST_ID else "NOT SET"),
        ("SETLISTFM_API_KEY", "***" if Config.SETLISTFM_API_KEY else "NOT SET"),
    ]

    for setting, value in settings:
        status = "✓" if value != "NOT SET" else "✗"
        table.add_row(setting, status, value)

    console.print(table)

    if not is_valid:
        console.print()
        console.print("[red]Missing configuration:[/red]")
        for error in errors:
            console.print(f"  • {error}")
        raise typer.Exit(1)
    else:
        console.print("\n[green]✓ All configuration variables set[/green]")


@app.command()
def add(artist: str) -> None:
    """Select and add one of an artist's setlists to the playlist.

    Args:
        artist: Name of the artist
    """
    setup_logging()

    if not artist:
        console.print("[red]✗ Artist name is required[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Adding setlist for: {artist}[/cyan]")

    try:
        spotify, cache = ensure_authenticated()

        # Validate configuration
        is_valid, errors = Config.validate()
        if not is_valid:
            console.print("[red]✗ Configuration incomplete:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            raise typer.Exit(1)

        # Get setlist
        console.print("[cyan]Fetching setlist from setlist.fm...[/cyan]")
        setlist_client = SetlistFmClient()
        selected_artist = choose_artist(setlist_client, artist)
        if not selected_artist:
            console.print(f"[red]No artist found for: {artist}[/red]")
            raise typer.Exit(1)

        setlist = choose_setlist(setlist_client, selected_artist)

        if not setlist:
            console.print(f"[red]✗ No setlist found for: {artist}[/red]")
            raise typer.Exit(1)

        console.print(f"[green]✓ Found setlist: {setlist.venue_name}, {setlist.event_date}[/green]")
        console.print(f"  Songs: {setlist.song_count}")

        # Search on Spotify
        console.print("[cyan]Searching for songs on Spotify...[/cyan]")

        with Progress() as progress:
            task = progress.add_task("[cyan]Processing...", total=setlist.song_count)

            added = 0
            skipped = 0
            not_found = 0

            for song in setlist.songs:
                # Check cache first
                cached = cache.get_song(song.artist, song.name)
                if cached:
                    song.spotify_uri = cached.spotify_uri
                    song.album = cached.album
                    song.popularity = cached.popularity
                else:
                    # Search Spotify
                    result = spotify.search_track(song.name, song.artist)
                    if result:
                        # Keep the original object in ``setlist.songs``. Rebinding
                        # ``song`` here would leave that list without Spotify URIs.
                        song.spotify_uri = result.spotify_uri
                        song.album = result.album
                        song.popularity = result.popularity
                        cache.cache_song(song)
                    else:
                        not_found += 1

                progress.update(task, advance=1)

            # Add to playlist
            console.print("[cyan]Adding tracks to playlist...[/cyan]")
            added_count, skipped_count, unresolved_songs = spotify.add_tracks_to_playlist(
                Config.SPOTIFY_PLAYLIST_ID,
                setlist.songs,
                skip_duplicates=True,
            )

            skipped += skipped_count
            # This normally matches the failed searches above. Count any remaining
            # unresolved songs as a safeguard without double-counting them.
            not_found = max(not_found, len(unresolved_songs))

            # Update cache with artist
            cache.add_artist(artist, len(setlist.songs), setlist.setlist_id)

        # Display summary
        result = SyncResult(
            artist=artist,
            total_songs=setlist.song_count,
            added=added_count,
            skipped=skipped,
            not_found=not_found,
        )
        display_sync_summary(result)

    except Exception as e:
        logger.exception("Error adding artist")
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def stats() -> None:
    """Show playlist statistics.

    Displays summary of tracked artists and playlist composition.
    """
    setup_logging()

    try:
        spotify, cache = ensure_authenticated()

        console.print("[cyan]Gathering statistics...[/cyan]")

        # Get playlist info
        playlist = spotify.get_playlist(Config.SPOTIFY_PLAYLIST_ID)
        tracks = spotify.get_playlist_tracks(Config.SPOTIFY_PLAYLIST_ID)

        # Get tracked artists
        artists = cache.get_all_artists()

        # Count unique artists in playlist
        unique_artists_set = set()
        for track in tracks:
            for artist in track["track"]["artists"]:
                unique_artists_set.add(artist["name"])

        console.print()
        console.print("[bold cyan]Playlist Statistics[/bold cyan]")
        console.print(f"Playlist: [bold]{playlist['name']}[/bold]")
        console.print(f"Total tracks: {playlist['tracks']['total']}")
        console.print(f"Unique artists: {len(unique_artists_set)}")
        console.print()

        if artists:
            console.print("[bold cyan]Tracked Artists[/bold cyan]")
            table = Table(box=box.ROUNDED)
            table.add_column("Artist", style="cyan")
            table.add_column("Added", style="magenta")
            table.add_column("Last Updated", style="green")
            table.add_column("Songs", style="yellow")

            for artist_name in artists:
                history = cache.get_artist_history(artist_name)
                if history:
                    added_at = history.added_at.strftime("%Y-%m-%d")
                    updated_at = history.last_updated.strftime("%Y-%m-%d") if history.last_updated else "—"
                    table.add_row(artist_name, added_at, updated_at, str(history.song_count))

            console.print(table)

    except Exception as e:
        logger.exception("Error getting statistics")
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()

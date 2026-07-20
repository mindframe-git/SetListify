# Guía rápida de Setlistify

## 1. Instala dependencias

```powershell
python -m uv sync --extra dev
.\.venv\Scripts\Activate.ps1
```

## 2. Configura `.env`

```powershell
Copy-Item .env.example .env
```

Edita `.env` con tus credenciales de Spotify y la clave de setlist.fm. Para
`SPOTIFY_PLAYLIST_ID`, copia el tramo final de una URL como:

```text
https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
```

El valor sería `37i9dQZF1DXcBWIGoYBM5M`.

## 3. Verifica y autentica

```powershell
python -m src.setlistify.cli config
python -m src.setlistify.cli auth
```

## 4. Añade un setlist

```powershell
python -m src.setlistify.cli add "Helloween"
```

Si setlist.fm encuentra varios artistas, elige uno en el primer menú. Después
elige un venue/setlist en el segundo menú. Ambos permiten `n` (siguiente), `p`
(anterior) y `q` (cancelar). La tabla de setlists muestra cuántas canciones
contiene cada resultado cuando setlist.fm proporciona ese dato.

## Comandos

```text
auth    Autentica Spotify mediante OAuth.
config  Comprueba las variables de configuración.
add     Selecciona artista y setlist, y añade sus canciones a la playlist.
stats   Muestra estadísticas de playlist e historial local.
```

## Problemas frecuentes

- `Invalid base62 id`: `SPOTIFY_PLAYLIST_ID` no es el ID de una playlist.
- `Invalid limit` en Search: actualiza la aplicación; la búsqueda de Spotify
  acepta un máximo de 10 resultados.
- Una canción eliminada en la playlist no bloquea la sincronización: se ignora
  al comprobar duplicados.
- Si no hay coincidencias, revisa el nombre del artista en setlist.fm.

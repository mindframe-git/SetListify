# Setlistify

Setlistify añade a una playlist de Spotify las canciones de un setlist de
[setlist.fm](https://www.setlist.fm/). La aplicación permite elegir el artista
correcto cuando una búsqueda es ambigua y, después, el concierto concreto.

## Requisitos

- Python 3.12 o superior.
- Una aplicación de Spotify y una playlist de destino.
- Una clave de API de setlist.fm.

## Instalación

```powershell
python -m uv sync --extra dev
```

En Windows, activa el entorno si vas a invocar Python directamente:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Configuración

Copia `.env.example` a `.env` y completa las variables:

```dotenv
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
SPOTIFY_PLAYLIST_ID=your_playlist_id
SETLISTFM_API_KEY=your_setlistfm_key
LOG_LEVEL=INFO
CACHE_DB=.cache/setlistify.db
```

`SPOTIFY_PLAYLIST_ID` es el identificador de la URL de la playlist: el texto
después de `/playlist/`. Debe ser un ID de playlist de Spotify, no el Client ID
de la aplicación.

Comprueba la configuración con:

```powershell
python -m src.setlistify.cli config
```

## Uso

Autentica Spotify una vez:

```powershell
python -m src.setlistify.cli auth
```

Para añadir canciones:

```powershell
python -m src.setlistify.cli add "Slaughter to Prevail"
```

El comando `add` sigue este flujo:

1. Busca artistas en setlist.fm. Si hay más de una coincidencia, muestra un
   menú paginado con nombre y descripción.
2. Selecciona el artista con su número. Usa `n` para la página siguiente, `p`
   para la anterior y `q` para cancelar.
3. Muestra los setlists/venues de ese artista, también paginados. La tabla
   incluye fecha, venue, ciudad, número de canciones y gira.
4. Descarga el setlist elegido, elimina elementos no musicales y busca cada
   canción en Spotify.
5. Añade las pistas encontradas, manteniendo el orden del setlist y evitando
   duplicados.

La columna `Songs` puede mostrar `-` cuando el resumen de setlist.fm no trae
las canciones; al elegir ese setlist se descarga su detalle completo.

Consulta estadísticas de la playlist y el historial local:

```powershell
python -m src.setlistify.cli stats
```

## Comportamiento de Spotify

- Las búsquedas de canciones usan hasta 9 resultados, dentro del límite actual
  de la API de Spotify.
- Se prefieren coincidencias de artista y se descartan álbumes en directo,
  tributos y recopilaciones de covers cuando es posible.
- Los resultados se guardan en una caché SQLite para reducir llamadas futuras.
- Las pistas ya presentes no se vuelven a añadir.
- Los elementos eliminados o no disponibles de la playlist se ignoran al
  comprobar duplicados.
- La playlist se descarga una sola vez por sincronización para comprobar
  duplicados. Si Spotify responde `429`, el comando muestra el tiempo de
  reintento indicado por Spotify y se detiene.

## Desarrollo

Ejecuta las pruebas después de instalar las dependencias de desarrollo:

```powershell
python -m pytest -q
```

La documentación técnica está en [ARCHITECTURE.md](ARCHITECTURE.md) y la guía
rápida en [QUICKSTART.md](QUICKSTART.md).

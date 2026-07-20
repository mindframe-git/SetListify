# Arquitectura

## Componentes

| Módulo | Responsabilidad |
|---|---|
| `cli.py` | Comandos Typer, menús Rich y flujo de sincronización. |
| `setlistfm_client.py` | Búsqueda paginada de artistas y setlists; descarga y análisis del setlist elegido. |
| `spotify_client.py` | OAuth, búsqueda de pistas, consulta de playlist y altas por lotes. |
| `cache.py` | Caché SQLite de canciones e historial de artistas. |
| `models.py` | Modelos `Song`, `Setlist` y resultados de sincronización. |
| `config.py` | Variables de entorno y rutas del proyecto. |
| `utils.py` | Normalización de URIs y filtros de álbumes. |

## Flujo de `add`

```text
consulta del usuario
       |
       v
búsqueda paginada de artistas ----> selección de artista
       |                                      |
       +--------------------------------------+
                                              v
                              setlists paginados del artista
                                              |
                                              v
                                  selección de venue/setlist
                                              |
                                              v
                              detalle del setlist y sus canciones
                                              |
                                              v
                       caché / búsqueda de cada pista en Spotify
                                              |
                                              v
                      comprobación de duplicados y alta en playlist
```

Las páginas se solicitan a setlist.fm solo cuando el usuario navega a ellas.
La selección de venue incluye el número de canciones disponible en el resumen
de la API; la descarga completa se retrasa hasta que el usuario elige uno.

## Persistencia y resiliencia

- La caché SQLite almacena artista, canción, URI, álbum y popularidad.
- La caché se usa antes de llamar al endpoint Search de Spotify.
- Las pistas sin URI se contabilizan como no encontradas y no se envían a
  Spotify.
- Para evitar duplicados se consulta la playlist una sola vez por
  sincronización y se compara contra un conjunto de URIs en memoria. Los
  elementos sin `track` o sin URI —por ejemplo, pistas eliminadas— se ignoran
  con seguridad.
- Las altas se envían en lotes de hasta 100 URIs.

## Límites externos

- setlist.fm se limita internamente a aproximadamente 0,6 solicitudes por
  segundo.
- Search de Spotify recibe un máximo de 9 resultados por consulta, compatible
  con su límite de 10.

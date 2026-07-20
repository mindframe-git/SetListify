# Estado actual del proyecto

Setlistify es una CLI de Python que transforma un setlist elegido de
setlist.fm en pistas de una playlist de Spotify.

## Funcionalidad disponible

- OAuth de Spotify y validación de configuración.
- Búsqueda paginada de artistas de setlist.fm con selección explícita.
- Selección paginada de venues/setlists del artista elegido.
- Columna de número de canciones en la selección de setlists cuando la API lo
  proporciona.
- Búsqueda de canciones en Spotify, filtrado de resultados no deseados y caché
  SQLite.
- Prevención de duplicados y tolerancia a elementos de playlist eliminados o
  no disponibles.
- Estadísticas de playlist e historial de artistas.

## Comandos

| Comando | Estado |
|---|---|
| `auth` | Implementado |
| `config` | Implementado |
| `add "Artista"` | Implementado, con selección de artista y setlist |
| `stats` | Implementado |

## Verificación

Hay pruebas unitarias e integración bajo `tests/`, incluidas pruebas para la
selección paginada y para entradas de playlist no disponibles. Instala las
dependencias de desarrollo con `python -m uv sync --extra dev` y ejecuta
`python -m pytest -q` para verificarlas.

## Límites conocidos

- El conteo del menú puede no estar disponible en algunos resúmenes de
  setlist.fm; se representa como `-`.
- La selección de artista y venue es interactiva; está diseñada para usarse
  desde una terminal.

# Changelog

Todas las fechas se expresan en formato `YYYY-MM-DD`.

## 2026-07-20

### Añadido

- Selección interactiva y paginada de artistas cuando setlist.fm devuelve más
  de una coincidencia.
- Selección interactiva y paginada de venues/setlists para el artista elegido.
- Columna `Songs` en el menú de setlists, cuando el resumen de setlist.fm
  contiene la información de canciones.
- Mensaje de cancelación al usar `q` en los menús, con despedida ASCII de
  SetListify.
- Pruebas para selección paginada, conteo de canciones, elementos de playlist
  no disponibles, límites de Spotify y respuestas alternativas de playlist.
- `CHANGELOG.md` para registrar cambios del proyecto.

### Corregido

- La búsqueda de Spotify usa `limit=9`, compatible con el máximo actual del
  endpoint Search.
- Las URIs encontradas en Spotify se conservan en los objetos del setlist antes
  de intentar añadirlas a la playlist.
- El resumen diferencia correctamente canciones no encontradas y canciones ya
  presentes en la playlist.
- Las entradas eliminadas o no disponibles de una playlist de Spotify ya no
  provocan errores `KeyError: 'track'` ni durante la sincronización ni en
  `stats`.
- `stats` tolera respuestas de metadatos de playlist que no incluyen
  `tracks.total`, usando los elementos descargados como respaldo.
- La cancelación mediante `q` ya no se registra como un error ni muestra un
  traceback.

### Cambiado

- La comprobación de duplicados descarga la playlist una sola vez por
  sincronización y compara las URIs en memoria, en lugar de descargarla para
  cada canción.
- Las respuestas HTTP `429` de Spotify se presentan con el valor `Retry-After`
  recibido, sin tratar las canciones afectadas como no encontradas.
- La documentación (`README`, guía rápida, arquitectura, resumen, entregables
  e índice) se actualizó para reflejar el flujo y los límites actuales.

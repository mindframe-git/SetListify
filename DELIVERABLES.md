# Funcionalidades entregadas

## CLI y configuración

- [x] `auth`, `config`, `add` y `stats`.
- [x] Configuración por `.env` para Spotify y setlist.fm.
- [x] Caché local de token OAuth y base de datos SQLite.

## Selección desde setlist.fm

- [x] Búsqueda de artistas con menú paginado.
- [x] Selección explícita de artista cuando hay varias coincidencias.
- [x] Selección paginada de venues/setlists para el artista elegido.
- [x] Fecha, venue, ciudad, gira y número de canciones en el menú de setlists.

## Integración Spotify

- [x] Búsqueda de pistas con límite compatible con la API actual.
- [x] Filtros para preferir versiones de estudio y evitar álbumes en directo,
  tributos y covers.
- [x] Añadido de pistas por lotes y prevención de duplicados.
- [x] Manejo seguro de elementos de playlist eliminados o no disponibles.

## Calidad

- [x] Pruebas para caché, modelos, utilidades, selección paginada y cliente de
  Spotify.
- [x] Documentación de instalación, uso y arquitectura actualizada.
- [ ] Ejecutar la suite localmente requiere instalar las dependencias de
  desarrollo (`python -m uv sync --extra dev`).

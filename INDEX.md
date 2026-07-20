# Índice de documentación

- [README.md](README.md): instalación, configuración, uso y comportamiento de
  Spotify.
- [QUICKSTART.md](QUICKSTART.md): puesta en marcha y primer comando `add`.
- [ARCHITECTURE.md](ARCHITECTURE.md): componentes, flujo de sincronización y
  resiliencia.
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md): estado funcional actual.
- [DELIVERABLES.md](DELIVERABLES.md): funcionalidades entregadas y verificación.

Para empezar:

```powershell
python -m uv sync --extra dev
Copy-Item .env.example .env
python -m src.setlistify.cli config
python -m src.setlistify.cli auth
python -m src.setlistify.cli add "Nombre del artista"
```

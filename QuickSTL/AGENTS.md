# QuickSTL add-in guidance for future agents

This add-in runs inside Fusion 360 and is loaded by `QuickSTL.py`. Keep the entrypoint minimal and put
logic in the `quickstl/` package so the structure stays modular.

## Rules of the road
- Keep `QuickSTL.py` as a tiny wrapper that only exports `run`/`stop`.
- Prefer adding or editing functions in focused modules under `quickstl/` instead of growing a monolith.
- Avoid side effects at import time (no filesystem writes or Fusion API calls outside functions).
- Never wrap imports in `try/except`; let missing modules fail loudly.
- Preserve the JSON config schema in `config.json` (backward compatible additions only).
- Maintain Windows-only assumptions where required (`os.startfile`, slicer EXE paths).
- Log errors with `quickstl/logging_utils.py` rather than `print`.

## Where things live
- Configuration + per-document folders: `quickstl/config.py`
- Export logic (STL/OBJ→STL): `quickstl/export.py`, `quickstl/obj_stl.py`
- UI command handlers: `quickstl/command.py`
- Toast/preview palette: `quickstl/toast.py`
- Diagnostics JSON: `quickstl/diagnostics.py`

When changing behavior, update the narrowest module possible and keep functions small and single-purpose.

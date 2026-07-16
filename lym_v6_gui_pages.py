from __future__ import annotations

import base64
from pathlib import Path

_payload_dir = Path(__file__).resolve().parent / "lym_v6_payloads"
_parts = sorted(_payload_dir.glob("gui_pages.part*"))
if not _parts:
    raise RuntimeError("Faltan los archivos de interfaz gui_pages de LYM V6.")
_source = base64.b64decode("".join(p.read_text(encoding="ascii") for p in _parts)).decode("utf-8")
exec(compile(_source, "lym_v6_gui_pages_source.py", "exec"), globals(), globals())

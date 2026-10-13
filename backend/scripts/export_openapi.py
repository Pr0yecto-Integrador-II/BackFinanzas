"""Exporta el contrato OpenAPI para `ng-openapi-gen`.

Uso (desde backend/): `uv run python scripts/export_openapi.py [ruta]`
Por defecto escribe `openapi.json`. Con `--check` falla si el archivo está desactualizado.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("JWT_SECRET", "x" * 32)  # solo para construir la app; no se usa

from app.main import create_app  # noqa: E402


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--check"]
    path = Path(args[0] if args else "openapi.json")
    text = json.dumps(create_app().openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            print(f"{path} está desactualizado: ejecuta scripts/export_openapi.py", file=sys.stderr)
            return 1
        return 0
    path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

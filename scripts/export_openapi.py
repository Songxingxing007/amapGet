"""Write the backend OpenAPI schema to docs/openapi.json."""

from __future__ import annotations

import json
import pathlib

from app.main import app

OUT = pathlib.Path(__file__).resolve().parents[1] / "docs" / "openapi.json"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()

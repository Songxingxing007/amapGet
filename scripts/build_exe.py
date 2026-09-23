"""Build the Windows bundle and both release archives.

    uv run python scripts/build_exe.py

Produces:
    dist/amap-poi-aoi/                    onedir bundle with amap-poi-aoi.exe
    dist/amap-poi-aoi-<version>-win64.zip bundle for people without Python
    dist/amap-poi-aoi-<version>-source.zip repository source, no exe
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
VERSION = "0.1.0"
BUNDLE = DIST / "amap-poi-aoi"

USAGE = """amap-poi-aoi {version} (Windows x64, no Python required)

1. Double click amap-poi-aoi.exe
2. A browser opens at http://127.0.0.1:8000
3. Go to the config page, paste your Amap Web service key and click save
4. Upload a CSV or Excel file with a name column, then run round one

Notes
- AOI boundary query needs a ticket-approved key from Amap.
- Config and database live in the data folder next to the exe.
- Closing the console window stops the server.
Full guide: 使用说明.md in the same folder.
"""


def run_pyinstaller() -> None:
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        "amap-poi-aoi",
        "--onedir",
        "--console",
        "--paths",
        "backend",
        "--add-data",
        f"frontend/dist{os.pathsep}frontend/dist",
        "--hidden-import",
        "uvicorn.logging",
        "--hidden-import",
        "uvicorn.loops.auto",
        "--hidden-import",
        "uvicorn.protocols.http.auto",
        "--hidden-import",
        "uvicorn.protocols.websockets.auto",
        "--hidden-import",
        "uvicorn.lifespan.on",
        "scripts/launcher.py",
    ]
    print("running:", " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True)


def prepare_bundle() -> None:
    (BUNDLE / "data").mkdir(parents=True, exist_ok=True)
    (BUNDLE / "data" / ".gitkeep").write_text("", encoding="utf-8")
    (BUNDLE / "使用说明.txt").write_text(USAGE.format(version=VERSION), encoding="utf-8")
    readme = ROOT / "README.md"
    if readme.exists():
        shutil.copyfile(readme, BUNDLE / "使用说明.md")


def zip_dir(source: pathlib.Path, target: pathlib.Path, arc_root: str = "") -> None:
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_dir():
                continue
            relative = path.relative_to(source)
            name = str(pathlib.PurePosixPath(arc_root) / pathlib.PurePosixPath(relative.as_posix()))
            archive.write(path, name)
    print(f"wrote {target} ({target.stat().st_size / 1024 / 1024:.1f} MB)")


def zip_source() -> None:
    listing = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.split()
    target = DIST / f"amap-poi-aoi-{VERSION}-source.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in listing:
            path = ROOT / name
            if path.exists():
                archive.write(path, f"amap-poi-aoi-{VERSION}/{name}")
    print(f"wrote {target} ({target.stat().st_size / 1024 / 1024:.1f} MB)")


def main() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    run_pyinstaller()
    prepare_bundle()
    zip_dir(BUNDLE, DIST / f"amap-poi-aoi-{VERSION}-win64.zip", "amap-poi-aoi")
    zip_source()
    print("done")


if __name__ == "__main__":
    main()

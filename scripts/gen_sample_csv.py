"""Generate a sample CSV for load testing. Usage: uv run python scripts/gen_sample_csv.py 10000"""

from __future__ import annotations

import pathlib
import sys

NL = chr(10)
PREFIXES = ["\u8d8a\u79c0", "\u5929\u6cb3", "\u767d\u4e91", "\u6d77\u73e0", "\u8354\u6e7e", "\u9ec4\u57d4", "\u756a\u79ba", "\u82b1\u90fd", "\u5357\u6c99", "\u589e\u57ce"]
SUFFIXES = ["\u516c\u56ed", "\u793e\u533a\u516c\u56ed", "\u6e38\u56ed", "\u68ee\u6797\u516c\u56ed"]


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    target = pathlib.Path(__file__).resolve().parents[1] / "data" / f"sample_{count}.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = ["\u540d\u79f0,\u884c\u653f\u533a"]
    for index in range(count):
        name = f"{PREFIXES[index % len(PREFIXES)]}{SUFFIXES[index % len(SUFFIXES)]}{index}"
        lines.append(f"{name},\u8d8a\u79c0\u533a")
    target.write_text(NL.join(lines) + NL, encoding="utf-8")
    print(f"wrote {target} ({count} rows)")


if __name__ == "__main__":
    main()

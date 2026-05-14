"""
mineru_pipeline.fingerprint
~~~~~~~~~~~~~~~~~~~~~~~~~~~
SHA-256 content fingerprints for all Markdown files under docs/.

Usage:
    python -m mineru_pipeline.fingerprint [--docs-dir DIR] [--out FILE]
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def compute(docs_dir: Path) -> dict[str, str]:
    return {
        str(p.relative_to(docs_dir)): sha256(p)
        for p in sorted(docs_dir.rglob("*.md"))
    }


def diff(old: dict, new: dict) -> list[str]:
    lines = []
    for k in sorted(set(old) | set(new)):
        if k not in old:
            lines.append(f"  + {k}  (new)")
        elif k not in new:
            lines.append(f"  - {k}  (removed)")
        elif old[k] != new[k]:
            lines.append(f"  ~ {k}  (changed)")
    return lines


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Fingerprint docs/ Markdown files")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--out", default="reports/fingerprints.json")
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    current = compute(docs_dir)

    if out_path.exists():
        previous = json.loads(out_path.read_text(encoding="utf-8"))
        changes = diff(previous, current)
        if changes:
            print("Fingerprint diff:")
            print("\n".join(changes))
        else:
            print("No changes detected.")
    else:
        print(f"No previous fingerprints; creating {out_path}")

    out_path.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Fingerprints written: {len(current)} files → {out_path}")


if __name__ == "__main__":
    main()

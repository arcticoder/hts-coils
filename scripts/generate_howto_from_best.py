#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def main():
    best_path = ROOT/"artifacts"/"best_config.json"
    out_md = ROOT/"docs"/"howto_5T.md"
    if not best_path.exists():
        print("best_config.json not found; run scripts/optimize_config.py first")
        return
    best = json.loads(best_path.read_text())
    md = out_md.read_text() if out_md.exists() else "# How to reach 5 T\n\n"
    md += "\n\nBest found configuration (auto):\n\n"
    md += "```json\n" + json.dumps(best, indent=2) + "\n```\n"
    out_md.write_text(md)
    print(json.dumps({"status": "ok", "updated": str(out_md)}, indent=2))

if __name__ == "__main__":
    main()

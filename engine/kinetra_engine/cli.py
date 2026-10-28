"""CLI: python -m kinetra_engine.cli VIDEO --protocol DEMO_FLEX_CODO_L --out salida.json|csv"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .protocols import PROTOCOLS
from .video import process_video, summarize, frames_as_dicts

DEFAULT_MODEL = Path(__file__).resolve().parent.parent / "models" / "pose_landmarker_full.task"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Kinetra: medición angular desde video (demostración técnica)")
    ap.add_argument("video", type=Path)
    ap.add_argument("--protocol", default="DEMO_FLEX_CODO_L", choices=sorted(PROTOCOLS))
    ap.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    ap.add_argument("--out", type=Path, required=True, help=".json o .csv")
    a = ap.parse_args(argv)

    if not a.model.is_file():
        print(f"ERROR: modelo no encontrado: {a.model}", file=sys.stderr)
        return 2
    proto = PROTOCOLS[a.protocol]
    try:
        info, frames, config = process_video(a.video, proto, a.model)
    except FileNotFoundError as e:
        print(f"ERROR: video no encontrado: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    summary = summarize(frames)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    if a.out.suffix.lower() == ".csv":
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(asdict(frames[0]).keys()) if frames else ["frame_index"])
            w.writeheader()
            w.writerows(frames_as_dicts(frames))
        meta = a.out.with_suffix(".meta.json")
    else:
        meta = a.out
    doc = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "video": {**asdict(info), "path": Path(info.path).name},
        "protocol": asdict(proto),
        "config": config,
        "summary": summary,
    }
    if meta == a.out:
        doc["frames"] = frames_as_dicts(frames)
    meta.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

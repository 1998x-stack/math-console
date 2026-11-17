#!/usr/bin/env python3
"""Summarize observed agent run events; unknown costs are NULL, never invented."""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path


def summarize(path: Path) -> dict:
    events = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    status = Counter(str(x.get("status", "unknown")) for x in events)
    stages = Counter(str(x.get("stage", "unknown")) for x in events)
    def all_reported(field, kind):
        return bool(events) and all(isinstance(x.get(field), kind) for x in events)
    tokens = all_reported("input_tokens", int) and all_reported("output_tokens", int)
    cost = all_reported("cost_usd", (int, float))
    timing = all_reported("duration_ms", (int, float))
    return {
        "events": len(events), "statuses": dict(status), "stages": dict(stages),
        "token_coverage": "complete" if tokens else "missing_or_partial",
        "total_input_tokens": sum(x["input_tokens"] for x in events) if tokens else None,
        "total_output_tokens": sum(x["output_tokens"] for x in events) if tokens else None,
        "cost_coverage": "complete" if cost else "missing_or_partial",
        "total_cost_usd": round(sum(x["cost_usd"] for x in events), 6) if cost else None,
        "latency_coverage": "complete" if timing else "missing_or_partial",
        "total_duration_ms": sum(x["duration_ms"] for x in events) if timing else None,
        "caveat": "Reported usage is not proof of billing or of true subagent invocation.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(summarize(args.events), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(result, encoding="utf-8")
    print(result, end="")


if __name__ == "__main__":
    main()

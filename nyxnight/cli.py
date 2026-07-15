"""NyxNight command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

from nyxnight.models import PlanResponse
from nyxnight.planner import create_plan, sample_request


def doctor() -> int:
    plan: PlanResponse = create_plan(sample_request())
    web = Path(__file__).resolve().parent / "web"
    required = [web / "index.html", web / "styles.css", web / "app.js"]
    if len(plan.stops) != 3 or not all(path.is_file() for path in required):
        print("NyxNight doctor: FAIL")
        return 1
    print(
        "NyxNight doctor: PASS "
        f"mode={plan.mode} stops={len(plan.stops)} total=${plan.estimated_total_per_person:.2f}"
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="nyxnight")
    subcommands = parser.add_subparsers(dest="command", required=True)
    serve = subcommands.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8088)
    subcommands.add_parser("doctor")
    args = parser.parse_args()
    if args.command == "doctor":
        raise SystemExit(doctor())
    uvicorn.run("nyxnight.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()

"""Execute the ADK factory and preserve a provenance receipt."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from nyxnight_factory.agents import FACTORY_ROOT, build_workflow

APP_NAME = "nyxnight_factory"
USER_ID = "shaev"
SESSION_ID = "nyxnight-build"


def _manifest(root: Path) -> list[dict[str, str]]:
    files: list[dict[str, str]] = []
    for path in sorted(root.rglob("*")):
        ignored = {
            ".git",
            ".venv",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".verify-dist",
            "__pycache__",
            "build",
            "dist",
        }
        if not path.is_file() or any(
            part in ignored or part.endswith(".egg-info") for part in path.parts
        ):
            continue
        relative = path.relative_to(root).as_posix()
        if relative == "docs/adk-generation-receipt.json":
            continue
        files.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return files


def _clean_transients(output: Path) -> None:
    for relative in (
        ".verify-dist",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "build",
        "dist",
    ):
        shutil.rmtree(output / relative, ignore_errors=True)
    for path in output.glob("*.egg-info"):
        shutil.rmtree(path, ignore_errors=True)
    for path in output.rglob("__pycache__"):
        shutil.rmtree(path, ignore_errors=True)


def _copy_factory_snapshot(output: Path) -> None:
    target = output / "factory"
    target.mkdir(parents=True, exist_ok=True)
    for relative in (
        "README.md",
        "pyproject.toml",
        "nyxnight_factory",
        "blueprint",
        "tests",
    ):
        source = FACTORY_ROOT / relative
        destination = target / relative
        if source.is_dir():
            shutil.copytree(
                source,
                destination,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
            )
        else:
            shutil.copy2(source, destination)


async def execute(output: Path, force: bool) -> dict[str, Any]:
    if output.exists():
        if not force:
            raise FileExistsError(f"Output exists; refuse to overwrite without --force: {output}")
        shutil.rmtree(output)

    workflow = build_workflow(output)
    sessions = InMemorySessionService()  # type: ignore[no-untyped-call]
    await sessions.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state={
            "request": "Create NyxNight as a standalone application",
            "output_root": str(output),
            "runtime_adk_dependency_allowed": False,
        },
    )
    runner = Runner(
        agent=workflow,
        app_name=APP_NAME,
        session_service=sessions,
    )
    message = types.Content(
        role="user",
        parts=[types.Part(text="Create, test, and package NyxNight now.")],
    )
    events: list[dict[str, Any]] = []
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=message,
    ):
        state_delta = dict(event.actions.state_delta) if event.actions else {}
        events.append(
            {
                "author": event.author,
                "state_delta": state_delta,
                "text": (
                    event.content.parts[0].text
                    if event.content and event.content.parts and event.content.parts[0].text
                    else None
                ),
            }
        )
        print(f"ADK EVENT author={event.author} state={','.join(state_delta) or '-'}")

    session = await sessions.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )
    if session is None:
        raise RuntimeError("ADK session disappeared after workflow execution")
    required = {
        "stage:requirements",
        "stage:backend",
        "stage:frontend",
        "stage:verification",
    }
    missing = sorted(required - session.state.keys())
    if missing:
        raise RuntimeError(f"Workflow finished without required stages: {missing}")

    _clean_transients(output)
    _copy_factory_snapshot(output)
    receipt = {
        "schema": "nyxnight.adk-generation-receipt/v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "workflow": workflow.name,
        "workflow_class": f"{type(workflow).__module__}.{type(workflow).__name__}",
        "runner_class": f"{type(runner).__module__}.{type(runner).__name__}",
        "session_service_class": f"{type(sessions).__module__}.{type(sessions).__name__}",
        "agents": [agent.name for agent in workflow.sub_agents],
        "events": events,
        "final_state": dict(session.state),
        "output_root": str(output),
        "app_runtime_uses_adk": False,
        "manifest": _manifest(output),
    }
    receipt_path = output / "docs" / "adk-generation-receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("/home/maver/NyxNight"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        receipt = asyncio.run(execute(args.output.resolve(), args.force))
    except Exception as exc:
        print(f"NyxNight factory FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"NyxNight factory PASS workflow={receipt['workflow']} files={len(receipt['manifest'])}")


if __name__ == "__main__":
    main()

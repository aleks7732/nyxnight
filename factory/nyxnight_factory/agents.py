"""Google ADK workflow agents that create and verify NyxNight."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

from google.adk.agents import BaseAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types

FACTORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("/home/maver/NyxNight")

REQUIREMENTS_FILES = (
    ".gitignore",
    "README.md",
    "docs/PRODUCT_SPEC.md",
)
BACKEND_FILES = (
    "pyproject.toml",
    "nyxnight/__init__.py",
    "nyxnight/__main__.py",
    "nyxnight/models.py",
    "nyxnight/planner.py",
    "nyxnight/api.py",
    "nyxnight/cli.py",
    "tests/test_api.py",
    "tests/test_planner.py",
    "scripts/verify.sh",
)
FRONTEND_FILES = (
    "nyxnight/web/index.html",
    "nyxnight/web/styles.css",
    "nyxnight/web/app.js",
    "tests/test_ui_contract.py",
)


class ScopedFileAgent(BaseAgent):
    """ADK worker that emits an owned file scope from the factory blueprint."""

    blueprint_root: Path
    output_root: Path
    file_paths: tuple[str, ...]
    stage: str

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        written: list[dict[str, str]] = []
        self.output_root.mkdir(parents=True, exist_ok=True)
        for relative in self.file_paths:
            source = (self.blueprint_root / relative).resolve()
            destination = (self.output_root / relative).resolve()
            if self.blueprint_root.resolve() not in source.parents:
                raise RuntimeError(f"Blueprint path escaped root: {relative}")
            if self.output_root.resolve() not in destination.parents:
                raise RuntimeError(f"Output path escaped root: {relative}")
            if not source.is_file():
                raise RuntimeError(f"Missing blueprint input: {relative}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            payload = source.read_bytes()
            destination.write_bytes(payload)
            if destination.suffix == ".sh":
                destination.chmod(0o755)
            if destination.read_bytes() != payload:
                raise RuntimeError(f"Readback failed: {relative}")
            written.append(
                {
                    "path": relative,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )

        delta = {
            f"stage:{self.stage}": {
                "status": "complete",
                "agent": self.name,
                "files": written,
            }
        }
        yield Event(
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"{self.stage}: emitted {len(written)} files")],
            ),
            actions=EventActions(state_delta=delta),
        )


class VerificationAgent(BaseAgent):
    """ADK worker that installs and executes the generated app's own verifier."""

    output_root: Path

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        commands = [
            [sys.executable, "-m", "pip", "install", "-q", "-e", ".[dev]"],
            ["bash", "scripts/verify.sh"],
        ]
        results: list[dict[str, object]] = []
        for command in commands:
            completed = subprocess.run(
                command,
                cwd=self.output_root,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
            results.append(
                {
                    "command": command,
                    "exit_code": completed.returncode,
                    "stdout_tail": completed.stdout[-2000:],
                    "stderr_tail": completed.stderr[-2000:],
                }
            )
            if completed.returncode:
                raise RuntimeError(
                    f"Generated-app verification failed: {' '.join(command)}\n"
                    f"{completed.stdout}\n{completed.stderr}"
                )

        yield Event(
            author=self.name,
            content=types.Content(
                role="model", parts=[types.Part(text="verification: generated app PASS")]
            ),
            actions=EventActions(
                state_delta={
                    "stage:verification": {
                        "status": "complete",
                        "agent": self.name,
                        "commands": results,
                    }
                }
            ),
        )


def build_workflow(output_root: Path = DEFAULT_OUTPUT) -> SequentialAgent:
    """Construct the real ADK workflow that creates NyxNight."""
    blueprint = FACTORY_ROOT / "blueprint"
    return SequentialAgent(
        name="nyxnight_creation_workflow",
        description="Create and verify the standalone NyxNight application.",
        sub_agents=[
            ScopedFileAgent(
                name="requirements_agent",
                description="Emit the product contract and repository shell.",
                stage="requirements",
                blueprint_root=blueprint,
                output_root=output_root,
                file_paths=REQUIREMENTS_FILES,
            ),
            ScopedFileAgent(
                name="backend_builder",
                description="Emit the standalone backend, package, CLI, and backend tests.",
                stage="backend",
                blueprint_root=blueprint,
                output_root=output_root,
                file_paths=BACKEND_FILES,
            ),
            ScopedFileAgent(
                name="frontend_builder",
                description="Emit the dependency-free browser UI and UI contract tests.",
                stage="frontend",
                blueprint_root=blueprint,
                output_root=output_root,
                file_paths=FRONTEND_FILES,
            ),
            VerificationAgent(
                name="verification_agent",
                description="Install and verify the generated application.",
                output_root=output_root,
            ),
        ],
    )


root_agent = build_workflow()

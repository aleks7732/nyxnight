# NyxNight Factory

This repository is the **creator**, not the created application.

It defines and runs a genuine Google Agent Development Kit workflow:

1. `requirements_agent` emits the product contract and repository shell.
2. `backend_builder` emits the standalone Python/FastAPI application and backend tests.
3. `frontend_builder` emits the dependency-free true-black/Crail-orange browser UI and UI tests.
4. `verification_agent` installs the generated application and executes its canonical verifier.

The workflow is a real `google.adk.agents.SequentialAgent` executed through `Runner` and `InMemorySessionService`. Its workers are deterministic custom `BaseAgent` implementations, so the build is reproducible and does not require a Gemini key.

The generated NyxNight application has no runtime or package dependency on Google ADK. A snapshot of this factory and a machine-readable run receipt are copied into the generated repository solely as provenance.

Run:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
nyxnight-factory --output /home/maver/NyxNight
```

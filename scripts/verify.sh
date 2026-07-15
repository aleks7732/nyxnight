#!/usr/bin/env bash
set -euo pipefail

printf '%s\n' '[1/8] Python compilation'
python -m compileall -q nyxnight tests
printf '%s\n' '[2/8] Ruff lint and format'
python -m ruff check .
python -m ruff format --check .
printf '%s\n' '[3/8] Strict mypy'
python -m mypy nyxnight
printf '%s\n' '[4/8] Pytest'
python -m pytest -q
printf '%s\n' '[5/8] JavaScript syntax'
node --check nyxnight/web/app.js
printf '%s\n' '[6/8] Dependency health'
python -m pip check
printf '%s\n' '[7/8] Standalone-runtime boundary'
python - <<'PY'
import tomllib
from pathlib import Path
project = tomllib.loads(Path('pyproject.toml').read_text())
deps = project['project']['dependencies']
assert not any('adk' in dep.casefold() for dep in deps), deps
for path in Path('nyxnight').rglob('*.py'):
    assert 'google.adk' not in path.read_text(), path
print('application-adk-runtime-dependency=absent')
PY
printf '%s\n' '[8/8] Wheel build and asset inspection'
rm -rf .verify-dist
python -m build --wheel --outdir .verify-dist >/dev/null
python - <<'PY'
from pathlib import Path
from zipfile import ZipFile
wheels = list(Path('.verify-dist').glob('*.whl'))
assert len(wheels) == 1, wheels
required = {
    'nyxnight/api.py',
    'nyxnight/planner.py',
    'nyxnight/web/index.html',
    'nyxnight/web/styles.css',
    'nyxnight/web/app.js',
}
with ZipFile(wheels[0]) as archive:
    names = set(archive.namelist())
    missing = required - names
    assert not missing, missing
    metadata = next(name for name in names if name.endswith('.dist-info/METADATA'))
    text = archive.read(metadata).decode()
    assert 'google-adk' not in text.casefold()
print(f'wheel={wheels[0]} assets=present adk-dependency=absent')
PY
printf '%s\n' 'NyxNight standalone verifier: PASS'

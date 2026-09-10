import ast
from pathlib import Path
import jinja2

root = Path(__file__).resolve().parents[1]
errors = []
for path in [*root.glob('*.py'), *root.joinpath('app').rglob('*.py'), *root.joinpath('tests').rglob('*.py')]:
    try:
        ast.parse(path.read_text())
    except Exception as exc:
        errors.append(f'PYTHON {path}: {exc}')

env = jinja2.Environment()
for path in root.joinpath('app/templates').rglob('*.html'):
    try:
        env.parse(path.read_text())
    except Exception as exc:
        errors.append(f'JINJA {path}: {exc}')

if errors:
    print('\n'.join(errors))
    raise SystemExit(1)
print('MatchFlow verification passed: Python syntax and Jinja templates are valid.')

import ast
from pathlib import Path

MAX_FUNCTION_LINES = 14
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIRS = [
    'auth_app',
    'profiles_app',
    'offers_app',
    'orders_app',
    'reviews_app',
    'core',
]
EXCLUDED_PARTS = {'migrations', 'tests', '__pycache__'}
EXCLUDED_FILE_PREFIXES = ('test_',)


def iter_source_files():
    for source_dir in SOURCE_DIRS:
        for path in (PROJECT_ROOT / source_dir).rglob('*.py'):
            relative_parts = set(path.relative_to(PROJECT_ROOT).parts)
            if relative_parts & EXCLUDED_PARTS:
                continue
            if path.name.startswith(EXCLUDED_FILE_PREFIXES):
                continue
            yield path


def collect_long_functions(path):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    long_functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            line_count = node.end_lineno - node.lineno + 1
            if line_count > MAX_FUNCTION_LINES:
                long_functions.append((node.name, node.lineno, line_count))
    return long_functions


def test_project_functions_do_not_exceed_max_line_count():
    violations = []
    for path in iter_source_files():
        for name, line_number, line_count in collect_long_functions(path):
            relative_path = path.relative_to(PROJECT_ROOT)
            violations.append(
                f'{relative_path}:{line_number} {name} has {line_count} lines'
            )

    assert not violations, '\n'.join(violations)

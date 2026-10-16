"""Conservative, module-level regression-test selection for Python agents.

Reads source without importing or executing it. Dynamic imports trigger full-suite
fallback. This is a research prototype, not a sound Python program analyser.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path


def select(root, changed):
    root = Path(root).resolve()
    files = sorted(p for p in root.rglob('*.py') if not any(
        part.startswith('.') or part in {'__pycache__', 'node_modules', 'venv'}
        for part in p.relative_to(root).parts))
    sources = {p.relative_to(root).as_posix(): p.read_text(encoding='utf-8') for p in files}
    modules = {name: name[:-3].replace('/', '.').removesuffix('.__init__') for name in sources}
    tests = sorted(n for n in sources if Path(n).name.startswith('test_'))
    changed = {Path(c).as_posix() for c in changed}
    reasons, dependencies = [], {}
    if not changed or not changed <= sources.keys():
        reasons.append('unknown, deleted, non-Python, or empty change set')
    for name, source in sources.items():
        dependencies[name] = set()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            reasons.append('syntax error: ' + name)
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                called = ast.unparse(node.func)
                if called in {'__import__', 'eval', 'exec'} or called.endswith('.import_module'):
                    reasons.append('dynamic execution/import: ' + name)
            if isinstance(node, ast.Import):
                imports = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                package = modules[name].split('.')[:-1]
                if Path(name).name == '__init__.py':
                    package = modules[name].split('.')
                base = ('.'.join(package[:len(package)-node.level+1]) + '.'
                        if node.level else '') + (node.module or '')
                base = base.strip('.')
                imports = [base] + [(base + '.' + a.name).strip('.') for a in node.names]
            else:
                continue
            for other, module in modules.items():
                if any(i == module or i.startswith(module + '.') for i in imports):
                    dependencies[name].add(other)
    impacted = set(changed)
    while True:
        more = {n for n, deps in dependencies.items() if deps & impacted}
        if more <= impacted:
            break
        impacted |= more
    if any(Path(c).name in {'conftest.py', '__init__.py'} for c in changed):
        reasons.append('package initialization or test configuration changed')
    static_selected = sorted(set(tests) & impacted)
    selected = tests if reasons else static_selected
    if not selected:
        reasons.append('no statically connected tests; full suite required')
        selected = tests
    return {'selected': selected, 'static_selected': static_selected,
            'total_tests': len(tests), 'fallback': bool(reasons),
            'reasons': sorted(set(reasons)), 'changed': sorted(changed),
            'source_sha256': {n: hashlib.sha256(s.encode()).hexdigest() for n, s in sources.items()},
            'limitations': 'Static imports only; plugins, reflection and runtime monkeypatching may escape detection.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root')
    parser.add_argument('changed', nargs='+', help='Repository-relative paths')
    args = parser.parse_args()
    print(json.dumps(select(args.root, args.changed), indent=2))

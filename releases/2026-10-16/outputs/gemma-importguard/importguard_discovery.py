"""Development selector with explicit source roots and test-name patterns.

Reads source without importing or executing it. Dynamic imports trigger full-suite
fallback. This is a research prototype, not a sound Python program analyser.
"""
import argparse
import ast
import hashlib
import json
from fnmatch import fnmatchcase
from pathlib import Path


def select(root, changed, source_roots=('.',), test_patterns=('test*.py','*_test.py')):
    root = Path(root).resolve()
    files = sorted(p for p in root.rglob('*.py') if not any(
        part.startswith('.') or part in {'__pycache__', 'node_modules', 'venv'}
        for part in p.relative_to(root).parts))
    sources = {p.relative_to(root).as_posix(): p.read_text(encoding='utf-8') for p in files}
    prefixes=[]
    for value in source_roots:
        path=Path(value)
        if path.is_absolute() or '..' in path.parts or not (root/path).is_dir():
            raise ValueError('Source roots must be existing repository-relative directories')
        prefixes.append(path.parts)
    if not prefixes:raise ValueError('Declare at least one source root')
    modules={}
    for name in sources:
        parts=Path(name).parts
        matching=[prefix for prefix in prefixes if parts[:len(prefix)]==prefix]
        prefix=max(matching,key=len) if matching else ()
        relative=parts[len(prefix):]
        modules[name]='/'.join(relative)[:-3].replace('/','.').removesuffix('.__init__')
    if not test_patterns or not all(isinstance(p,str) and p for p in test_patterns):
        raise ValueError('Declare nonempty test filename patterns')
    tests = sorted(n for n in sources if any(fnmatchcase(Path(n).name,p) for p in test_patterns))
    changed = {Path(c).as_posix() for c in changed}
    reasons, dependencies = [], {}
    collisions={module for module in modules.values() if list(modules.values()).count(module)>1}
    reasons.extend('ambiguous module name across source roots: '+module for module in sorted(collisions))
    if not changed or not changed <= sources.keys():
        reasons.append('unknown, deleted, non-Python, or empty change set')
    for name, source in sources.items():
        dependencies[name] = set()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            reasons.append('syntax error: ' + name)
            continue
        # A conservative name set, deliberately not a scope-sensitive resolver.
        # Track imported and assigned aliases so load = __import__ and
        # from importlib import import_module as load cannot hide uncertainty.
        dynamic_names = {'__import__', 'eval', 'exec'}
        dynamic_names.update(a.asname or a.name for n in ast.walk(tree)
                             if isinstance(n, ast.ImportFrom) and n.module == 'importlib'
                             for a in n.names if a.name == 'import_module')
        while True:
            aliases = set()
            for assignment in ast.walk(tree):
                if isinstance(assignment, (ast.Assign, ast.AnnAssign)):
                    value = assignment.value
                    if (isinstance(value, ast.Name) and value.id in dynamic_names
                            or isinstance(value, ast.Attribute) and value.attr == 'import_module'):
                        targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
                        aliases.update(t.id for t in targets if isinstance(t, ast.Name))
            if aliases <= dynamic_names:
                break
            dynamic_names.update(aliases)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                called = ast.unparse(node.func)
                if called in dynamic_names or called.endswith('.import_module'):
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
            'declared_source_roots':['/'.join(p) or '.' for p in prefixes],
            'test_filename_patterns':list(test_patterns),
            'source_sha256': {n: hashlib.sha256(s.encode()).hexdigest() for n, s in sources.items()},
            'limitations': 'Static imports only; plugins, reflection and runtime monkeypatching may escape detection.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root')
    parser.add_argument('changed', nargs='+', help='Repository-relative paths')
    parser.add_argument('--source-root',action='append',help='Repository-relative import root; repeat for multiple roots')
    parser.add_argument('--test-pattern',action='append',help='Test filename pattern; repeat to override defaults')
    args = parser.parse_args()
    print(json.dumps(select(args.root, args.changed,args.source_root or ['.'],args.test_pattern or ['test*.py','*_test.py']), indent=2))

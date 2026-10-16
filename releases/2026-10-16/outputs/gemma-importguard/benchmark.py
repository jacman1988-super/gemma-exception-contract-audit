"""Execute original, small controlled mutations; never claim Gemma performance."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from importguard import select


def run_suite(root, paths):
    start = time.perf_counter()
    proc = subprocess.run([sys.executable, '-B', '-m', 'unittest', *[p[:-3].replace('/', '.') for p in paths]],
                          cwd=root, capture_output=True, text=True, timeout=20)
    return {'returncode': proc.returncode, 'seconds': time.perf_counter()-start,
            'stdout': proc.stdout, 'stderr': proc.stderr}


def benchmark():
    rows = []
    # Every fixture is generated here, without third-party or competition data.
    for mode in ['direct', 'transitive', 'relative', 'dynamic']:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = {'core.py': 'def fee(n):\n    return n * 2\n',
                      'unrelated.py': 'def label():\n    return "ok"\n',
                      'test_a_unrelated.py': 'import unittest\nimport unrelated\nclass Test(unittest.TestCase):\n def test_label(self): self.assertEqual(unrelated.label(), "ok")\n'}
            if mode == 'direct':
                wrapper = 'from core import fee\n'
            elif mode == 'transitive':
                source['bridge.py'] = 'from core import fee\n'
                wrapper = 'from bridge import fee\n'
            elif mode == 'relative':
                source['pkg/__init__.py'] = ''
                source['pkg/bridge.py'] = 'from . import core\nfee = core.fee\n'
                source['pkg/core.py'] = source.pop('core.py')
                wrapper = 'from pkg.bridge import fee\n'
            else:
                wrapper = 'import importlib\nfee = importlib.import_module("core").fee\n'
            source['test_z_fee.py'] = 'import unittest\n' + wrapper + 'class Test(unittest.TestCase):\n def test_fee(self): self.assertEqual(fee(3), 6)\n'
            for name, text in source.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding='utf-8')
            all_tests = ['test_a_unrelated.py', 'test_z_fee.py']
            clean = run_suite(root, all_tests)
            assert clean['returncode'] == 0, clean
            changed = 'pkg/core.py' if mode == 'relative' else 'core.py'
            (root / changed).write_text('def fee(n):\n    return n * 3\n', encoding='utf-8')
            choice = select(root, [changed])
            runs = {method: run_suite(root, paths) for method, paths in {
                'full': all_tests, 'prefix_budget_1': all_tests[:1], 'importguard': choice['selected']}.items()}
            rows.append({'fixture': mode, 'selection': choice, 'runs': runs})
    return {'kind': 'controlled_synthetic_fixture_experiment', 'model_used': None,
            'python': sys.version, 'benchmark_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'cases': rows, 'caveat': 'Four constructed cases; no real-repository or model capability evidence.'}


if __name__ == '__main__':
    result = benchmark()
    target = Path('results/smoke-benchmark.json')
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(target, 'cases:', len(result['cases']))

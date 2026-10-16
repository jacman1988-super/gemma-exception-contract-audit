"""Record two local Gemma patch suggestions. Generated text is never executed.

These known public fixes are a convenience diagnostic, not a contamination-free
benchmark. The model sees task descriptions and buggy snippets, not gold diffs
or fixed-version tests. Source/licensing records live in real-bugs-pilot/.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

MODEL_SHA256='fa401b55b07ee70a54c6dae3903c783a6e65064312529ea57175cb5f8dec6634'
MODEL_REVISION='675cff42a74c774d6cb76f76d8eacb49b48c9b93'
TASKS=[{'id':'boltons-indexedset','file':'boltons/setutils.py',
 'description':'IndexedSet.update accepts several iterables. Add their elements in order, not the iterables themselves. Preserve the zero-argument and one-argument behavior.',
 'anchor':'    def update(self, *others):','lines':10},
 {'id':'more-itertools-bucket','file':'more_itertools/more.py',
 'description':'bucket must honor a supplied validator even when that callable is falsey, for example an empty set subclass with __call__. Only the absence of a validator should select the default.',
 'anchor':'    def __init__(self, iterable, key, validator=None):','lines':8}]

def run(executable,model,data,out):
    out.mkdir(parents=True,exist_ok=True)
    if hashlib.file_digest(model.open('rb'),'sha256').hexdigest()!=MODEL_SHA256:
        raise ValueError('Unexpected model bytes')
    version=subprocess.run([str(executable),'--version'],capture_output=True,text=True)
    tasks=[]
    for task in TASKS:
        root=next((data/(task['id']+'-buggy')).iterdir())
        source=(root/task['file']).read_text(encoding='utf-8')
        start=source.index(task['anchor'])
        snippet='\n'.join(source[start:].splitlines()[:task['lines']])
        prompt=('You are reviewing a Python bug. Suggest the smallest source edit. '
                'Return only JSON with string fields old and new containing one exact '
                'old line and its replacement. Do not run commands.\n\nTask: '+task['description']+
                '\nFile: '+task['file']+'\nBuggy source:\n'+snippet)
        tasks.append({**task,'prompt':prompt,'buggy_file_sha256':hashlib.sha256((root/task['file']).read_bytes()).hexdigest()})
    protocol={'model':'google/gemma-4-E2B-it-qat-q4_0-gguf','revision':MODEL_REVISION,
       'model_sha256':MODEL_SHA256,'runtime_version':version.stdout+version.stderr,
       'runtime_executable_sha256':hashlib.file_digest(executable.open('rb'),'sha256').hexdigest(),
       'context_tokens':2048,'max_generated_tokens':192,'temperature':0,'seed':20261014,
       'threads':2,'batch':64,'reasoning':'off','hardware':platform.platform(),
       'python':sys.version,'tasks':tasks,'automatic_execution_of_output':False,
       'scope':'Two known public bug snippets, no tools or feedback loop; not a full coding-agent benchmark or held-out model capability estimate.'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2))
    results=[]
    for task in tasks:
        prompt_file=out/(task['id']+'.prompt.txt');prompt_file.write_text(task['prompt'])
        command=[str(executable),'-m',str(model),'-f',str(prompt_file),'-c','2048','-n','192',
             '-t','2','-b','64','-ub','64','-ngl','0','--temp','0','--seed','20261014',
             '--reasoning','off','--single-turn','--simple-io','--no-display-prompt',
             '--color','off','--no-warmup','--perf']
        print('Local Gemma:',task['id'],flush=True);start=time.perf_counter()
        try:
            p=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300)
            record={'id':task['id'],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'timed_out':False}
        except subprocess.TimeoutExpired as e:
            decode=lambda x:x.decode('utf-8',errors='replace') if isinstance(x,bytes) else (x or '')
            record={'id':task['id'],'returncode':None,'stdout':decode(e.stdout),'stderr':decode(e.stderr),'timed_out':True}
        record['seconds']=time.perf_counter()-start
        results.append(record)
        (out/(task['id']+'.output.txt')).write_text(record['stdout'],encoding='utf-8')
        (out/(task['id']+'.runtime.txt')).write_text(record['stderr'],encoding='utf-8')
        (out/'results.json').write_text(json.dumps({'results':results,'applied':False,'submitted':False},indent=2))
        print(task['id'],'exit',record['returncode'],'seconds',round(record['seconds'],1),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('executable',type=Path)
    p.add_argument('model',type=Path);p.add_argument('data',type=Path)
    p.add_argument('--output',type=Path,default=Path('results/local-model-pilot'))
    a=p.parse_args();run(a.executable.resolve(),a.model.resolve(),a.data.resolve(),a.output.resolve())

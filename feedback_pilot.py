"""One predeclared retry of the failed upstream pilot, with a no-feedback arm.

Writes model text only. No output is executed by this script. Both arms start
from the same first model edit; this is an inspected development case.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time
from local_model_pilot import MODEL_SHA256,MODEL_REVISION,TASKS

def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()

def run(executable,model,data,previous,out):
    out.mkdir(parents=True,exist_ok=True)
    assert sha(model)==MODEL_SHA256
    first=json.loads((previous/'reviewed-patch-evaluation.json').read_text())['cases'][0]
    assert first['id']=='boltons-indexedset' and first['test_result']['returncode']==1
    task=TASKS[0];root=next((data/'boltons-indexedset-buggy').iterdir())
    source=(root/task['file']).read_text(encoding='utf-8')
    assert source.count(first['suggestion']['old'])==1
    current=source.replace(first['suggestion']['old'],first['suggestion']['new'])
    start=current.index(task['anchor']);snippet='\n'.join(current[start:].splitlines()[:task['lines']])
    common=('You are reviewing a Python patch. You get one revision opportunity. '
        'Return only JSON with string fields old and new containing an exact '
        'source block and its replacement. Do not run commands.\nTask: '+task['description']+
        '\nCurrent source after your previous edit:\n'+snippet)
    feedback=first['test_result']['stdout'][:2000]
    prompts={'no_feedback':common+'\nReview your previous edit once more. No test feedback is provided.',
             'test_feedback':common+'\nThe current edit was tested. Here is the first 2000 characters of the actual test output:\n'+feedback+'\nRevise the current code to address the failures.'}
    protocol={'model_revision':MODEL_REVISION,'model_sha256':MODEL_SHA256,
       'runtime_executable_sha256':sha(executable),'platform':platform.platform(),
       'parent_result_sha256':sha(previous/'reviewed-patch-evaluation.json'),
       'previous_output_sha256':sha(previous/'boltons-indexedset.output.txt'),
       'current_file_sha256':hashlib.sha256(current.encode()).hexdigest(),
       'arms':list(prompts),'prompts':prompts,'feedback_rule':'First 2000 characters, unchanged',
       'max_additional_generations_per_arm':1,'temperature':0,'seed':20261014,
       'max_generated_tokens':192,'context_tokens':2048,'threads':2,
       'generation_timeout_seconds':90,'automatic_execution':False,
       'scope':'One known failed public case, inspected before protocol. Not a held-out assessment or matched input-token budget; both arms have the same output-token cap.'}
    protocol_path=out/'protocol.json'
    if protocol_path.exists():raise FileExistsError('Preserve prior protocol; use a fresh output directory')
    protocol_path.write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    records=[]
    for arm,prompt in prompts.items():
        prompt_file=out/(arm+'.prompt.txt');prompt_file.write_text(prompt,encoding='utf-8')
        command=[str(executable),'-m',str(model),'-f',str(prompt_file),'-c','2048','-n','192',
             '-t','2','-b','64','-ub','64','-ngl','0','--temp','0','--seed','20261014',
             '--reasoning','off','--single-turn','--simple-io','--no-display-prompt',
             '--color','off','--no-warmup','--perf']
        start=time.perf_counter();print('Retry arm:',arm,flush=True)
        try:
            p=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
            row={'arm':arm,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'timed_out':False}
        except subprocess.TimeoutExpired as e:
            decode=lambda x:x.decode('utf-8',errors='replace') if isinstance(x,bytes) else (x or '')
            row={'arm':arm,'returncode':None,'stdout':decode(e.stdout),'stderr':decode(e.stderr),'timed_out':True}
        row['seconds']=time.perf_counter()-start;records.append(row)
        (out/(arm+'.output.txt')).write_text(row['stdout'],encoding='utf-8')
        (out/(arm+'.runtime.txt')).write_text(row['stderr'],encoding='utf-8')
        (out/'results.json').write_text(json.dumps({'results':records,'applied':False},indent=2))
        print(arm,'exit',row['returncode'],round(row['seconds'],1),'seconds',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['executable','model','data','previous','output']:p.add_argument(name,type=Path)
    a=p.parse_args();run(*(getattr(a,n).resolve() for n in ['executable','model','data','previous','output']))

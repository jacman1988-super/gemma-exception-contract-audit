"""One frozen Gemma generation per reproduced expansion case; text only."""
import argparse,ast,hashlib,json
from pathlib import Path
import re,subprocess,time
from local_model_pilot import MODEL_SHA256,MODEL_REVISION

def changed_old_lines(patch):
    points=[];line=0
    for text in patch.splitlines():
        if text.startswith('@@'):
            line=int(re.search(r'@@ -(\d+)',text).group(1))
        elif text.startswith('-'):points.append(line);line+=1
        elif text.startswith(' '):line+=1
    return points

def prepare(data,evaluation,out,executable,model):
    out.mkdir(parents=True,exist_ok=True)
    assert hashlib.file_digest(model.open('rb'),'sha256').hexdigest()==MODEL_SHA256
    protocol=json.loads((evaluation/'protocol.json').read_text(encoding='utf-8'))
    results=json.loads((evaluation/'results.json').read_text())
    eligible={c['id'] for c in results['cases'] if c['status']=='reproduced'}
    tasks=[]
    for case in protocol['cases']:
        if case['id'] not in eligible:continue
        meta=json.loads((data/(case['id']+'.json')).read_text(encoding='utf-8-sig'))
        buggy=next((data/(case['id']+'-buggy')).iterdir());segments=[]
        for name in case['changed']:
            source=(buggy/name).read_text(encoding='utf-8');lines=source.splitlines()
            patch=next(f['patch'] for f in meta['files'] if f['filename']==name)
            points=changed_old_lines(patch);tree=ast.parse(source);chosen={}
            functions=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
            for point in points:
                covering=[n for n in functions if n.lineno<=point<=n.end_lineno]
                if covering:
                    n=min(covering,key=lambda n:n.end_lineno-n.lineno)
                    chosen[(n.lineno,n.end_lineno)]='\n'.join(lines[n.lineno-1:n.end_lineno])
                else:
                    start=max(0,point-8);end=min(len(lines),point+8)
                    chosen[(start+1,end)]='\n'.join(lines[start:end])
            segments.append('File: '+name+'\n'+'\n\n'.join(chosen[k] for k in sorted(chosen)))
        snippet='\n\n'.join(segments)[:6000]
        prompt=('Fix a Python bug. Return only JSON with string fields old and new for an exact source block and its replacement. '
            'Make the smallest edit, preserve unrelated behavior, and do not run commands.\n'
            'Task description (public commit message):\n'+case['description']+'\nBuggy source:\n'+snippet)
        tasks.append({'id':case['id'],'prompt':prompt,'source_snippet':snippet,
                      'localization':'Removed-line coordinates identify buggy functions. No added patch lines or test source supplied.'})
    p=out/'protocol.json'
    if p.exists():raise FileExistsError('Keep prior run; choose a fresh directory')
    record={'model_revision':MODEL_REVISION,'model_sha256':MODEL_SHA256,
        'runtime_executable_sha256':hashlib.file_digest(executable.open('rb'),'sha256').hexdigest(),
        'selection_protocol_sha256':hashlib.sha256((evaluation/'protocol.json').read_bytes()).hexdigest(),
        'tasks':tasks,'excluded':[{c['id']:c['status']} for c in results['cases'] if c['id'] not in eligible],
        'context_tokens':2048,'max_generated_tokens':192,'temperature':0,'seed':20261014,
        'threads':2,'attempts_per_case':1,'reasoning':'off','timeout_seconds':90,
        'automatic_execution':False,'gold_diff_supplied':False,
        'limitations':'Oracle localization and commit-message guidance. Public descriptions may explain the fix; not autonomous issue solving or contamination-free tasks.'}
    p.write_text(json.dumps(record,indent=2),encoding='utf-8')
    return record

def run(data,evaluation,out,executable,model):
    protocol=prepare(data,evaluation,out,executable,model);records=[]
    for task in protocol['tasks']:
        f=out/(task['id']+'.prompt.txt');f.write_text(task['prompt'],encoding='utf-8')
        command=[str(executable),'-m',str(model),'-f',str(f),'-c','2048','-n','192','-t','2',
          '-b','64','-ub','64','-ngl','0','--temp','0','--seed','20261014','--reasoning','off',
          '--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--perf']
        print('Gemma expansion:',task['id'],flush=True);start=time.perf_counter()
        try:
            p=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
            row={'id':task['id'],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'timed_out':False}
        except subprocess.TimeoutExpired as e:
            dec=lambda x:x.decode('utf-8',errors='replace') if isinstance(x,bytes) else x or ''
            row={'id':task['id'],'returncode':None,'stdout':dec(e.stdout),'stderr':dec(e.stderr),'timed_out':True}
        row['seconds']=time.perf_counter()-start;records.append(row)
        (out/(task['id']+'.output.txt')).write_text(row['stdout'],encoding='utf-8')
        (out/'results.json').write_text(json.dumps({'results':records,'applied':False},indent=2))
        print(task['id'],'exit',row['returncode'],round(row['seconds'],1),'seconds',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['data','evaluation','output','executable','model']:p.add_argument(n,type=Path)
    a=p.parse_args();run(*(getattr(a,n).resolve() for n in ['data','evaluation','output','executable','model']))

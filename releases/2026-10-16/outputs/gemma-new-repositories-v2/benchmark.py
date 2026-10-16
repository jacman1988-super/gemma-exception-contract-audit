"""Pinned upstream reference and parent runs, followed by one text-only generation."""
import sys,os,json,shutil,hashlib,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DATA=ROOT/'work/new-upstream-v2'
sys.path.insert(0,str(HERE.parent/'gemma-importguard'))
from expansion_model import changed_old_lines
from local_model_pilot import MODEL_SHA256,MODEL_REVISION
import ast
def write(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def execute(root,case,label):
    env=os.environ.copy();env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';env['PYTHONDONTWRITEBYTECODE']='1'
    env['PYTHONPATH']=os.pathsep.join([str(root/case['source_root']),str(root),env.get('PYTHONPATH','')])
    report=HERE/(case['id']+'-'+label+'.xml')
    start=time.perf_counter()
    try:
        p=subprocess.run([sys.executable,'-B','-m','pytest','-o','addopts=','-q','--tb=short','--junitxml='+str(report),*case['pool']],cwd=root,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
        result={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'seconds':time.perf_counter()-start,'report':str(report)}
    except subprocess.TimeoutExpired:result={'returncode':None,'timeout':True,'seconds':time.perf_counter()-start}
    write(HERE/(case['id']+'-'+label+'.json'),result);return result
def prepare():
    cases=json.loads((DATA/'cases.json').read_text())['cases']
    protocol={'cases':cases,'selection':'First most recent first-parent fix/handle/catch source change with modified source and changed test module; no replacements after outcomes.',
        'max_tokens':512,'context':4096,'seed':20261016,'attempts':1,'temperature':0,'reasoning':'off',
        'limitations':'Oracle localization using removed-line coordinates; public commit description provided. Not autonomous navigation or contamination-free evaluation.',
        'model_revision':MODEL_REVISION,'model_sha256':MODEL_SHA256,'source_sha256':sha(Path(__file__)),'no_external_writes':True}
    if (HERE/'protocol.json').exists():raise FileExistsError('Preserve existing run')
    write(HERE/'protocol.json',protocol);results=[]
    for c in cases:
        fixed=next((DATA/(c['id']+'-fixed')).iterdir());buggy=next((DATA/(c['id']+'-buggy')).iterdir())
        root=ROOT/'work'/(c['id']+'-evaluation');shutil.copytree(fixed,root)
        (HERE/(c['id']+'-LICENSE.txt')).write_text(c['license_text'],encoding='utf-8')
        ref=execute(root,c,'reference')
        for n in c['changed']:shutil.copy2(buggy/n,root/n)
        parent=execute(root,c,'parent')
        results.append({'id':c['id'],'reference':ref,'parent':parent,'root':str(root),'reproduced':ref['returncode']==0 and parent['returncode']==1 and 'ERROR collecting' not in parent.get('stdout','')})
        write(HERE/'reference-results.json',results);print(c['id'],ref['returncode'],parent['returncode'],flush=True)
def generate():
    protocol=json.loads((HERE/'protocol.json').read_text());results=json.loads((HERE/'reference-results.json').read_text());tasks=[]
    for c in protocol['cases']:
        if not next(x for x in results if x['id']==c['id'])['reproduced']:continue
        meta=json.loads((DATA/(c['id']+'.json')).read_text());buggy=next((DATA/(c['id']+'-buggy')).iterdir());segments=[]
        for name in c['changed']:
            source=(buggy/name).read_text(encoding='utf-8');lines=source.splitlines();tree=ast.parse(source);chosen={}
            patch=next(f['patch'] for f in meta['files'] if f['filename']==name)
            for point in changed_old_lines(patch):
                nodes=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.lineno<=point<=n.end_lineno]
                if nodes:
                    n=min(nodes,key=lambda n:n.end_lineno-n.lineno);chosen[(n.lineno,n.end_lineno)]='\n'.join(lines[n.lineno-1:n.end_lineno])
                else:chosen[(max(0,point-8),point+8)]='\n'.join(lines[max(0,point-8):point+8])
            segments.append('File: '+name+'\n'+'\n\n'.join(chosen[k] for k in sorted(chosen)))
        prompt='Fix a Python bug. Return only JSON with string fields old and new for an exact source block and its replacement. Make the smallest edit, preserve unrelated behavior, and do not run commands.\nTask description (public commit message):\n'+meta['commit']['message']+'\nBuggy source:\n'+'\n\n'.join(segments)[:6000]
        path=HERE/(c['id']+'.prompt.txt');path.write_text(prompt,encoding='utf-8');tasks.append({'id':c['id'],'prompt_sha256':sha(path),'prompt':prompt})
    write(HERE/'generation-protocol.json',{'tasks':tasks,'protocol_sha256':sha(HERE/'protocol.json')})
    model=ROOT/'work/gemma-runtime/gemma-4-E2B_q4_0-it.gguf';exe=ROOT/'work/gemma-runtime/llama/llama-cli.exe'
    assert sha(model)==MODEL_SHA256
    for task in tasks:
        command=[str(exe),'-m',str(model),'-f',str(HERE/(task['id']+'.prompt.txt')),'-c','4096','-n','512','-t','2','-b','64','-ub','64','-ngl','0','--temp','0','--seed','20261016','--reasoning','off','--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--perf']
        start=time.perf_counter();print('Generating',task['id'],flush=True)
        try:
            p=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
            row={'id':task['id'],'stdout':p.stdout,'stderr':p.stderr,'returncode':p.returncode,'timeout':False}
        except subprocess.TimeoutExpired as e:
            dec=lambda v:v.decode('utf-8',errors='replace') if isinstance(v,bytes) else v or ''
            row={'id':task['id'],'stdout':dec(e.stdout),'stderr':dec(e.stderr),'returncode':None,'timeout':True}
        row['seconds']=time.perf_counter()-start;write(HERE/(task['id']+'-generation.json'),row)
        print('Generated',task['id'],row['returncode'],row['seconds'],flush=True)
if __name__=='__main__':
    {'prepare':prepare,'generate':generate}[sys.argv[1]]()

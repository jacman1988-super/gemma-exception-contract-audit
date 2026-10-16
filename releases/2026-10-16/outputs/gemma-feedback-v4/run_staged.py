"""Two-stage diagnosis and literal Python functions; clean parent sources."""
import sys,ast,json,subprocess,time
from pathlib import Path
H=Path(__file__).resolve().parent;OLD=H.parent/'gemma-new-repositories-v2'
sys.path.insert(0,str(OLD));import benchmark as b
def generate(ident,stage,prompt,limit):
    path=H/(ident+'-'+stage+'.prompt.txt');path.write_text(prompt,encoding='utf-8')
    exe=b.ROOT/'work/gemma-runtime/llama/llama-cli.exe';model=b.ROOT/'work/gemma-runtime/gemma-4-E2B_q4_0-it.gguf'
    cmd=[str(exe),'-m',str(model),'-f',str(path),'-c','4096','-n',str(limit),'-t','2','-b','64','-ub','64','-ngl','0','--temp','0','--seed','20261016','--reasoning','off','--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--perf']
    start=time.perf_counter()
    try:
        p=subprocess.run(cmd,stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180);row={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'timeout':False}
    except subprocess.TimeoutExpired as x:
        dec=lambda v:v.decode('utf-8',errors='replace') if isinstance(v,bytes) else v or ''
        row={'returncode':None,'stdout':dec(x.stdout),'stderr':dec(x.stderr),'timeout':True}
    row.update(seconds=time.perf_counter()-start,prompt_sha256=b.sha(path));b.write(H/(ident+'-'+stage+'.json'),row);print(ident,stage,row['returncode'],row['seconds'],flush=True)
    return row
def answer(text):
    return text.split(' ... (truncated)\n',1)[-1].split('\n\n[ Prompt:',1)[0].strip()
def main():
    cases=json.loads((OLD/'protocol.json').read_text())['cases'];tasks=[]
    for c in cases:
        parent=next((b.DATA/(c['id']+'-buggy')).iterdir());snippets=[]
        for name in c['changed']:
            source=(parent/name).read_text(encoding='utf-8');lines=source.splitlines();nodes=[n for n in ast.walk(ast.parse(source)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in ['_run_wait','is_valid_pylock_path']]
            text='\n'.join('\n'.join(lines[n.lineno-1:n.end_lineno]) for n in nodes)
            if c['package']=='packaging':text=next(line for line in lines if line.startswith('_PYLOCK_FILE_NAME_RE ='))+'\n\n'+text
            snippets.append('FILE: '+name+'\n'+text)
        examples=('Case | expected upcoming_sleep\nwait=None | 0\nwait=0 | 0\nfalsey callable returning 1.25 | 1.25\nempty list subclass callable returning .75 | .75\nBoth synchronous and asynchronous paths must honor these examples.' if c['package']=='tenacity' else 'filename represented with Python repr | expected\n"pylock.toml" | True\n"pylock.spam.toml" | True\n"pylock.prod.toml" | True\n"pylock.spam.toml\\n" (final character U+000A) | False\n"pylock.prod.toml.backup" | False\nMatch the entire unmodified filename; do not normalize away invalid suffixes.')
        tasks.append({'id':c['id'],'snippets':'\n\n'.join(snippets),'examples':examples})
    protocol={'tasks':tasks,'stages':['diagnose without code','repair using literal Python functions'],'diagnosis_tokens':256,'repair_tokens':768,'attempts_per_stage':1,'seed':20261016,'temperature':0,'context':4096,'model_sha256':b.MODEL_SHA256,'source_sha256':b.sha(Path(__file__)),'change':'Start from pinned clean buggy parent, include relevant regex definition, use case table and separate diagnosis; literal Python output avoids JSON escapes. Not directly comparable to previous failed-patch feedback rounds.','gold_source_supplied':False,'withheld_tests_shared':False}
    if (H/'protocol.json').exists():raise FileExistsError('Preserve run')
    b.write(H/'protocol.json',protocol);assert b.sha(b.ROOT/'work/gemma-runtime/gemma-4-E2B_q4_0-it.gguf')==b.MODEL_SHA256
    for task in tasks:
        context='Observed behavior requirements:\n'+task['examples']+'\nCurrent buggy source:\n'+task['snippets']
        diagnosis=generate(task['id'],'diagnosis','Explain the cause of these failing Python cases in at most 100 words. State the behavioral rule needed. Do not provide replacement code.\n'+context,256)
        if diagnosis['timeout'] or diagnosis['returncode']!=0:continue
        prompt='Repair the functions below. Return ONLY one FILE: relative/path.py header per file followed by a fenced python block containing the COMPLETE replacement function, preserving its name, signature and indentation. No JSON, no diff, no extra functions or commands.\n'+context+'\nYour diagnosis:\n'+answer(diagnosis['stdout'])
        generate(task['id'],'repair',prompt,768)
if __name__=='__main__':main()

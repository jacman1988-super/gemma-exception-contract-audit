"""Packaging follow-up: concrete execution counterexamples plus local stdlib API docs."""
import sys,json,re,subprocess,time
from pathlib import Path
H=Path(__file__).resolve().parent;OUT=H/'api-feedback';OUT.mkdir(exist_ok=True);OLD=H.parent/'gemma-new-repositories-v2'
sys.path.insert(0,str(OLD));import benchmark as b
def main():
    review=next(r for r in json.loads((H/'reviewed-functions.json').read_text()) if r['id']=='packaging-new-v2');source=review['edits'][0]['literal_function']
    case=next(c for c in json.loads((OLD/'protocol.json').read_text())['cases'] if c['package']=='packaging');parent=next((b.DATA/(case['id']+'-buggy')).iterdir());constant=next(line for line in (parent/case['changed'][0]).read_text(encoding='utf-8').splitlines() if line.startswith('_PYLOCK_FILE_NAME_RE ='))
    docs={'Pattern.match':re.Pattern.match.__doc__,'Pattern.fullmatch':re.Pattern.fullmatch.__doc__,'Pattern.search':re.Pattern.search.__doc__}
    prompt='Repair your current Python function after these EXECUTED counterexamples. Return ONLY a fenced python block containing the complete is_valid_pylock_path function with the same signature. Do not change imports or regex constant. Do not strip or normalize input.\nCurrent context:\n'+constant+'\n'+source+'\nExecuted counterexamples:\nfilename repr | your actual result | required\n"pylock.toml" | False | True\n"pylock.spam.toml" | True | True\n"pylock.prod.toml" | True | True\n"pylock.spam.toml\\n" (final U+000A) | True | False\n"pylock.prod.toml.backup" | False | False\nLocal Python API reference (available methods, not a gold patch):\n'+json.dumps(docs)+'\nSatisfy every example simultaneously. Return only the function, no explanation.'
    (OUT/'prompt.txt').write_text(prompt,encoding='utf-8');protocol={'case':case['id'],'method':'Execution counterexample table + local Python regex API reference','api_docs':docs,'source_prompt_sha256':b.sha(OUT/'prompt.txt'),'previous_generation_sha256':b.sha(H/'packaging-new-v2-repair.json'),'attempts':1,'context':4096,'tokens':512,'seed':20261016,'temperature':0,'reference_assistance':'Explicit fullmatch API documentation supplied among match/search methods; stronger assistance, not comparable with unassisted stages. No upstream gold code.','source_sha256':b.sha(Path(__file__))}
    if (OUT/'protocol.json').exists():raise FileExistsError('Preserve run')
    b.write(OUT/'protocol.json',protocol);exe=b.ROOT/'work/gemma-runtime/llama/llama-cli.exe';model=b.ROOT/'work/gemma-runtime/gemma-4-E2B_q4_0-it.gguf';assert b.sha(model)==b.MODEL_SHA256
    cmd=[str(exe),'-m',str(model),'-f',str(OUT/'prompt.txt'),'-c','4096','-n','512','-t','2','-b','64','-ub','64','-ngl','0','--temp','0','--seed','20261016','--reasoning','off','--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--perf'];start=time.perf_counter()
    try:
        p=subprocess.run(cmd,stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180);row={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'timeout':False}
    except subprocess.TimeoutExpired as x:
        dec=lambda v:v.decode('utf-8',errors='replace') if isinstance(v,bytes) else v or ''
        row={'returncode':None,'stdout':dec(x.stdout),'stderr':dec(x.stderr),'timeout':True}
    row['seconds']=time.perf_counter()-start;b.write(OUT/'generation.json',row);print(row,flush=True)
if __name__=='__main__':main()

"""Second and final feedback round: concise, cumulative failures, no gold code."""
import sys,json,ast,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'gemma-new-repositories-v2';OUT=HERE/'round2';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(OLD));import benchmark as b
def main():
    cases=json.loads((OLD/'protocol.json').read_text())['cases'];previous=json.loads((OLD/'edit-review.json').read_text());reviews=json.loads((HERE/'reviewed-edits.json').read_text());tasks=[]
    for case in cases:
        ident=case['id'];parent=next((b.DATA/(ident+'-buggy')).iterdir());sources={n:(parent/n).read_text(encoding='utf-8') for n in case['changed']}
        patch=next(x for x in previous if x['id']==ident)['patch'];name=next(n for n,s in sources.items() if s.count(patch['old'])==1);sources[name]=sources[name].replace(patch['old'],patch['new'],1)
        review=next(x for x in reviews if x['id']==ident)
        if review.get('approved'):
            for edit in review['edits']:sources[edit['file']]=sources[edit['file']].replace(edit['old'],edit['new'],1)
        snippets=[]
        for name,source in sources.items():
            lines=source.splitlines();nodes=[n for n in ast.walk(ast.parse(source)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in ['_run_wait','is_valid_pylock_path']]
            snippets.append('File: '+name+'\n'+'\n'.join('\n'.join(lines[n.lineno-1:n.end_lineno]) for n in nodes))
        facts=('Previous feedback response was invalid, incomplete JSON with repeated keys and was not applied. Current code still skips falsey callable wait strategies. Both sync and async must call these strategies. A falsey callable returning 1.25 must yield upcoming_sleep 1.25, and an empty list subclass returning .75 must yield .75. None and numeric zero must still mean zero wait. Do not change other behavior.' if case['package']=='tenacity' else 'Previous feedback merely restored the original buggy function. Current code wrongly accepts filename "pylock.spam.toml\\n"; expected False. It must reject trailing newlines and suffix garbage while still accepting "pylock.toml", "pylock.spam.toml", and "pylock.prod.toml". Do not solve the newline case by rejecting legitimate named lockfiles.')
        prompt='Repair the current Python source using this cumulative test feedback. Return ONLY complete JSON {"edits":[{"file":"relative/path.py","old":"exact block","new":"replacement"}]}. Keep edits concise; do not repeat keys. No commands.\nFeedback:\n'+facts+'\nCurrent source:\n'+'\n\n'.join(snippets)
        path=OUT/(ident+'.prompt.txt');path.write_text(prompt,encoding='utf-8');tasks.append({'id':ident,'prompt_sha256':b.sha(path),'current_source_sha256':{n:__import__('hashlib').sha256(s.encode()).hexdigest() for n,s in sources.items()}})
    protocol={'tasks':tasks,'feedback_round':2,'attempts_per_case':1,'max_tokens':512,'context':4096,'seed':20261016,'temperature':0,'timeout_seconds':180,'feedback':'Concise cumulative original failure plus regressions; malformed-response feedback. No gold source or patches. Existing withheld tests remain withheld.','source_sha256':b.sha(Path(__file__))}
    if (OUT/'protocol.json').exists():raise FileExistsError('Preserve run')
    b.write(OUT/'protocol.json',protocol);exe=b.ROOT/'work/gemma-runtime/llama/llama-cli.exe';model=b.ROOT/'work/gemma-runtime/gemma-4-E2B_q4_0-it.gguf';assert b.sha(model)==b.MODEL_SHA256
    for task in tasks:
        cmd=[str(exe),'-m',str(model),'-f',str(OUT/(task['id']+'.prompt.txt')),'-c','4096','-n','512','-t','2','-b','64','-ub','64','-ngl','0','--temp','0','--seed','20261016','--reasoning','off','--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--perf'];start=time.perf_counter();print('Round2',task['id'],flush=True)
        try:
            p=subprocess.run(cmd,stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180);row={'id':task['id'],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'timeout':False}
        except subprocess.TimeoutExpired as x:
            dec=lambda v:v.decode('utf-8',errors='replace') if isinstance(v,bytes) else v or ''
            row={'id':task['id'],'returncode':None,'stdout':dec(x.stdout),'stderr':dec(x.stderr),'timeout':True}
        row['seconds']=time.perf_counter()-start;b.write(OUT/(task['id']+'-generation.json'),row);print('Finished',task['id'],row['returncode'],row['seconds'],flush=True)
if __name__=='__main__':main()

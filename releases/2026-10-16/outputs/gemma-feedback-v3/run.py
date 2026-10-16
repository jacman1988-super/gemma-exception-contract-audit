"""One feedback-conditioned generation per previously failed upstream task."""
import sys,json,subprocess,time,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'gemma-new-repositories-v2';ROOT=HERE.parents[1]
sys.path.insert(0,str(OLD));import benchmark as b
def main():
    tasks=json.loads((OLD/'generation-protocol.json').read_text())['tasks'];reviews=json.loads((OLD/'edit-review.json').read_text());prompts=[]
    for task in tasks:
        ident=task['id'];previous=next(x for x in reviews if x['id']==ident)['patch']
        prompt=task['prompt'].split('Task description (public commit message):',1)[1].replace(previous['old'],previous['new'])
        failures='\n'.join(json.loads((OLD/(ident+'-model-'+kind+'-checked.json')).read_text())['stdout'] for kind in ['full','contract'])
        prompt='Repair your previous unsuccessful edit. The source below already includes that edit. Preserve all valid behavior. Return only JSON {"edits":[{"file":"relative/path.py","old":"exact block","new":"replacement"}]}. Multiple files are allowed; every old block must match exactly once in its file. Do not run commands.\nTask description:'+prompt+'\nObserved test failures from your previous patch:\n'+failures+'\nReturn only the JSON edits, relative to the CURRENT source above. Fix both synchronous and asynchronous behavior if applicable. Preserve legitimate named pylock files if applicable.'
        (HERE/(ident+'.prompt.txt')).write_text(prompt,encoding='utf-8');prompts.append({'id':ident,'prompt_sha256':b.sha(HERE/(ident+'.prompt.txt')),'previous_patch':previous})
    protocol={'tasks':prompts,'attempts_per_case':1,'feedback':'Exact failed-test output from previous model full module and extra controls. No upstream fixed source or gold patch supplied.','max_tokens':1536,'context':4096,'seed':20261016,'temperature':0,'timeout':240,'model_sha256':b.MODEL_SHA256,'source_sha256':b.sha(Path(__file__)),'limitations':'Known public tasks with oracle localization and now test feedback; no independent evaluation claim.'}
    if (HERE/'protocol.json').exists():raise FileExistsError('Preserve prior run')
    b.write(HERE/'protocol.json',protocol);exe=ROOT/'work/gemma-runtime/llama/llama-cli.exe';model=ROOT/'work/gemma-runtime/gemma-4-E2B_q4_0-it.gguf';assert b.sha(model)==b.MODEL_SHA256
    for task in prompts:
        cmd=[str(exe),'-m',str(model),'-f',str(HERE/(task['id']+'.prompt.txt')),'-c','4096','-n','1536','-t','2','-b','64','-ub','64','-ngl','0','--temp','0','--seed','20261016','--reasoning','off','--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--perf']
        start=time.perf_counter();print('Feedback generation',task['id'],flush=True)
        try:
            p=subprocess.run(cmd,stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240);row={'id':task['id'],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'timeout':False}
        except subprocess.TimeoutExpired as x:
            dec=lambda v:v.decode('utf-8',errors='replace') if isinstance(v,bytes) else v or ''
            row={'id':task['id'],'returncode':None,'stdout':dec(x.stdout),'stderr':dec(x.stderr),'timeout':True}
        row['seconds']=time.perf_counter()-start;b.write(HERE/(task['id']+'-generation.json'),row);print('Finished',task['id'],row['returncode'],row['seconds'],flush=True)
if __name__=='__main__':main()

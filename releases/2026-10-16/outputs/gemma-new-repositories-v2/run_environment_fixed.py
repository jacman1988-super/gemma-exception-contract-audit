"""Environment-only repeat after neutral inference fails in sandbox and works outside."""
import benchmark as b
import json,subprocess,time
OUT=b.HERE/'environment-fixed';OUT.mkdir(exist_ok=True)
def main():
    tasks=json.loads((b.HERE/'generation-protocol.json').read_text())['tasks']
    protocol={'reason':'Sandboxed inference produced no output before timeout. Neutral prompt timed out at 90s with DEVNULL, but succeeded outside sandbox in ~4s. Same case prompts and budgets repeated outside sandbox; no model feedback or edits supplied.',
      'initial_attempts_preserved':True,'case_attempts_in_this_environment':1,'stdin':'DEVNULL','context':4096,'max_tokens':512,'seed':20261016,'temperature':0,'timeout_seconds':180,
      'tasks':tasks,'original_protocol_sha256':b.sha(b.HERE/'protocol.json'),'source_sha256':b.sha(b.Path(__file__))}
    if (OUT/'protocol.json').exists():raise FileExistsError('Preserve run')
    b.write(OUT/'protocol.json',protocol)
    model=b.ROOT/'work/gemma-runtime/gemma-4-E2B_q4_0-it.gguf';exe=b.ROOT/'work/gemma-runtime/llama/llama-cli.exe';assert b.sha(model)==b.MODEL_SHA256
    for task in tasks:
        pth=b.HERE/(task['id']+'.prompt.txt');assert b.sha(pth)==task['prompt_sha256']
        command=[str(exe),'-m',str(model),'-f',str(pth),'-c','4096','-n','512','-t','2','-b','64','-ub','64','-ngl','0','--temp','0','--seed','20261016','--reasoning','off','--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--perf']
        start=time.perf_counter();print('Generating outside sandbox',task['id'],flush=True)
        try:
            p=subprocess.run(command,stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
            row={'id':task['id'],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'timeout':False}
        except subprocess.TimeoutExpired as ex:
            dec=lambda x:x.decode('utf-8',errors='replace') if isinstance(x,bytes) else x or ''
            row={'id':task['id'],'returncode':None,'stdout':dec(ex.stdout),'stderr':dec(ex.stderr),'timeout':True}
        row['seconds']=time.perf_counter()-start;b.write(OUT/(task['id']+'-generation.json'),row);print('Finished',task['id'],row['returncode'],row['seconds'],flush=True)
if __name__=='__main__':main()

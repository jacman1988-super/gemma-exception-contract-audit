"""Replay the final frozen assisted prompts with separately supplied local Gemma weights."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODEL_SHA='fa401b55b07ee70a54c6dae3903c783a6e65064312529ea57175cb5f8dec6634'
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',action='store_true');p.add_argument('--model',type=Path);p.add_argument('--executable',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    tasks=[('tenacity',ROOT/'outputs/gemma-feedback-v4/tenacity-new-v2-repair.prompt.txt',768),('packaging',ROOT/'outputs/gemma-branch-feedback-v5/prompt.txt',512)]
    plan={'model_sha256':MODEL_SHA,'context':4096,'seed':20261016,'temperature':0,'threads':2,'tasks':[{'id':n,'prompt_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'max_tokens':limit} for n,path,limit in tasks],'scope':'Frozen assisted prompts; Tenacity includes the recorded diagnosis. Packaging contains explicit human structural guidance.'}
    if a.plan:print(json.dumps(plan,indent=2));return
    if not all([a.model,a.executable,a.output]):p.error('--model, --executable and --output are required unless --plan is used')
    if a.output.exists():p.error('Output must not already exist')
    if not a.model.is_file() or not a.executable.is_file():p.error('Model and executable must be local files')
    with a.model.open('rb') as file:
        if hashlib.file_digest(file,'sha256').hexdigest()!=MODEL_SHA:p.error('Model hash differs from the recorded experiment')
    version=subprocess.run([str(a.executable),'--version'],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=15);v=version.stdout+version.stderr
    if '11429' not in v or 'd81235049' not in v:p.error('Use the recorded llama.cpp b11429 / d81235049 runtime')
    a.output.mkdir(parents=True);(a.output/'protocol.json').write_text(json.dumps({**plan,'runtime_version':v},indent=2),encoding='utf-8')
    for name,prompt,limit in tasks:
        cmd=[str(a.executable),'-m',str(a.model),'-f',str(prompt),'-c','4096','-n',str(limit),'-t','2','-b','64','-ub','64','-ngl','0','--temp','0','--seed','20261016','--reasoning','off','--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--perf'];start=time.perf_counter()
        try:
            proc=subprocess.run(cmd,stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180);row={'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr,'timeout':False}
        except subprocess.TimeoutExpired as exc:
            dec=lambda x:x.decode('utf-8',errors='replace') if isinstance(x,bytes) else x or ''
            row={'returncode':None,'stdout':dec(exc.stdout),'stderr':dec(exc.stderr),'timeout':True}
        row['seconds']=time.perf_counter()-start;(a.output/(name+'.json')).write_text(json.dumps(row,indent=2),encoding='utf-8');print(name,'saved; no code executed',flush=True)
if __name__=='__main__':main()

"""Freeze all original diagnostics before running one text-only Gemma attempt each."""
import hashlib,json,subprocess,time
from pathlib import Path
from contract_resource import freeze
from local_model_pilot import MODEL_SHA256,MODEL_REVISION

def run():
    project=Path(__file__).resolve().parent;base=project.parents[1];out=project/'results/exception-contract-resource'
    protocol=freeze(out)
    model=base/'work/gemma-runtime/gemma-4-E2B_q4_0-it.gguf';exe=base/'work/gemma-runtime/llama/llama-cli.exe'
    if hashlib.file_digest(model.open('rb'),'sha256').hexdigest()!=MODEL_SHA256:raise ValueError('Unexpected model')
    environment={'model_revision':MODEL_REVISION,'model_sha256':MODEL_SHA256,'executable_sha256':hashlib.file_digest(exe.open('rb'),'sha256').hexdigest(),
                 'protocol_sha256':hashlib.sha256((out/'protocol.json').read_bytes()).hexdigest(),'context':4096,'max_tokens':512,'temperature':0,'seed':20261015,'threads':2,'reasoning':'off','automatic_execution':False}
    (out/'inference-protocol.json').write_text(json.dumps(environment,indent=2))
    rows=[]
    for case in protocol['cases']:
        prompt=out/(case['id']+'.prompt.txt');prompt.write_text(case['prompt'])
        cmd=[str(exe),'-m',str(model),'-f',str(prompt),'-c','4096','-n','512','-t','2','-b','64','-ub','64','-ngl','0','--temp','0','--seed','20261015','--reasoning','off','--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--perf']
        start=time.perf_counter()
        try:
            p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
            row={'id':case['id'],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'timed_out':False}
        except subprocess.TimeoutExpired as e:
            decode=lambda v:v.decode('utf-8',errors='replace') if isinstance(v,bytes) else v or ''
            row={'id':case['id'],'returncode':None,'stdout':decode(e.stdout),'stderr':decode(e.stderr),'timed_out':True}
        row['seconds']=time.perf_counter()-start;rows.append(row)
        (out/(case['id']+'.output.txt')).write_text(row['stdout'],encoding='utf-8')
        (out/'generations.json').write_text(json.dumps({'cases':rows,'complete':len(rows)==len(protocol['cases']),'applied':False},indent=2))
        print(case['id'],'exit',row['returncode'],'seconds',round(row['seconds'],1),flush=True)

if __name__=='__main__':run()

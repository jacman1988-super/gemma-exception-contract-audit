"""Packaging: isolate the one remaining behavioral failure, preserve passing cases."""
import sys,json,subprocess,time
from pathlib import Path
H=Path(__file__).resolve().parent;OUT=H/'single-failure';OUT.mkdir(exist_ok=True);sys.path.insert(0,str(H.parent/'gemma-new-repositories-v2'));import benchmark as b
def main():
    previous=json.loads((H/'api-feedback/reviewed.json').read_text());function=previous['edits'][0]['literal_function'];failure=json.loads((H/'api-feedback/packaging-new-v2-api-upstream.json').read_text())['stdout']
    prompt='Fix only the remaining failing behavior in this Python function while preserving already passing cases. Return ONLY a fenced python block with the complete function and same signature. Do not change the regex constant, normalize filenames, or remove full-string matching.\nContext:\n_PYLOCK_FILE_NAME_RE = re.compile(r"^pylock\\.([^.]+)\\.toml$")\n'+function+'\nRemaining executed failure:\n'+failure+'\nBehavior ledger:\npylock.toml -> True (currently False; fix this)\npylock.spam.toml -> True (already passes)\npylock.prod.toml -> True (already passes)\npylock.spam.toml followed by U+000A -> False (already passes)\npylock.prod.toml.backup -> False (already passes)\nKeep all these behaviors simultaneously.'
    (OUT/'prompt.txt').write_text(prompt,encoding='utf-8');protocol={'method':'Single remaining failure plus passing-behavior ledger','attempts':1,'tokens':512,'context':4096,'seed':20261016,'temperature':0,'previous_generation_sha256':b.sha(H/'api-feedback/generation.json'),'source_sha256':b.sha(Path(__file__)),'gold_source_supplied':False,'withheld_tests_shared':False}
    if (OUT/'protocol.json').exists():raise FileExistsError('Preserve run')
    b.write(OUT/'protocol.json',protocol);exe=b.ROOT/'work/gemma-runtime/llama/llama-cli.exe';model=b.ROOT/'work/gemma-runtime/gemma-4-E2B_q4_0-it.gguf';assert b.sha(model)==b.MODEL_SHA256
    cmd=[str(exe),'-m',str(model),'-f',str(OUT/'prompt.txt'),'-c','4096','-n','512','-t','2','-b','64','-ub','64','-ngl','0','--temp','0','--seed','20261016','--reasoning','off','--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--perf'];start=time.perf_counter()
    try:
        p=subprocess.run(cmd,stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180);row={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'timeout':False}
    except subprocess.TimeoutExpired as x:
        dec=lambda v:v.decode('utf-8',errors='replace') if isinstance(v,bytes) else v or ''
        row={'returncode':None,'stdout':dec(x.stdout),'stderr':dec(x.stderr),'timeout':True}
    row['seconds']=time.perf_counter()-start;b.write(OUT/'generation.json',row);print('Saved generation',row['returncode'],row['seconds'],flush=True)
if __name__=='__main__':main()

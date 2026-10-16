"""Packaging follow-up with explicit behavioral families and branch-oriented output."""
import sys,json,subprocess,time
from pathlib import Path
H=Path(__file__).resolve().parent;OLD=H.parent/'gemma-new-repositories-v2'
sys.path.insert(0,str(OLD));import benchmark as b
def main():
    previous=json.loads((H.parent/'gemma-feedback-v4/api-feedback/reviewed.json').read_text())['edits'][0]['literal_function']
    prompt='Repair this Python function. Previous one-expression answers omitted a valid case. Use an explicit decision tree with separate if branches for the TWO allowed filename families; do not compress both into only one regex check.\nRequirements:\nFamily 1: the exact ordinary filename pylock.toml is valid, even though the named-file regex does not recognize it.\nFamily 2: pylock.NAME.toml is valid when NAME is nonempty and contains no dot, and the entire unmodified filename matches.\nAll other filenames, including trailing U+000A and suffix garbage, are invalid. Do not strip or normalize input.\nContext:\n_PYLOCK_FILE_NAME_RE = re.compile(r"^pylock\\.([^.]+)\\.toml$")\n'+previous+'\nReturn ONLY a fenced python block containing the complete is_valid_pylock_path function with the same signature. Do not add imports, constants or helpers. Check both valid families before rejecting. No explanation.'
    (H/'prompt.txt').write_text(prompt,encoding='utf-8');protocol={'case':'packaging-new-v2','feedback':'Explicit two-family behavioral decomposition and requested separate if branches; strong human structural guidance, not an autonomous discovery claim. No upstream gold source.','tokens':512,'context':4096,'seed':20261016,'temperature':0,'attempts':1,'model_sha256':b.MODEL_SHA256,'source_sha256':b.sha(Path(__file__)),'previous_function':previous,'withheld_tests_shared':False}
    if (H/'protocol.json').exists():raise FileExistsError('Preserve run')
    b.write(H/'protocol.json',protocol);exe=b.ROOT/'work/gemma-runtime/llama/llama-cli.exe';model=b.ROOT/'work/gemma-runtime/gemma-4-E2B_q4_0-it.gguf';assert b.sha(model)==b.MODEL_SHA256
    cmd=[str(exe),'-m',str(model),'-f',str(H/'prompt.txt'),'-c','4096','-n','512','-t','2','-b','64','-ub','64','-ngl','0','--temp','0','--seed','20261016','--reasoning','off','--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--perf'];start=time.perf_counter()
    try:
        p=subprocess.run(cmd,stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180);row={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'timeout':False}
    except subprocess.TimeoutExpired as x:
        dec=lambda v:v.decode('utf-8',errors='replace') if isinstance(v,bytes) else v or ''
        row={'returncode':None,'stdout':dec(x.stdout),'stderr':dec(x.stderr),'timeout':True}
    row['seconds']=time.perf_counter()-start;b.write(H/'generation.json',row);print('Saved generation',row['returncode'],row['seconds'],flush=True)
if __name__=='__main__':main()

"""Neutral prompt: check whether inherited open stdin blocks noninteractive startup."""
import benchmark as b
import subprocess,time
def main():
    exe=b.ROOT/'work/gemma-runtime/llama/llama-cli.exe';model=b.ROOT/'work/gemma-runtime/gemma-4-E2B_q4_0-it.gguf'
    start=time.perf_counter()
    cmd=[str(exe),'-m',str(model),'-p','Reply OK.','-c','512','-n','1','-t','2','-ngl','0','--reasoning','off','--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup']
    try:
        p=subprocess.run(cmd,stdin=subprocess.DEVNULL,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
        row={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except subprocess.TimeoutExpired:row={'timeout':True}
    row['seconds']=time.perf_counter()-start;b.write(b.HERE/'runtime-diagnostic.json',row);print(row,flush=True)
if __name__=='__main__':main()

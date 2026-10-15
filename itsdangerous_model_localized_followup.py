"""One local model attempt; output recorded as text for review, never executed."""
import ast,hashlib,json,subprocess,time
from pathlib import Path
from local_model_pilot import MODEL_SHA256,MODEL_REVISION

def run():
    root=Path(__file__).resolve().parent;base=root.parents[1];out=root/'results/itsdangerous-model-localized-feedback'
    out.mkdir(parents=True,exist_ok=False)
    buggy=next((base/'work/new-upstream/itsdangerous-new-buggy').iterdir())
    path=buggy/'src/itsdangerous/timed.py';source=path.read_text();lines=source.splitlines()
    tree=ast.parse(source);functions=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in ['unsign','timestamp_to_datetime']]
    snippet='\n\n'.join('\n'.join(lines[n.lineno-1:n.end_lineno]) for n in functions if n.lineno<200)
    prompt=('Fix a Python bug. A malformed signed future timestamp reaches datetime.fromtimestamp and raises OSError on Windows instead of the library BadTimeSignature exception. '
            'Preserve valid timestamps and other error handling. Return only JSON string fields old and new containing one exact source block and its replacement. Do not run commands.\nBuggy source:\n'+snippet)
    prompt += '\nReview feedback: A previous proposal caught OSError in timestamp_to_datetime and raised BadTimeSignature with a new string payload. It passed 297 tests, but a differential probe found that the payload must remain the original bytes value and date_signed must stay None. Preserve these existing exception fields and direct conversion behavior. Return the smallest exact replacement block, not the whole function.'
    prompt += '\nAdditional execution feedback: The last proposal changed the bytes_to_int decoding handler but still failed the same test. The traceback is inside unsign: ts_dt = self.timestamp_to_datetime(ts_int), in the sig_error is not None branch. That call raises OSError. Keep the decoder and timestamp_to_datetime function unchanged; preserve existing BadTimeSignature construction, payload and exception chaining. Return one minimal replacement block in unsign.'
    model=base/'work/gemma-runtime/gemma-4-E2B_q4_0-it.gguf';exe=base/'work/gemma-runtime/llama/llama-cli.exe'
    if hashlib.file_digest(model.open('rb'),'sha256').hexdigest()!=MODEL_SHA256:raise ValueError('Model mismatch')
    protocol={'model_revision':MODEL_REVISION,'model_sha256':MODEL_SHA256,'executable_sha256':hashlib.file_digest(exe.open('rb'),'sha256').hexdigest(),
              'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'prompt':prompt,'attempts':1,'context':4096,'output_tokens':512,'temperature':0,'seed':20261015,'threads':2,
              'limitations':'Known public fix and previously observed failure; manually localized functions and symptom supplied. No fixed source, patch or test source in prompt. Not autonomous or contamination-free.',
              'harness_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'feedback_followup':'Second feedback-informed retry with explicit failing-call localization and edit restrictions. Earlier unsuccessful outputs retained. Strong human-agent guidance; not independent model success.', 'automatic_execution':False}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2));f=out/'prompt.txt';f.write_text(prompt)
    cmd=[str(exe),'-m',str(model),'-f',str(f),'-c','4096','-n','512','-t','2','-b','64','-ub','64','-ngl','0','--temp','0','--seed','20261015','--reasoning','off','--single-turn','--simple-io','--no-display-prompt','--color','off','--no-warmup','--perf']
    start=time.perf_counter()
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
        result={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'timed_out':False}
    except subprocess.TimeoutExpired as e:
        dec=lambda s:s.decode('utf-8',errors='replace') if isinstance(s,bytes) else s or ''
        result={'returncode':None,'stdout':dec(e.stdout),'stderr':dec(e.stderr),'timed_out':True}
    result['seconds']=time.perf_counter()-start
    (out/'generation.json').write_text(json.dumps(result,indent=2));(out/'output.txt').write_text(result['stdout'],encoding='utf-8')
    print('Model exit',result['returncode'],'seconds',round(result['seconds'],1),'raw output saved')

if __name__=='__main__':run()

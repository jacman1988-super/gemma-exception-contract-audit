"""Post-test differential diagnostic; not part of original frozen test pool."""
import json,os,subprocess,sys
from pathlib import Path

def run():
    root=Path(__file__).resolve().parent;base=root.parents[1];rows=[]
    code='''import json
from itsdangerous.timed import TimestampSigner
try:
    TimestampSigner("secret-key").unsign(b"value.TgPVoaGhoQ.AGBfQ6G6cr07byTRt0zAdPljHOY")
except Exception as e:
    print(json.dumps({"exception":type(e).__name__,"payload_type":type(getattr(e,"payload",None)).__name__,"payload_repr":repr(getattr(e,"payload",None))}))
'''
    for variant in ['fixed','parent','generated']:
        target=max((base/'work').glob('itsdangerous-'+variant+'-*'),key=lambda p:p.stat().st_mtime)
        env=os.environ.copy();env['PYTHONPATH']=str(target/'src')+os.pathsep+env.get('PYTHONPATH','')
        p=subprocess.run([sys.executable,'-B','-c',code],env=env,capture_output=True,text=True)
        if p.returncode:raise RuntimeError(p.stderr)
        rows.append({'variant':variant,**json.loads(p.stdout)})
    out=root/'results/itsdangerous-model-budget1024/payload-diagnostic.json'
    out.write_text(json.dumps({'scope':__doc__,'rows':rows,'model_patch_manually_corrected':False},indent=2));print(json.dumps(rows,indent=2))

if __name__=='__main__':run()

"""Evaluate the exact locally reviewed generated function; no arbitrary patches."""
import ast,hashlib,json,re,shutil,time
from pathlib import Path
from expansion_benchmark import execute

REVIEWED_NEW='''    def timestamp_to_datetime(self, ts: int) -> datetime:
        """Convert the timestamp from :meth:`get_timestamp` into an
        aware :class`datetime.datetime` in UTC. Raises :exc:`.BadTimeSignature`
        if the timestamp is malformed or out of range for Python.

        .. versionchanged:: 2.0
            The timestamp is returned as a timezone-aware ``datetime``
            in UTC rather than a naive ``datetime`` assumed to be UTC.
        """
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except OSError as e:
            # On Windows, datetime.fromtimestamp raises OSError for invalid timestamps.
            # We catch this and raise BadTimeSignature as per the requirement.
            raise BadTimeSignature("Malformed timestamp", payload=f"Timestamp {ts} caused OSError: {e}")'''

def run():
    project=Path(__file__).resolve().parent;base=project.parents[1];out=project/'results/itsdangerous-model-budget1024'
    text=(out/'output.txt').read_text(encoding='utf-8');match=re.search(r'```json\s*(.*?)\s*```',text,re.S)
    if not match:raise ValueError('No complete JSON; no repairs permitted')
    edit=json.loads(match.group(1))
    if set(edit)!= {'old','new'} or edit['new']!=REVIEWED_NEW:raise ValueError('Not the exact reviewed function')
    data=base/'work/new-upstream';case=json.loads((data/'cases.json').read_text())['cases'][0]
    fixed=next((data/'itsdangerous-new-fixed').iterdir());buggy=next((data/'itsdangerous-new-buggy').iterdir());name=case['changed'][0]
    source=(buggy/name).read_text();protocol=json.loads((out/'protocol.json').read_text())
    if hashlib.sha256((buggy/name).read_bytes()).hexdigest()!=protocol['source_sha256'] or source.count(edit['old'])!=1:raise ValueError('Source mismatch')
    patched=source.replace(edit['old'],edit['new']);ast.parse(patched)
    assessment={'reviewed_by':'Codex, not participant publication approval','review':'Only datetime conversion function changed; catches OSError and creates BadTimeSignature with a string payload. No file/network/process effects. Exact generated code tested without correction.',
                'patch':edit,'output_sha256':hashlib.sha256((out/'output.txt').read_bytes()).hexdigest(),'patched_text_sha256':hashlib.sha256(patched.encode()).hexdigest(),
                'pretest_rule':'Record primary declared timed-test module and full test directory for fixed, parent and generated versions. Retain all failures; no retry after test feedback.'}
    (out/'reviewed-patch.json').write_text(json.dumps(assessment,indent=2))
    rows=[]
    for variant in ['fixed','parent','generated']:
        target=base/'work'/('itsdangerous-'+variant+'-'+str(time.time_ns()));shutil.copytree(fixed,target)
        if variant=='parent':(target/name).write_text(source,encoding='utf-8')
        if variant=='generated':(target/name).write_text(patched,encoding='utf-8')
        primary=execute(target,case,case['pool']);full=execute(target,case,['tests'])
        rows.append({'variant':variant,'primary':primary,'full_suite':full})
        print(variant,'primary',primary['returncode'],'full',full['returncode'],flush=True)
    (out/'patch-evaluation.json').write_text(json.dumps({'cases':rows,'patch_manually_corrected':False,'submitted':False},indent=2))

if __name__=='__main__':run()

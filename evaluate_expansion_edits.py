"""Test only edits pinned in an assistant-reviewed local review record."""
import argparse,hashlib,json,os,re,shutil,time
from pathlib import Path
from expansion_benchmark import execute

def evaluate(data,evaluation,model_results,work,review,utf8=False):
    cases=json.loads((evaluation/'protocol.json').read_text(encoding='utf-8'))['cases']
    approved=json.loads(review.read_text(encoding='utf-8'))
    rows=[]
    for item in approved['cases']:
        case=next(c for c in cases if c['id']==item['id'])
        output=model_results/(case['id']+'.output.txt')
        assert hashlib.sha256(output.read_bytes()).hexdigest()==item['output_sha256']
        match=re.search(r'```json\s*(.*?)\s*```',output.read_text(encoding='utf-8'),re.S)
        if not match:
            rows.append({'id':case['id'],'status':'no_complete_json'});continue
        edit=json.loads(match.group(1))
        assert edit==item['reviewed_edit'],'Different edits require a separate review'
        fixed=next((data/(case['id']+'-fixed')).iterdir());buggy=next((data/(case['id']+'-buggy')).iterdir())
        assert len(case['changed'])==1
        file=case['changed'][0];source=(buggy/file).read_text(encoding='utf-8')
        if source.count(edit['old'])!=1:
            rows.append({'id':case['id'],'status':'nonapplicable_exact_edit','matches':source.count(edit['old'])});continue
        if edit['old']==edit['new']:
            original=next(c for c in json.loads((evaluation/'results.json').read_text())['cases'] if c['id']==case['id'])
            rows.append({'id':case['id'],'status':'unchanged_source_unresolved',
                         'test_result':original['runs']['full_declared_pool'],
                         'reused_unchanged_parent_test_result':True,'edit_repaired_by_reviewer':False})
            print(case['id'],'unchanged source; retained actual parent failure',flush=True)
            continue
        root=work/(case['id']+'-model-'+str(time.time_ns()));shutil.copytree(fixed,root)
        for n in case['changed']:shutil.copy2(buggy/n,root/n)
        patched=source.replace(edit['old'],edit['new'])
        (root/file).write_text(patched,encoding='utf-8')
        if utf8:os.environ['PYTHONUTF8']='1'
        result=execute(root,case,case['pool'])
        rows.append({'id':case['id'],'status':'passed_declared_pool' if result['returncode']==0 else 'failed_declared_pool',
                     'test_result':result,'patched_source_text_sha256':hashlib.sha256(patched.encode()).hexdigest(),
                     'utf8_environment':utf8,'edit_repaired_by_reviewer':False})
        print(case['id'],rows[-1]['status'],flush=True)
    (model_results/'reviewed-patch-evaluation.json').write_text(json.dumps({'cases':rows,'review_sha256':hashlib.sha256(review.read_bytes()).hexdigest(),
           'scope':'Inspected exact model edits only. Passing a declared subset is not complete upstream correctness.'},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['data','evaluation','model_results','work','review']:p.add_argument(n,type=Path)
    p.add_argument('--utf8',action='store_true');a=p.parse_args()
    evaluate(*(getattr(a,n).resolve() for n in ['data','evaluation','model_results','work','review']),utf8=a.utf8)

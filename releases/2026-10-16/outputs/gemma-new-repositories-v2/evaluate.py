"""Apply only manually reviewed exact edits to isolated parent trees."""
import json,shutil,ast,time
import benchmark as b
from collections import Counter
import xml.etree.ElementTree as ET
from validation_report import review

def checked(case,label,result,expected=None):
    path=b.Path(result['report']);root=ET.parse(path).getroot()
    counts=dict(Counter(t.get('classname') for t in root.iter('testcase')))
    checked=review(path,result['returncode'],expected or counts)
    return {'execution':result,'evidence':checked,'expected_counts':expected or counts}

def main():
    protocol=json.loads((b.HERE/'protocol.json').read_text());reviews=json.loads((b.HERE/'edit-review.json').read_text());out=[]
    for case in protocol['cases']:
        ident=case['id'];row=next(x for x in reviews if x['id']==ident)
        fixed=next((b.DATA/(ident+'-fixed')).iterdir());parent=next((b.DATA/(ident+'-buggy')).iterdir())
        pool_expected=checked(case,'reference',json.loads((b.HERE/'reference-results.json').read_text())[protocol['cases'].index(case)]['reference'])['expected_counts']
        record={'id':ident,'review':row,'runs':{}}
        for variant in ['fixed','parent','model']:
            if variant=='model' and not row.get('approved'):continue
            root=b.ROOT/'work'/(ident+'-checked-'+variant+'-'+str(time.time_ns()));shutil.copytree(fixed,root)
            if variant!='fixed':
                for name in case['changed']:shutil.copy2(parent/name,root/name)
            if variant=='model':
                generation=b.HERE/row['generation_file'];assert b.sha(generation)==row['generation_sha256']
                patch=row['patch'];matches=[name for name in case['changed'] if (root/name).read_text(encoding='utf-8').count(patch['old'])==1]
                assert len(matches)==1,'Exact unique replacement required'
                path=root/matches[0];source=path.read_text(encoding='utf-8').replace(patch['old'],patch['new'],1);ast.parse(source);path.write_text(source,encoding='utf-8')
                record['applied_file']=matches[0];record['patched_sha256']=b.sha(path)
            full=b.execute(root,case,variant+'-full-checked')
            record['runs'][variant]={'full':checked(case,variant,full,pool_expected)}
            control=b.HERE/('test_contract_'+case['package']+'.py');shutil.copy2(control,root/control.name)
            result=b.execute(root,{**case,'pool':[control.name]},variant+'-contract-checked')
            count=8 if case['package']=='tenacity' else 7
            record['runs'][variant]['contract']=checked(case,variant,result,{control.stem:count})
        out.append(record);b.write(b.HERE/'evaluated-results.json',out)
        print(ident,{v:{k:q['evidence']['accepted'] for k,q in rs.items()} for v,rs in record['runs'].items()},flush=True)
if __name__=='__main__':main()

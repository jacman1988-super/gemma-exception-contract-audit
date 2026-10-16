"""Strictly parse, review, and test feedback edits against the previous patch."""
import sys,json,shutil,time,ast
from pathlib import Path
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'gemma-new-repositories-v2'
sys.path.insert(0,str(OLD));import benchmark as b
from evaluate import checked

def unique_object(pairs):
    out={}
    for k,v in pairs:
        if k in out:raise ValueError('Duplicate JSON key: '+k)
        out[k]=v
    return out

def parse(text):
    if '```json\n' not in text:raise ValueError('No JSON response block')
    block=text.rsplit('```json\n',1)[1].split('```',1)[0]
    block=block.split('\n\n[ Prompt:',1)[0].strip()
    parsed=json.loads(block,object_pairs_hook=unique_object)
    if set(parsed)!= {'edits'} or not isinstance(parsed['edits'],list) or not parsed['edits']:raise ValueError('Expected nonempty edits list')
    for edit in parsed['edits']:
        if set(edit)!={'file','old','new'} or not all(isinstance(v,str) and v for v in edit.values()):raise ValueError('Invalid edit schema')
    return parsed['edits']

def preflight():
    reviews=[];cases=json.loads((OLD/'protocol.json').read_text())['cases']
    previous=json.loads((OLD/'edit-review.json').read_text())
    for case in cases:
        ident=case['id'];path=HERE/(ident+'-generation.json');gen=json.loads(path.read_text());item={'id':ident,'generation_sha256':b.sha(path),'parse_valid':False}
        try:
            if gen['timeout'] or gen['returncode']!=0:raise ValueError('Generation not completed')
            edits=parse(gen['stdout']);sources={n:(next((b.DATA/(ident+'-buggy')).iterdir())/n).read_text(encoding='utf-8') for n in case['changed']}
            p=next(x for x in previous if x['id']==ident)['patch'];matches=[n for n,s in sources.items() if s.count(p['old'])==1];assert len(matches)==1
            sources[matches[0]]=sources[matches[0]].replace(p['old'],p['new'],1)
            for edit in edits:
                if edit['file'] not in sources:raise ValueError('File outside declared source scope')
                source=sources[edit['file']]
                if source.count(edit['old'])!=1:raise ValueError('Old block must match exactly once')
                source=source.replace(edit['old'],edit['new'],1);ast.parse(source);sources[edit['file']]=source
            item.update(parse_valid=True,edits=edits)
        except (ValueError,KeyError,SyntaxError,AssertionError) as exc:item['rejection']=str(exc)
        reviews.append(item)
    b.write(HERE/'preflight.json',reviews);print(reviews,flush=True)

def evaluate():
    cases=json.loads((OLD/'protocol.json').read_text())['cases'];previous=json.loads((OLD/'edit-review.json').read_text());reviews=json.loads((HERE/'reviewed-edits.json').read_text());out=[]
    b.HERE=HERE
    for case in cases:
        ident=case['id'];review=next(x for x in reviews if x['id']==ident)
        assert b.sha(HERE/(ident+'-generation.json'))==review['generation_sha256']
        controls=OLD/('test_contract_'+case['package']+'.py');unseen=HERE/('test_unseen_'+case['package']+'.py')
        expected_full=checked(case,'fixed',json.loads((OLD/'reference-results.json').read_text())[cases.index(case)]['reference'])['expected_counts']
        result={'id':ident,'review':review,'runs':{}}
        for variant in ['fixed','previous','feedback']:
            if variant=='feedback' and not review.get('approved'):continue
            root=b.ROOT/'work'/(ident+'-feedback-'+variant+'-'+str(time.time_ns()));fixed=next((b.DATA/(ident+'-fixed')).iterdir());parent=next((b.DATA/(ident+'-buggy')).iterdir());shutil.copytree(fixed,root)
            if variant!='fixed':
                for name in case['changed']:shutil.copy2(parent/name,root/name)
                patch=next(x for x in previous if x['id']==ident)['patch'];matches=[n for n in case['changed'] if (root/n).read_text(encoding='utf-8').count(patch['old'])==1];assert len(matches)==1
                path=root/matches[0];path.write_text(path.read_text(encoding='utf-8').replace(patch['old'],patch['new'],1),encoding='utf-8')
            if variant=='feedback':
                for edit in review['edits']:
                    path=root/edit['file'];source=path.read_text(encoding='utf-8');assert source.count(edit['old'])==1
                    source=source.replace(edit['old'],edit['new'],1);ast.parse(source);path.write_text(source,encoding='utf-8')
            shutil.copy2(controls,root/controls.name);shutil.copy2(unseen,root/unseen.name)
            runs={}
            for group,paths,expected in [('upstream',case['pool'],expected_full),('feedback_tests',[controls.name],{controls.stem:8 if case['package']=='tenacity' else 7}),('withheld_tests',[unseen.name],{unseen.stem:9})]:
                run=b.execute(root,{**case,'pool':paths},variant+'-'+group);runs[group]=checked(case,variant,run,expected)
            result['runs'][variant]=runs
        out.append(result);b.write(HERE/'evaluated.json',out);print(ident,{v:{k:r['evidence']['accepted'] for k,r in groups.items()} for v,groups in result['runs'].items()},flush=True)
if __name__=='__main__':{'preflight':preflight,'evaluate':evaluate}[sys.argv[1]]()

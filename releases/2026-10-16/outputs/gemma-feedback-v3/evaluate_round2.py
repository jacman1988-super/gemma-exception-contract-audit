"""Evaluate the final cumulative-feedback attempt, retaining every rejection."""
import sys,json,shutil,time,ast
from pathlib import Path
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'gemma-new-repositories-v2';OUT=HERE/'round2'
sys.path.insert(0,str(OLD));import benchmark as b
from evaluate import checked
from evaluate_feedback import parse

def current(case):
    ident=case['id'];parent=next((b.DATA/(ident+'-buggy')).iterdir());sources={n:(parent/n).read_text(encoding='utf-8') for n in case['changed']}
    previous=json.loads((OLD/'edit-review.json').read_text());p=next(x for x in previous if x['id']==ident)['patch'];name=next(n for n,s in sources.items() if s.count(p['old'])==1);sources[name]=sources[name].replace(p['old'],p['new'],1)
    review=next(x for x in json.loads((HERE/'reviewed-edits.json').read_text()) if x['id']==ident)
    if review.get('approved'):
        for edit in review['edits']:sources[edit['file']]=sources[edit['file']].replace(edit['old'],edit['new'],1)
    return sources

def apply_edits(sources,edits):
    result=sources.copy()
    for edit in edits:
        if edit['file'] not in result:raise ValueError('File outside source scope')
        if edit['old']==edit['new']:raise ValueError('No-op edit is not a repair')
        if result[edit['file']].count(edit['old'])!=1:raise ValueError('Old block not unique')
        result[edit['file']]=result[edit['file']].replace(edit['old'],edit['new'],1);ast.parse(result[edit['file']])
    return result

def preflight():
    cases=json.loads((OLD/'protocol.json').read_text())['cases'];rows=[]
    for case in cases:
        path=OUT/(case['id']+'-generation.json');gen=json.loads(path.read_text());row={'id':case['id'],'generation_sha256':b.sha(path),'parse_valid':False}
        try:
            if gen['timeout'] or gen['returncode']!=0:raise ValueError('Generation failed')
            edits=parse(gen['stdout']);apply_edits(current(case),edits);row.update(parse_valid=True,edits=edits)
        except (ValueError,KeyError,SyntaxError,StopIteration) as ex:row['rejection']=str(ex)
        rows.append(row)
    b.write(OUT/'preflight.json',rows);print(rows,flush=True)

def evaluate():
    cases=json.loads((OLD/'protocol.json').read_text())['cases'];reviews=json.loads((OUT/'reviewed-edits.json').read_text());out=[];b.HERE=OUT
    for case in cases:
        review=next(x for x in reviews if x['id']==case['id']);row={'id':case['id'],'review':review,'runs':{}}
        if review.get('approved'):
            assert b.sha(OUT/(case['id']+'-generation.json'))==review['generation_sha256']
            sources=apply_edits(current(case),review['edits']);fixed=next((b.DATA/(case['id']+'-fixed')).iterdir());root=b.ROOT/'work'/(case['id']+'-feedback-round2-'+str(time.time_ns()));shutil.copytree(fixed,root)
            for name,source in sources.items():(root/name).write_text(source,encoding='utf-8')
            control=OLD/('test_contract_'+case['package']+'.py');unseen=HERE/('test_unseen_'+case['package']+'.py');shutil.copy2(control,root/control.name);shutil.copy2(unseen,root/unseen.name)
            expected=checked(case,'fixed',json.loads((OLD/'reference-results.json').read_text())[cases.index(case)]['reference'])['expected_counts']
            for group,paths,counts in [('upstream',case['pool'],expected),('feedback_tests',[control.name],{control.stem:8 if case['package']=='tenacity' else 7}),('withheld_tests',[unseen.name],{unseen.stem:9})]:
                run=b.execute(root,{**case,'pool':paths},'round2-'+group);row['runs'][group]=checked(case,'round2',run,counts)
        out.append(row);b.write(OUT/'evaluated.json',out);print(case['id'],{k:q['evidence']['accepted'] for k,q in row['runs'].items()},flush=True)
if __name__=='__main__':{'preflight':preflight,'evaluate':evaluate}[sys.argv[1]]()

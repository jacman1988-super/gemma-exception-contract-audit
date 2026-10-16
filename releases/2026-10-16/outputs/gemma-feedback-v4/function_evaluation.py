"""Extract literal generated functions without changing their bodies; isolated tests."""
import ast,json,re,sys,textwrap,shutil,time
from pathlib import Path
H=Path(__file__).resolve().parent;OLD=H.parent/'gemma-new-repositories-v2';CONTROLS=H.parent/'gemma-feedback-v3'
sys.path.insert(0,str(OLD));import benchmark as b
from evaluate import checked

def response(text):
    if ' ... (truncated)\n' not in text:raise ValueError('Cannot locate end of echoed prompt')
    return text.split(' ... (truncated)\n',1)[1].split('\n\n[ Prompt:',1)[0].strip()

def functions(text,case):
    text=response(text);parts=re.split(r'^FILE:\s*(\S+)\s*$',text,flags=re.M)
    if len(parts)==1:
        if len(case['changed'])!=1:raise ValueError('Ambiguous missing file headers')
        blocks=[(case['changed'][0],text)]
    else:
        if parts[0].strip():raise ValueError('Unexpected preamble')
        blocks=list(zip(parts[1::2],parts[2::2]))
    if sorted(n for n,_ in blocks)!=sorted(case['changed']):raise ValueError('Missing, repeated or out-of-scope file')
    result=[]
    for name,code in blocks:
        if '```' in code:
            match=re.search(r'```(?:python)?\s*\n(.*?)```',code,re.S)
            if not match:raise ValueError('Incomplete code fence')
            code=match.group(1)
        code=textwrap.dedent(code).strip();tree=ast.parse(code)
        expected='_run_wait' if case['package']=='tenacity' else 'is_valid_pylock_path'
        nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
        if len(nodes)!=1 or nodes[0].name!=expected:raise ValueError('Expected precisely the declared function')
        node=nodes[0];literal='\n'.join(code.splitlines()[node.lineno-1:node.end_lineno])
        result.append({'file':name,'function':node.name,'literal_function':literal,'ignored_module_context':[type(n).__name__ for n in tree.body if n is not node]})
    return result

def preflight():
    cases=json.loads((OLD/'protocol.json').read_text())['cases'];rows=[]
    b.write(H/'parser-policy.json',{'interface':'Function replacement only, as requested before generation. Preserve generated function bodies exactly; reindent to original method scope. Accept bare code with FILE header or fenced code. Missing header accepted only for single declared file. Extra module imports/constants never applied; retained in audit. No semantic repair.', 'policy_recorded_before_test_execution':True})
    for case in cases:
        path=H/(case['id']+'-repair.json');gen=json.loads(path.read_text());row={'id':case['id'],'generation_sha256':b.sha(path),'parsed':False}
        try:
            if gen['timeout'] or gen['returncode']!=0:raise ValueError('Generation incomplete')
            edits=functions(gen['stdout'],case);parent=next((b.DATA/(case['id']+'-buggy')).iterdir())
            for edit in edits:
                tree=ast.parse((parent/edit['file']).read_text(encoding='utf-8'));original=next(n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==edit['function']);new=ast.parse(edit['literal_function']).body[0]
                # Decorators precede node.lineno and remain in the original file.
                if type(original)!=type(new) or ast.dump(original.args)!=ast.dump(new.args) or ast.dump(original.returns)!=ast.dump(new.returns) or new.decorator_list:raise ValueError('Function signature/type changed or decorator added')
            row.update(parsed=True,edits=edits)
        except (ValueError,SyntaxError,StopIteration) as ex:row['rejection']=str(ex)
        rows.append(row)
    b.write(H/'preflight.json',rows);print(rows,flush=True)

def evaluate():
    cases=json.loads((OLD/'protocol.json').read_text())['cases'];reviews=json.loads((H/'reviewed-functions.json').read_text());out=[];b.HERE=H
    for case in cases:
        review=next(v for v in reviews if v['id']==case['id']);item={'id':case['id'],'review':review,'runs':{}}
        if review.get('approved'):
            assert b.sha(H/(case['id']+'-repair.json'))==review['generation_sha256']
            parent=next((b.DATA/(case['id']+'-buggy')).iterdir());fixed=next((b.DATA/(case['id']+'-fixed')).iterdir());root=b.ROOT/'work'/(case['id']+'-staged-'+str(time.time_ns()));shutil.copytree(fixed,root)
            for name in case['changed']:shutil.copy2(parent/name,root/name)
            for edit in review['edits']:
                path=root/edit['file'];source=path.read_text(encoding='utf-8');lines=source.splitlines();node=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==edit['function']);indent=' '*node.col_offset
                replacement=textwrap.indent(edit['literal_function'],indent).splitlines();lines[node.lineno-1:node.end_lineno]=replacement;new='\n'.join(lines)+'\n';ast.parse(new);path.write_text(new,encoding='utf-8')
            control=OLD/('test_contract_'+case['package']+'.py');withheld=CONTROLS/('test_unseen_'+case['package']+'.py');shutil.copy2(control,root/control.name);shutil.copy2(withheld,root/withheld.name)
            reference=json.loads((OLD/'reference-results.json').read_text())[cases.index(case)]['reference'];expected=checked(case,'ref',reference)['expected_counts']
            for group,paths,counts in [('upstream',case['pool'],expected),('examples',[control.name],{control.stem:8 if case['package']=='tenacity' else 7}),('withheld',[withheld.name],{withheld.stem:9})]:
                result=b.execute(root,{**case,'pool':paths},'staged-'+group);item['runs'][group]=checked(case,'staged',result,counts)
            item['patched_source_sha256']={name:b.sha(root/name) for name in case['changed']}
        out.append(item);b.write(H/'evaluated.json',out);print(case['id'],{k:v['evidence']['accepted'] for k,v in item['runs'].items()},flush=True)
if __name__=='__main__':{'preflight':preflight,'evaluate':evaluate}[sys.argv[1]]()

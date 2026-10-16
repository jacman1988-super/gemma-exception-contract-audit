"""Review and evaluate the Packaging API-assisted follow-up."""
import function_evaluation as f
import ast,json,textwrap,shutil,time,sys
H=f.H;OUT=H/'api-feedback';b=f.b
def preflight():
    case=next(c for c in json.loads((f.OLD/'protocol.json').read_text())['cases'] if c['package']=='packaging');gen=json.loads((OUT/'generation.json').read_text());assert gen['returncode']==0 and not gen['timeout']
    edits=f.functions(gen['stdout'],case);b.write(OUT/'preflight.json',{'edits':edits,'generation_sha256':b.sha(OUT/'generation.json'),'function_only_context_policy':b.sha(H/'parser-policy.json')});print(edits,flush=True)
def evaluate():
    case=next(c for c in json.loads((f.OLD/'protocol.json').read_text())['cases'] if c['package']=='packaging');review=json.loads((OUT/'reviewed.json').read_text());assert review['approved'] and review['generation_sha256']==b.sha(OUT/'generation.json')
    fixed=next((b.DATA/(case['id']+'-fixed')).iterdir());parent=next((b.DATA/(case['id']+'-buggy')).iterdir());root=b.ROOT/'work'/('packaging-api-'+str(time.time_ns()));shutil.copytree(fixed,root)
    for name in case['changed']:shutil.copy2(parent/name,root/name)
    for edit in review['edits']:
        path=root/edit['file'];source=path.read_text(encoding='utf-8');lines=source.splitlines();node=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name==edit['function']);new=ast.parse(edit['literal_function']).body[0]
        assert ast.dump(new.args)==ast.dump(node.args) and ast.dump(new.returns)==ast.dump(node.returns)
        lines[node.lineno-1:node.end_lineno]=textwrap.indent(edit['literal_function'],' '*node.col_offset).splitlines();source='\n'.join(lines)+'\n';ast.parse(source);path.write_text(source,encoding='utf-8')
    control=f.OLD/'test_contract_packaging.py';withheld=f.CONTROLS/'test_unseen_packaging.py';shutil.copy2(control,root/control.name);shutil.copy2(withheld,root/withheld.name)
    reference=next(r for r in json.loads((f.OLD/'reference-results.json').read_text()) if r['id']==case['id'])['reference'];expected=f.checked(case,'ref',reference)['expected_counts'];b.HERE=OUT;runs={}
    for group,paths,counts in [('upstream',case['pool'],expected),('examples',[control.name],{control.stem:7}),('withheld',[withheld.name],{withheld.stem:9})]:
        run=b.execute(root,{**case,'pool':paths},'api-'+group);runs[group]=f.checked(case,'api',run,counts)
    b.write(OUT/'evaluated.json',{'runs':runs,'patched_source_sha256':{n:b.sha(root/n) for n in case['changed']}});print({k:q['evidence']['accepted'] for k,q in runs.items()},flush=True)
if __name__=='__main__':{'preflight':preflight,'evaluate':evaluate}[sys.argv[1]]()

"""Post-hoc differential filename check against actual pinned upstream function."""
import sys,json,ast,textwrap,shutil,subprocess,os,random,string,time
from pathlib import Path
H=Path(__file__).resolve().parent;OLD=H.parent/'gemma-new-repositories-v2'
sys.path.insert(0,str(OLD));import benchmark as b
def main():
    case=next(c for c in json.loads((OLD/'protocol.json').read_text())['cases'] if c['package']=='packaging');fixed=next((b.DATA/(case['id']+'-fixed')).iterdir());parent=next((b.DATA/(case['id']+'-buggy')).iterdir());review=json.loads((H/'reviewed.json').read_text());root=b.ROOT/'work'/('packaging-branch-vector-'+str(time.time_ns()));shutil.copytree(fixed,root)
    for n in case['changed']:shutil.copy2(parent/n,root/n)
    for edit in review['edits']:
        path=root/edit['file'];source=path.read_text(encoding='utf-8');lines=source.splitlines();node=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name==edit['function']);lines[node.lineno-1:node.end_lineno]=textwrap.indent(edit['literal_function'],' '*node.col_offset).splitlines();path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    tested=json.loads((H/'evaluated.json').read_text())['patched_source_sha256'];assert all(b.sha(root/n)==tested[n] for n in case['changed'])
    names=['pylock.toml','pylock.toml\n','pylock.toml.old','pylock..toml']
    for name in ['a','prod','','.','..','a.b','a\n','\n','å','a\\b','a/b','a\x00b','C:']:
        for prefix in ['pylock.','other.','PYLOCK.','pylock..']:
            for suffix in ['.toml','.toml\n','.toml\r\n','.toml.old','.TOML','']:names.append(prefix+name+suffix)
    rng=random.Random(20261016);alphabet='abcXYZ012._-\n\r\\/å'
    for _ in range(1000):
        middle=''.join(rng.choice(alphabet) for _ in range(rng.randrange(0,20)));names.append(rng.choice(['pylock.','other.',''])+middle+rng.choice(['.toml','.toml\n','.toml.old','']))
    names=list(dict.fromkeys(names));inputs=H/'differential-inputs.json'
    if inputs.exists():raise FileExistsError('Preserve check')
    inputs.write_text(json.dumps(names),encoding='utf-8');b.write(H/'differential-protocol.json',{'count':len(names),'seed':20261016,'input_sha256':b.sha(inputs),'post_hoc_after_model_output':True,'reference':'Pinned upstream fixed function, not a hand-written oracle','model_source_hashes_match_tested':True,'source_sha256':b.sha(Path(__file__))})
    rows={}
    script='import json,sys;from pathlib import Path;import packaging.pylock as m;names=json.loads(Path(sys.argv[1]).read_text());print(json.dumps({"module":m.__file__,"values":[m.is_valid_pylock_path(Path(n)) for n in names]}))'
    for label,folder in [('fixed',fixed),('model',root)]:
        env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join([str(folder/'src'),env.get('PYTHONPATH','')]);env['PYTHONDONTWRITEBYTECODE']='1'
        p=subprocess.run([sys.executable,'-B','-c',script,str(inputs.resolve())],cwd=folder,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60);assert p.returncode==0,p.stderr
        rows[label]=json.loads(p.stdout);b.write(H/('differential-'+label+'.json'),rows[label])
    differences=[{'name':n,'reference':a,'model':b2} for n,a,b2 in zip(names,rows['fixed']['values'],rows['model']['values']) if a!=b2]
    result={'tested_names':len(names),'differences':differences,'all_agree':not differences,'post_hoc':True};b.write(H/'differential-result.json',result);print(result,flush=True)
if __name__=='__main__':main()

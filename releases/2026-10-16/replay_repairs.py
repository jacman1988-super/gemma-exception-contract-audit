"""Replay reviewed Tenacity/Packaging repairs using hash-verified local pinned archives."""
import argparse,ast,hashlib,json,os,shutil,subprocess,sys,textwrap,time,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parent;PROJECT=ROOT/'outputs/gemma-importguard'
sys.path.insert(0,str(PROJECT));from validation_report import review
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def extract(archive,destination):
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            path=PurePosixPath(item.filename)
            if path.is_absolute() or '..' in path.parts or ':' in item.filename or '\\' in item.filename:raise ValueError('Unsafe archive member')
            if (item.external_attr>>16)&0o170000==0o120000:continue
            z.extract(item,destination)
    return next(destination.iterdir())
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--archives',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():parser.error('Output must be a new directory')
    out=args.output.resolve();out.mkdir(parents=True);old=ROOT/'outputs/gemma-new-repositories-v2';cases=json.loads((old/'protocol.json').read_text())['cases'];results=[]
    for case in cases:
        ident=case['id'];sources={}
        for version in ['fixed','buggy']:
            archive=args.archives/(ident+'-'+version+'.zip')
            if sha(archive)!=case['archives_sha256'][version]:raise ValueError('Pinned archive hash differs: '+archive.name)
            sources[version]=extract(archive,out/(ident+'-'+version))
        for name,digest in case['tests_sha256'].items():
            if sha(sources['fixed']/name)!=digest:raise ValueError('Upstream test changed')
        if case['package']=='tenacity':record=next(x for x in json.loads((ROOT/'outputs/gemma-feedback-v4/reviewed-functions.json').read_text()) if x['id']==ident);generated=ROOT/'outputs/gemma-feedback-v4'/ (ident+'-repair.json')
        else:record=json.loads((ROOT/'outputs/gemma-branch-feedback-v5/reviewed.json').read_text());generated=ROOT/'outputs/gemma-branch-feedback-v5/generation.json'
        if sha(generated)!=record['generation_sha256']:raise ValueError('Reviewed generation changed')
        expected_runs=json.loads((ROOT/'outputs/gemma-feedback-v4/evaluated.json').read_text());expected=next(x for x in expected_runs if x['id']==ident)['runs']['upstream']['expected_counts'];runs={}
        for variant in ['fixed','parent','model']:
            work=out/(ident+'-'+variant+'-run');shutil.copytree(sources['fixed'],work)
            if variant!='fixed':
                for name in case['changed']:shutil.copy2(sources['buggy']/name,work/name)
            if variant=='model':
                for edit in record['edits']:
                    path=work/edit['file'];lines=path.read_text(encoding='utf-8').splitlines();tree=ast.parse('\n'.join(lines));node=next(n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==edit['function']);new=ast.parse(edit['literal_function']).body[0]
                    if type(node)!=type(new) or ast.dump(node.args)!=ast.dump(new.args) or ast.dump(node.returns)!=ast.dump(new.returns):raise ValueError('Reviewed signature differs')
                    lines[node.lineno-1:node.end_lineno]=textwrap.indent(edit['literal_function'],' '*node.col_offset).splitlines();source='\n'.join(lines)+'\n';ast.parse(source);path.write_text(source,encoding='utf-8')
            controls=old/('test_contract_'+case['package']+'.py');hidden=ROOT/'outputs/gemma-feedback-v3'/('test_unseen_'+case['package']+'.py');shutil.copy2(controls,work/controls.name);shutil.copy2(hidden,work/hidden.name)
            env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join([str(work/case['source_root']),str(work),env.get('PYTHONPATH','')]);env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';env['PYTHONDONTWRITEBYTECODE']='1';groups={}
            for group,paths,counts in [('upstream',case['pool'],expected),('examples',[controls.name],{controls.stem:8 if case['package']=='tenacity' else 7}),('withheld',[hidden.name],{hidden.stem:9})]:
                xml=out/(ident+'-'+variant+'-'+group+'.xml');proc=subprocess.run([sys.executable,'-B','-m','pytest','-o','addopts=','-q','--tb=short','--junitxml='+str(xml),*paths],cwd=work,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180);evidence=review(xml,proc.returncode,counts)
                if not evidence['complete']:raise ValueError(evidence['reasons'])
                groups[group]={'accepted':evidence['accepted'],'returncode':proc.returncode,'tests':sum(counts.values())};(out/(ident+'-'+variant+'-'+group+'.log.txt')).write_text(proc.stdout+proc.stderr,encoding='utf-8')
            runs[variant]=groups
        if not all(q['accepted'] for q in runs['fixed'].values()) or not all(q['accepted'] for q in runs['model'].values()) or runs['parent']['upstream']['accepted']:raise ValueError('Repair replay differs from frozen outcome')
        results.append({'id':ident,'runs':runs});(out/'results.json').write_text(json.dumps({'cases':results,'all_checks_passed':len(results)==len(cases)},indent=2),encoding='utf-8');print(ident,'reproduced',flush=True)
if __name__=='__main__':main()

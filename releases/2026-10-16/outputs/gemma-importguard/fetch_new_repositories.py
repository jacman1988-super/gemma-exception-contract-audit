import urllib.request,json,zipfile,hashlib
from pathlib import Path,PurePosixPath
B=Path(__file__).resolve().parents[2];D=B/'work/new-upstream';D.mkdir(exist_ok=True)
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ImportGuard-local-research'}),timeout=90) as r:return r.read()
cases=[]
for repo,package in [('pallets/itsdangerous','itsdangerous'),('grantjenks/python-sortedcontainers','sortedcontainers')]:
    commits=[]
    for prefix in ['src/'+package,package]:commits.extend(json.loads(get('https://api.github.com/repos/'+repo+'/commits?per_page=100&path='+prefix)))
    commits=sorted({c['sha']:c for c in commits}.values(),key=lambda c:c['commit']['committer']['date'],reverse=True)
    selected=None
    for short in commits:
        if not any(word in short['commit']['message'].lower() for word in ['fix','handle','catch']):continue
        c=json.loads(get('https://api.github.com/repos/'+repo+'/commits/'+short['sha']))
        source=[f['filename'] for f in c['files'] if f['filename'].endswith('.py') and (f['filename'].startswith(package+'/') or f['filename'].startswith('src/'+package+'/'))]
        tests=[f['filename'] for f in c['files'] if f['filename'].startswith('tests/') and f['filename'].endswith('.py') and Path(f['filename']).name.startswith('test')]
        if len(c['parents'])==1 and source and tests and all(f['status']=='modified' for f in c['files'] if f['filename'] in source):selected=(c,source,tests);break
    if selected is None:raise RuntimeError('No eligible case '+repo)
    c,source,tests=selected;identifier=package+'-new';(D/(identifier+'.json')).write_text(json.dumps(c,indent=2))
    archives={}
    for version,rev in [('fixed',c['sha']),('buggy',c['parents'][0]['sha'])]:
        data=get('https://codeload.github.com/'+repo+'/zip/'+rev);p=D/(identifier+'-'+version+'.zip');p.write_bytes(data);archives[version]=hashlib.sha256(data).hexdigest()
        with zipfile.ZipFile(p) as z:
            for info in z.infolist():
                path=PurePosixPath(info.filename)
                if path.is_absolute() or '..' in path.parts or ':' in info.filename or '\\' in info.filename or (info.external_attr>>16)&0o170000==0o120000:raise ValueError('Unsafe archive')
            z.extractall(D/(identifier+'-'+version))
    fixed=next((D/(identifier+'-fixed')).iterdir());license=next(p for p in [fixed/'LICENSE',fixed/'LICENSE.txt',fixed/'LICENSE.rst'] if p.exists())
    case={'id':identifier,'repo':repo,'package':package,'source_root':'src' if (fixed/'src'/package).exists() else '.', 'changed':source,'pool':tests,'fixed':c['sha'],'parent':c['parents'][0]['sha'],'url':c['html_url'],'archives_sha256':archives,'license_text':license.read_text(),'tests_sha256':{n:hashlib.sha256((fixed/n).read_bytes()).hexdigest() for n in tests}}
    cases.append(case);print(identifier,c['sha'],source,tests,flush=True)
(D/'cases.json').write_text(json.dumps({'cases':cases,'selection':'First newest first-parent source change in latest 100 source-directory commits per root (message contains fix, handle or catch) with modified package Python source and changed test module. Expanded from fix-only before any test outcomes: ItsDangerous uses handle/catch for exception corrections. No replacement after results.'},indent=2))

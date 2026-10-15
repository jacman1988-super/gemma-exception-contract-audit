"""Download the two public pilot snapshots, verifying the recorded archives.

No package installation, authentication, terms acceptance, or code execution.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import urllib.request
import zipfile

def download(url,path):
    request=urllib.request.Request(url,headers={'User-Agent':'ImportGuard-research-pilot'})
    with urllib.request.urlopen(request,timeout=90) as response:
        path.write_bytes(response.read())

def fetch(destination,manifest):
    destination.mkdir(parents=True,exist_ok=True)
    for case in json.loads(manifest.read_text())['cases']:
        meta=destination/(case['id']+'.json')
        download(f"https://api.github.com/repos/{case['repo']}/commits/{case['fixed']}",meta)
        actual=json.loads(meta.read_text())
        assert actual['sha']==case['fixed'] and actual['parents'][0]['sha']==case['parent']
        for version,sha in [('fixed',case['fixed']),('buggy',case['parent'])]:
            archive=destination/(case['id']+'-'+version+'.zip')
            download(f"https://codeload.github.com/{case['repo']}/zip/{sha}",archive)
            if hashlib.sha256(archive.read_bytes()).hexdigest()!=case['archives_sha256'][version]:
                raise ValueError('Archive bytes changed; inspect provenance before proceeding: '+str(archive))
            target=destination/(case['id']+'-'+version)
            with zipfile.ZipFile(archive) as z:
                for info in z.infolist():
                    path=PurePosixPath(info.filename)
                    if path.is_absolute() or '..' in path.parts or '\\' in info.filename or ':' in info.filename:
                        raise ValueError('Unsafe archive path')
                    if (info.external_attr>>16)&0o170000==0o120000:
                        raise ValueError('Symbolic link not supported')
                if z.testzip() is not None:raise ValueError('Archive CRC failure')
                z.extractall(target)
        print('Verified',case['id'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',type=Path)
    p.add_argument('--manifest',type=Path,default=Path('results/real-bugs-pilot/pilot-manifest.json'))
    a=p.parse_args();fetch(a.destination,a.manifest)

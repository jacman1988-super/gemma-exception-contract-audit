"""Repair a missing test-only dependency; preserve the failed first reference."""
import benchmark as b
import json,shutil
def main():
    cases=json.loads((b.HERE/'protocol.json').read_text())['cases']
    rows=json.loads((b.HERE/'reference-results.json').read_text())
    b.write(b.HERE/'reference-results-initial.json',rows)
    b.write(b.HERE/'environment-amendment.json',{'reason':'Packaging collection failed due to absent tomli_w. Install tomli-w==1.2.0; unchanged source, tests and case selection. Keep initial failure.', 'model_has_run':False})
    c=next(x for x in cases if x['package']=='packaging');row=next(x for x in rows if x['id']==c['id']);root=b.Path(row['root'])
    fixed=next((b.DATA/(c['id']+'-fixed')).iterdir());buggy=next((b.DATA/(c['id']+'-buggy')).iterdir())
    for n in c['changed']:shutil.copy2(fixed/n,root/n)
    ref=b.execute(root,c,'reference-env-fixed')
    for n in c['changed']:shutil.copy2(buggy/n,root/n)
    parent=b.execute(root,c,'parent-env-fixed')
    row.update(reference=ref,parent=parent,reproduced=ref['returncode']==0 and parent['returncode']==1 and 'ERROR collecting' not in parent.get('stdout',''))
    b.write(b.HERE/'reference-results.json',rows);print(c['id'],ref['returncode'],parent['returncode'],flush=True)
if __name__=='__main__':main()

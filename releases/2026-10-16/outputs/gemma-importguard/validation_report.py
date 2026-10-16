"""Fail-closed JUnit evidence review; passing is not proof of patch correctness."""
import argparse,json
from pathlib import Path
import xml.etree.ElementTree as ET

def review(path,returncode,expected,*,timed_out=False):
    if not expected or any(type(n) is not int or n<1 for n in expected.values()):
        raise ValueError('Expected groups must have positive integer test counts')
    reasons=[];tests=[];groups={name:[] for name in expected}
    if timed_out:reasons.append('Execution timed out')
    if returncode not in (0,1):reasons.append(f'Unexpected process exit code: {returncode}')
    try:root=ET.parse(path).getroot()
    except (ET.ParseError,OSError) as e:
        return {'complete':False,'accepted':False,'reasons':reasons+[f'Unreadable JUnit report: {e}'],'groups':groups}
    if root.tag not in ('testsuite','testsuites'):reasons.append('Unexpected XML root')
    suites=list(root.iter('testsuite'))
    if not suites:reasons.append('No test suites')
    # Validate every aggregation level, including testsuites roots and nested
    # parents. Checking only leaf suites can hide contradictory summary errors.
    for suite in (e for e in root.iter() if e.tag in ('testsuite','testsuites')):
        try:
            for attr in ('errors','failures','skipped','tests'):
                if int(suite.attrib.get(attr,0))<0:raise ValueError(attr)
            if int(suite.attrib.get('errors',0)):reasons.append('Suite reports collection or execution errors')
            descendants=list(suite.iter('testcase'))
            if 'tests' in suite.attrib and int(suite.attrib['tests'])!=len(descendants):
                reasons.append('Suite test count differs from testcase records')
            for attr,tag in [('failures','failure'),('errors','error'),('skipped','skipped')]:
                if attr in suite.attrib and int(suite.attrib[attr])!=sum(t.find(tag) is not None for t in descendants):
                    reasons.append(f'Suite {attr} counter contradicts testcase records')
        except ValueError:reasons.append('Invalid suite counters')
        if suite.findall('error'):reasons.append('Suite-level error')
    seen=set()
    for case in root.iter('testcase'):
        classname=case.attrib.get('classname','');name=case.attrib.get('name','');key=(classname,name)
        if not name or key in seen:reasons.append('Missing or duplicate test identity')
        seen.add(key)
        if classname not in groups:
            reasons.append(f'Unexpected test group: {classname}');continue
        passed=not any(case.find(tag) is not None for tag in ('failure','error','skipped'))
        item={'name':name,'passed':passed};groups[classname].append(item);tests.append(item)
    for name,n in expected.items():
        if len(groups[name])!=n:reasons.append(f'Expected {n} tests in {name}; found {len(groups[name])}')
    if not tests:reasons.append('No recognized tests')
    all_pass=bool(tests) and all(t['passed'] for t in tests)
    if returncode==0 and not all_pass:reasons.append('Successful exit contradicts test outcomes')
    if returncode==1 and all_pass:reasons.append('Failing exit contradicts passing test records')
    complete=not reasons
    return {'complete':complete,'accepted':complete and returncode==0 and all_pass,'reasons':list(dict.fromkeys(reasons)),
            'group_pass':{k:complete and bool(v) and all(t['passed'] for t in v) for k,v in groups.items()},'groups':groups}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);p.add_argument('--returncode',type=int,required=True)
    p.add_argument('--weak',type=int,default=3);p.add_argument('--contract',type=int,default=4);p.add_argument('--timed-out',action='store_true')
    a=p.parse_args()
    if min(a.weak,a.contract)<0 or a.weak+a.contract==0:p.error('Test counts must be nonnegative and total must be positive')
    expected={k:n for k,n in [('test_weak',a.weak),('test_contract',a.contract)] if n}
    result=review(a.report,a.returncode,expected,timed_out=a.timed_out)
    print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['accepted'] else 1)

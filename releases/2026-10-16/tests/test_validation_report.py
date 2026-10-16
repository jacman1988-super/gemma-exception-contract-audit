import xml.etree.ElementTree as ET
import pytest
from validation_report import review

def report(tmp_path,mutate=None):
    root=ET.Element('testsuites');suite=ET.SubElement(root,'testsuite',tests='2',errors='0',failures='0',skipped='0')
    ET.SubElement(suite,'testcase',classname='test_weak',name='weak')
    ET.SubElement(suite,'testcase',classname='test_contract',name='contract')
    if mutate:mutate(suite)
    path=tmp_path/'result.xml';ET.ElementTree(root).write(path);return path

def check(path,code=0,**kwargs):return review(path,code,{'test_weak':1,'test_contract':1},**kwargs)

def test_valid_complete_report_passes(tmp_path):assert check(report(tmp_path))['accepted']

@pytest.mark.parametrize('expected',[{}, {'test_weak':0},{'test_weak':-1},{'test_weak':True}])
def test_invalid_expectations_do_not_certify_empty_or_incomplete_runs(tmp_path,expected):
    with pytest.raises(ValueError):review(report(tmp_path),0,expected)

@pytest.mark.parametrize('change',[
    lambda s:s.set('errors','1'),
    lambda s:s.set('failures','1'),
    lambda s:s.set('tests','3'),
    lambda s:s.set('tests','invalid'),
    lambda s:ET.SubElement(s,'error').__setattr__('text','collection failed'),
    lambda s:s.find('testcase').set('classname','unrelated'),
    lambda s:ET.SubElement(s.find('testcase'),'skipped'),
    lambda s:ET.SubElement(s,'testcase',classname='test_weak',name='weak')
])
def test_incomplete_or_inconsistent_evidence_rejected(tmp_path,change):
    result=check(report(tmp_path,change));assert not result['accepted'] and not result['complete']

def test_failing_exit_cannot_reuse_old_passing_xml(tmp_path):assert not check(report(tmp_path),1)['accepted']
def test_timeout_cannot_reuse_old_passing_xml(tmp_path):assert not check(report(tmp_path),timed_out=True)['accepted']
def test_missing_report_is_incomplete(tmp_path):assert not check(tmp_path/'missing.xml')['complete']
def test_truncated_report_is_incomplete(tmp_path):
    p=tmp_path/'partial.xml';p.write_text('<testsuites>');assert not check(p)['complete']

def test_honest_failed_contract_preserves_weak_result(tmp_path):
    def fail(s):s.set('failures','1');ET.SubElement(s.findall('testcase')[1],'failure')
    result=check(report(tmp_path,fail),1)
    assert result['complete'] and not result['accepted']
    assert result['group_pass']=={'test_weak':True,'test_contract':False}

@pytest.mark.parametrize('attribute,value',[('errors','1'),('failures','1'),('tests','99'),('skipped','1')])
def test_root_aggregate_cannot_contradict_passing_children(tmp_path,attribute,value):
    p=report(tmp_path);tree=ET.parse(p);tree.getroot().set(attribute,value);tree.write(p)
    assert not check(p)['accepted']

def test_nested_suite_aggregate_must_match_descendants(tmp_path):
    p=report(tmp_path);tree=ET.parse(p);root=tree.getroot();child=root[0];root.remove(child)
    parent=ET.SubElement(root,'testsuite',tests='999',failures='1');parent.append(child);tree.write(p)
    assert not check(p)['accepted']

def test_consistent_nested_aggregates_remain_accepted(tmp_path):
    p=report(tmp_path);tree=ET.parse(p);root=tree.getroot();child=root[0];root.remove(child)
    root.set('tests','2');root.set('errors','0');root.set('failures','0');root.set('skipped','0')
    parent=ET.SubElement(root,'testsuite',tests='2',errors='0',failures='0',skipped='0');parent.append(child)
    tree.write(p);assert check(p)['accepted']

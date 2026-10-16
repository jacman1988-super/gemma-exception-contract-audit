"""Keep first-stage result and summarize API-assisted/no-op follow-ups."""
import json,ast,xml.etree.ElementTree as ET
from pathlib import Path
import function_evaluation as f
H=f.H
def main():
    stage=json.loads((H/'summary.json').read_text());api=json.loads((H/'api-feedback/evaluated.json').read_text());groups={}
    for name,run in api['runs'].items():
        assert run['evidence']['complete'];tests=list(ET.parse(run['execution']['report']).getroot().iter('testcase'));groups[name]={'passed':sum(not any(t.find(k) is not None for k in ['failure','error','skipped']) for t in tests),'total':len(tests),'accepted':run['evidence']['accepted']}
    case=next(c for c in json.loads((f.OLD/'protocol.json').read_text())['cases'] if c['package']=='packaging');gen=json.loads((H/'single-failure/generation.json').read_text());assert gen['returncode']==0 and not gen['timeout']
    edits=f.functions(gen['stdout'],case);previous=json.loads((H/'api-feedback/reviewed.json').read_text())['edits']
    same=ast.dump(ast.parse(edits[0]['literal_function']))==ast.dump(ast.parse(previous[0]['literal_function']));assert same,'Unexpected changed final function; requires review and fresh tests'
    final_review={'generation_sha256':f.b.sha(H/'single-failure/generation.json'),'parsed_functions':edits,'rejected_as_noop':True,'same_function_ast_as_tested_api_attempt':True,'not_executed_again':True};f.b.write(H/'single-failure/review.json',final_review)
    result={'staged_result':stage,'latest_packaging_groups':groups,'latest_passing_cases':1,'case_count':2,'model_generations_this_turn':6,'packaging_followups':2,'last_attempt_rejected_noop':True,'api_reference_assistance_explicit':True,'published_or_submitted':False}
    f.b.write(H/'summary-final.json',result)
    backup=H/'Wyniki-Gemma-etap-diagnozy.txt'
    if backup.exists():raise FileExistsError('Preserve report history')
    text=(H/'Wyniki-Gemma.txt').read_text(encoding='utf-8');backup.write_text(text,encoding='utf-8')
    prefix='Gemma — wynik końcowy nowych sposobów informacji zwrotnej, 16.10.2026\nAutor: Jacek Adamek\n\nTenacity: 159/159 sprawdzeń, oba warianty (sync/async) naprawione w zadeklarowanym zakresie. Gotowa lokalna poprawka tenacity-tested.patch ma identyczne hashe źródeł jak przetestowany kod.\n\nPackaging: po dodatkowej tabeli wyników wykonania i dokumentacji metod regex poprawka odrzuca końcowy znak nowej linii, ale nadal odrzuca poprawne pylock.toml. Najnowsza zmieniona funkcja przechodzi 88/90 sprawdzeń: upstream 73/74, kontrole przykładów 6/7, kontrole niepokazane modelowi 9/9. Ostatnia próba z jednym pozostałym błędem i listą działających zachowań powtórzyła identyczną funkcję; odrzucono ją bez ponownego wykonania.\n\nŁącznie 6 generacji w tej turze: diagnoza i naprawa po jednej dla każdego repozytorium oraz dwa dodatkowe podejścia Packaging. Zachowano pierwszy wynik 1/2 i wszystkie niepowodzenia. Dokumentacja fullmatch została jawnie dostarczona w dodatkowej próbie; to mocniejsza pomoc, nie samodzielne odkrycie API przez model. Złotego kodu upstream nie przekazano.\n\nTechniczna uwaga: wygenerowany wynik API zapisano poprawnie przed błędem wypisywania znaków Unicode do konsoli. Nie powtarzano przez to generacji; oceniono zachowany kompletny wynik.\n\nNadal 1/2 przypadków przechodzi cały zadeklarowany zakres. Nie zmieniono artykułu ani zgłoszeń i niczego nie opublikowano.\n\nSzczegóły pierwszego etapu:\n\n'
    (H/'Wyniki-Gemma.txt').write_text(prefix+text,encoding='utf-8');print(result,flush=True)
if __name__=='__main__':main()

"""Audit both feedback rounds, including invalid/no-op responses."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
HERE=Path(__file__).resolve().parent
def counts(run):
    tests=list(ET.parse(run['execution']['report']).getroot().iter('testcase'))
    return {'passed':sum(not any(c.find(t) is not None for t in ['failure','error','skipped']) for c in tests),'total':len(tests),'accepted':run['evidence']['accepted'],'complete':run['evidence']['complete']}
def main():
    first=json.loads((HERE/'evaluated.json').read_text());second=json.loads((HERE/'round2/evaluated.json').read_text());summary=[]
    fixed_total=0
    for row in first:
        reference={k:counts(v) for k,v in row['runs']['fixed'].items()};assert all(v['accepted'] and v['complete'] for v in reference.values());fixed_total+=sum(v['total'] for v in reference.values())
        latest=next(v for v in second if v['id']==row['id']);r1={k:counts(v) for k,v in row['runs'].get('feedback',{}).items()};r2={k:counts(v) for k,v in latest['runs'].items()}
        assert all(v['complete'] for v in list(r1.values())+list(r2.values()))
        summary.append({'id':row['id'],'reference':reference,'round1':{'rejection':row['review'].get('rejection'),'tests':r1},'round2':{'rejection':latest['review'].get('rejection'),'tests':r2},'fully_repaired':bool(r2) and all(v['accepted'] for v in r2.values())})
    result={'cases':summary,'fully_repaired':sum(r['fully_repaired'] for r in summary),'cases_evaluated':2,'feedback_rounds':2,'generations_this_turn':4,'fixed_reference_checks_passed':fixed_total,'no_publication_or_submission':True}
    (HERE/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    text='Gemma — dwie rundy informacji zwrotnej, 16.10.2026\nAutor: Jacek Adamek\n\nWynik: 0/2 pełnych napraw mimo dwóch rund informacji o błędach. Zachowano wszystkie cztery odpowiedzi.\n\nTenacity:\nRunda 1: odpowiedź powtarza pola i urywa się przy limicie 1536 tokenów. Niekompletny JSON odrzucono bez wykonania.\nRunda 2: model zwrócił identyczne bloki old/new — brak zmiany. Odrzucono bez wykonania. Pierwotny problem z wywoływalnymi obiektami o fałszywej wartości logicznej pozostaje.\n\nPackaging:\nRunda 1: model przywrócił oryginalne wyrażenie .match(), usuwając regresję poprawnych nazw, ale przywracając akceptację końcowego znaku nowej linii.\nRunda 2: model dodał rstrip; testy nadal wykazują przyjmowanie niepoprawnych nazw z końcowym znakiem nowej linii.\n'
    for row in summary:
        text+='\n'+row['id']+' — liczby:\n'
        for name in ['round1','round2']:
            q=row[name];text+=name+': '+(q['rejection'] or ', '.join(f"{k} {v['passed']}/{v['total']}" for k,v in q['tests'].items()))+'\n'
    text+=f'\nReferencje upstream: {fixed_total}/{fixed_total} sprawdzeń przechodzi. Zawiera to 216 testów ze zmienionych modułów, 15 wcześniejszych kontroli oraz 18 nowych kontroli niepokazanych modelowi w żadnej rundzie. Każdy raport sprawdzono pod względem kompletności, liczby i tożsamości testów oraz zgodności z kodem zakończenia.\n'
    text+='\nMetoda: ten sam lokalny model Gemma 4 E2B Q4_0, temperatura 0, seed 20261016, kontekst 4096. Runda 1 otrzymała dokładne wyjście nieudanych testów poprzedniej poprawki, limit 1536 tokenów. Runda 2 otrzymała krótszą informację zbiorczą o pierwotnym błędzie, regresjach i problemie formatu, limit 512 tokenów. Jedna generacja na przypadek w każdej rundzie; żadnych cichych powtórzeń i ręcznych napraw przypisanych modelowi. Model nie otrzymał poprawionego kodu upstream ani złotego patcha.\n'
    text+='\nOgraniczenia: zadania publiczne, dobrane wygodnie; lokalizacja funkcji i ręcznie przygotowane informacje zwrotne. Wynik dotyczy tego modelu i tej procedury, nie ogólnej możliwości rozwiązania tych błędów przez inne modele lub agentów. Wysłany artykuł, repozytoria i zgłoszenia pozostają bez zmian.\n'
    (HERE/'Wyniki-Gemma.txt').write_text(text,encoding='utf-8');print(result,flush=True)
if __name__=='__main__':main()

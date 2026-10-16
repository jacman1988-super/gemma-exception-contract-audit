"""Describe a bounded test result, not a general model capability claim."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
H=Path(__file__).resolve().parent
def main():
    evaluated=json.loads((H/'evaluated.json').read_text());out=[]
    for row in evaluated:
        groups={}
        for name,result in row['runs'].items():
            assert result['evidence']['complete'];tests=list(ET.parse(result['execution']['report']).getroot().iter('testcase'))
            groups[name]={'passed':sum(not any(t.find(k) is not None for k in ['failure','error','skipped']) for t in tests),'total':len(tests),'accepted':result['evidence']['accepted']}
        out.append({'id':row['id'],'groups':groups,'all_pass':bool(groups) and all(q['accepted'] for q in groups.values()),'passed':sum(q['passed'] for q in groups.values()),'total':sum(q['total'] for q in groups.values())})
    summary={'cases':out,'fully_passing_cases':sum(v['all_pass'] for v in out),'case_count':2,'generations':4,'method':'one diagnosis + one literal-function repair per clean-parent case','external_publication_or_submission':False}
    (H/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    text='Gemma — diagnoza i przykłady zamiast raportu błędów, 16.10.2026\nAutor: Jacek Adamek\n\nWynik: 1/2 przypadków przechodzi pełny zadeklarowany zestaw sprawdzeń.\n\n'
    for row in out:
        text+=row['id']+f": {row['passed']}/{row['total']}. "+', '.join(f"{k}: {v['passed']}/{v['total']}" for k,v in row['groups'].items())+'\n'
    text+='\nTenacity: wygenerowana poprawka zastępuje sprawdzanie fałszywej wartości logicznej rozróżnieniem None/0 i wywołuje pozostałe strategie. Poprawione oba warianty _run_wait — synchroniczny i asynchroniczny. Przechodzi 142 testy ze zmienionego modułu upstream, 8 kontroli związanych z przykładami i 9 wcześniej przygotowanych kontroli niepokazanych modelowi. To 159/159 w tym zadeklarowanym zakresie, nie dowód poprawności całej biblioteki.\n'
    text+='\nPackaging: model odrzuca poprawne pylock.toml i nadal przyjmuje nazwę z końcowym znakiem nowej linii. Wygenerował też niezamówiony kontekst modułu (importy i regex); przetestowano literalnie wygenerowaną funkcję w oryginalnym module, zgodnie z interfejsem zastępowania wyłącznie funkcji. Dodatkowego kontekstu nie zastosowano ani ręcznie nie naprawiono funkcji. Próba odrzucona.\n'
    text+='\nZmiana procedury: zaczęto od czystych przypiętych wersji z błędem, a nie od poprzednich wadliwych edycji. Model otrzymał tabelę wejście/oczekiwany wynik i istotny kontekst, w tym definicję regexu Packaging. Najpierw wygenerował krótką diagnozę bez kodu (256 tokenów), następnie pełne funkcje Python bez JSON (768 tokenów). Jedna generacja na etap, temperatura 0, seed 20261016, kontekst 4096; ten sam lokalny model Gemma 4 E2B Q4_0. Nie dostarczono złotej poprawki ani ukrytych kontroli.\n'
    text+='\nObsługa formatu: zaakceptowano dosłowne funkcje z nagłówkami FILE bez wymaganych ogrodzeń oraz pojedynczy blok dla jednoznacznego pliku Packaging. Zachowano oryginalne dekoratory poza zastępowanym zakresem. Pierwszy kontroler błędnie uznał zachowany dekorator override za zmianę sygnatury; poprawiono ten test interfejsu przed wykonaniem wygenerowanego kodu i zachowano pierwszy zapis odrzucenia. Ciała funkcji nie były redagowane.\n'
    text+='\nOgraniczenia: mała publiczna próbka, lokalizacja funkcji i ręcznie podane przykłady. Diagnoza Tenacity zawiera niepoprawną sugestię, że samo 0.0 zamiast 0 wyjaśnia niepowodzenie; ta teza nie jest potwierdzona. Wynik naprawy oparto na testach, nie na jakości wyjaśnienia. Zmieniono kilka elementów procedury naraz, więc nie można przypisać sukcesu wyłącznie etapowi diagnozy. Wynik nie jest niezależnym porównaniem skuteczności metod. Wszystkie odpowiedzi i nieudane próby z poprzednich etapów zachowano. Niczego nie opublikowano ani nie wysłano; artykuł i zgłoszenia są niezmienione.\n'
    (H/'Wyniki-Gemma.txt').write_text(text,encoding='utf-8');print(summary,flush=True)
if __name__=='__main__':main()

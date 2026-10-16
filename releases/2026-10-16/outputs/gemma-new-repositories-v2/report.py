"""Summarize checked evidence without changing the submitted writeup."""
import benchmark as b
import json,xml.etree.ElementTree as ET
def counts(path):
    cases=list(ET.parse(path).getroot().iter('testcase'))
    return {'passed':sum(not any(c.find(x) is not None for x in ['failure','error','skipped']) for c in cases),'failed':sum(c.find('failure') is not None for c in cases),'total':len(cases)}
def main():
    rows=json.loads((b.HERE/'evaluated-results.json').read_text());summary=[]
    for row in rows:
        item={'id':row['id'],'complete':all(q['evidence']['complete'] for run in row['runs'].values() for q in run.values()),'variants':{v:{k:counts(q['execution']['report']) for k,q in run.items()} for v,run in row['runs'].items()}}
        def failures(v):
            root=ET.parse(row['runs'][v]['full']['execution']['report']).getroot()
            return {(c.get('classname'),c.get('name')) for c in root.iter('testcase') if c.find('failure') is not None}
        item['original_failure_still_present']=bool(failures('parent')&failures('model'))
        item['new_failures_introduced']=sorted(failures('model')-failures('parent'))
        summary.append(item)
    assert all(x['complete'] for x in summary)
    b.write(b.HERE/'summary.json',{'cases':summary,'fully_repaired':0,'cases_evaluated':2,'initial_environment_timeouts':2,'no_publication_or_submission':True})
    text='Gemma — nowe repozytoria, 16.10.2026\nAutor: Jacek Adamek\n\nWynik: 0/2 pełnych napraw. Oficjalne poprawki przechodzą wszystkie 231 sprawdzeń (216 testów z dwóch zmienionych modułów upstream i 15 dodatkowych kontroli). Obie wygenerowane poprawki odrzucono.\n\n'
    text+='Tenacity: 141/142 testów upstream i 4/8 dodatkowych kontroli. Model pozostawił „not self.wait”, więc nadal pomija wywoływalne obiekty o fałszywej wartości logicznej. Nie naprawił także odpowiednika asynchronicznego.\n\n'
    text+='Packaging: 73/74 testy upstream i 6/7 dodatkowych kontroli. Model usuwa objaw dotyczący końcowego znaku nowej linii, ale odrzuca poprawne nazwy pylock.spam.toml i pylock.prod.toml. Sam test pierwotnego błędu zaakceptowałby tę wadliwą poprawkę; pełny moduł ją odrzuca.\n\n'
    text+='Metoda: przypięte rewizje publicznych repozytoriów; oficjalne testy z poprawionej wersji uruchomione na poprawionym i poprzednim kodzie. Gemma 4 E2B Q4_0, ten sam zapisany model, temperatura 0, seed 20261016, kontekst 4096, limit 512 tokenów. Jedna próba w działającym środowisku na przypadek. Model widział publiczny opis commitu i zlokalizowane funkcje z wersji błędnej, bez oficjalnej poprawki i testów. Dodatkowe kontrole powstały po próbach referencyjnych, przed odczytaniem odpowiedzi modelu.\n\n'
    text+='Problemy techniczne zachowane: brak tomli-w przerwał pierwszą kolekcję Packaging; po instalacji 1.2.0 test odtworzono. Dwie próby inferencji w sandboxie przekroczyły 180 s bez odpowiedzi. Neutralna diagnostyka również nie działała w sandboxie, a poza nim zakończyła się w kilka sekund. Powtórzono niezmienione zadania poza sandboxem, bez informacji zwrotnej o naprawach. Testy asyncio także uruchomiono poza sandboxem po zawieszeniu pierwszej kontroli.\n\n'
    text+='Ograniczenia: tylko dwa wygodnie dobrane publiczne przypadki, lokalizacja na podstawie miejsc zmian, opis commitu może podpowiadać rozwiązanie. To rozszerzenie badania walidacji napraw, nie dwa nowe przypadki kontraktów wyjątków ani niezależny szacunek ogólnej skuteczności Gemma. Nie zmieniono wysłanego artykułu ani zgłoszenia.\n\nŹródła:\n'
    for c in json.loads((b.HERE/'protocol.json').read_text())['cases']:text+=c['url']+'\n'
    (b.HERE/'Wyniki-Gemma.txt').write_text(text,encoding='utf-8');print(summary,flush=True)
if __name__=='__main__':main()

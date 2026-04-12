# Noteeli Architecture

Ten dokument opisuje aktualny układ aplikacji i konwencje, których warto się trzymać przy dalszym rozwoju projektu.

## Cel

Projekt to uproszczony edytor notatek Markdown inspirowany Obsidianem:

- FastAPI odpowiada za routing HTTP i API
- Mako renderuje widoki HTML po stronie serwera
- SQLite przechowuje ustawienia aplikacji i manualny order elementów
- frontend w `static/app.js` obsługuje drzewo plików, modale, edycję i drag and drop

## Główne zasady układu

Najważniejsza zasada: projekt jest organizowany domenowo, a nie warstwowo.

To oznacza, że kod związany z jednym obszarem funkcjonalnym trzymamy razem:

- routing
- logika domenowa
- schematy danych
- widoki Mako specyficzne dla tej domeny

Zamiast jednego wspólnego katalogu typu `routers/`, `services/`, `templates/` dla całej aplikacji, preferowany jest układ z podziałem na domeny.

## Struktura katalogów

```text
app/
  core/
    config.py
    templates.py
  domains/
    auth/
      router.py
      service.py
      views/
        login.mako
    preferences/
      repository.py
      schemas.py
      service.py
    workspace/
      router.py
      schemas.py
      service.py
      views/
        index.mako
  views/
    base.mako
static/
  app.css
  app.js
content/
  ...
```

## Co gdzie trafia

### `app/core`

Kod wspólny dla całej aplikacji:

- `config.py` trzyma ustawienia i ścieżki runtime
- `templates.py` konfiguruje lookup Mako i renderowanie

To miejsce jest dla rzeczy frameworkowych i współdzielonych, nie dla logiki biznesowej.

### `app/domains/auth`

Odpowiada za:

- logowanie Google
- bypass autoryzacji dla ruchu lokalnego
- widok logowania

Jeśli pojawią się nowe ekrany związane z autoryzacją, powinny trafić do `app/domains/auth/views/`.

### `app/domains/preferences`

Odpowiada za trwałe ustawienia aplikacji:

- katalog notatek
- tryb sortowania
- tryb jasny/ciemny
- manualny order elementów w drzewie

Podział odpowiedzialności:

- `schemas.py` definiuje modele wejścia i wyjścia
- `repository.py` rozmawia bezpośrednio z SQLite
- `service.py` zawiera logikę aplikacyjną wokół repozytorium

### `app/domains/workspace`

To główna domena aplikacji. Odpowiada za:

- budowę drzewa katalogów i plików
- odczyt i zapis Markdown
- tworzenie nowych katalogów i plików
- reorder elementów
- główny widok aplikacji
- API używane przez frontend

Podział odpowiedzialności:

- `router.py` mapuje requesty HTTP na operacje domenowe
- `service.py` zawiera logikę pracy na plikach i walidację ścieżek
- `schemas.py` opisuje payloady i odpowiedzi API
- `views/index.mako` renderuje główny ekran workspace

### `app/views`

Tutaj trzymamy tylko widoki wspólne dla wielu domen.

Obecnie jest tam:

- `base.mako`

Jeśli jakiś widok jest używany tylko przez jedną domenę, powinien siedzieć w `views/` tej domeny, a nie tutaj.

## Dlaczego widoki Mako są przy domenach

To jest celowa decyzja architektoniczna.

Korzyści:

- łatwiej zrozumieć cały feature, bo routing, widok i logika są blisko siebie
- łatwiej pracować z AI, bo mniej trzeba tłumaczyć gdzie czego szukać
- łatwiej usuwać lub rozbudowywać pojedynczą domenę
- mniejsze ryzyko, że widoki staną się anonimową, płaską listą plików

Reguła praktyczna:

- widok specyficzny dla domeny: `app/domains/<nazwa>/views/`
- layout współdzielony: `app/views/`

## Routing

Każda domena ma własny `router.py`.

Router:

- powinien być cienki
- powinien mapować HTTP na operacje domenowe
- nie powinien zawierać ciężkiej logiki biznesowej ani logiki persistence

Jeśli handler zaczyna robić dużo pracy na plikach, SQL albo walidować wiele reguł biznesowych, to ta logika powinna wylądować w `service.py`.

## Serwisy

`service.py` to miejsce na logikę aplikacyjną i domenową.

Przykłady:

- walidacja ścieżek względem `content_root`
- budowanie drzewa katalogów
- tworzenie pliku Markdown z automatycznym `.md`
- sprawdzanie, czy reorder jest poprawny

Serwis może korzystać z repozytorium, ale router nie powinien gadać z repozytorium bezpośrednio.

## Repozytorium i SQLite

Bezpośredni dostęp do SQLite powinien być skupiony w `preferences/repository.py`.

To daje:

- jedno miejsce do zmian schematu i SQL
- prostsze testowanie logiki wyżej
- jasny podział między persistence a logiką domenową

Jeśli w przyszłości pojawią się nowe tabele dla innych domen, najlepiej dodać repozytorium w odpowiedniej domenie, zamiast wrzucać wszystko do jednego wspólnego pliku.

## Frontend

Frontend jest obecnie prosty i świadomie centralny:

- `static/app.js`
- `static/app.css`

To jest akceptowalne na obecnym etapie, bo aplikacja ma jeden główny ekran.

Jeśli UI urośnie, sensowny kierunek to podział na moduły według odpowiedzialności, na przykład:

- drzewo plików
- modale
- ustawienia
- edytor

Na razie jednak prostota jednego pliku JS i jednego CSS jest uzasadniona.

## Konwencje dalszego rozwoju

Przy dodawaniu nowego feature:

1. Najpierw określ domenę, do której należy.
2. Jeśli feature jest specyficzny dla jednej domeny, trzymaj routing, widok i logikę blisko niej.
3. Jeśli coś ma być współdzielone między domenami, dopiero wtedy przenieś to do `core/` albo `app/views/`.
4. Nie wkładaj logiki biznesowej do szablonów Mako.
5. Nie wkładaj ciężkiej logiki do routerów.
6. Nie mieszaj SQL z warstwą HTTP.

## Wskazówki dla AI i nowych osób

Jeśli chcesz zmienić zachowanie aplikacji, najczęściej szukaj w tej kolejności:

1. `app/domains/workspace/router.py` albo `app/domains/auth/router.py`
2. odpowiadający `service.py`
3. odpowiadający widok Mako w `views/`
4. `static/app.js`, jeśli zmiana dotyczy interakcji w przeglądarce
5. `preferences/repository.py`, jeśli zmiana dotyczy trwałych ustawień

Jeśli dodajesz nowy ekran:

- najpierw zdecyduj, do której domeny należy
- dodaj widok Mako w `views/` tej domeny
- podepnij go przez router tej domeny

## Czego unikać

- powrotu do jednego globalnego katalogu `templates/` dla wszystkich widoków domenowych
- wrzucania całej logiki do `app.js`, jeśli UI zacznie wyraźnie rosnąć
- bezpośredniego dostępu do SQLite z routerów
- mieszania logiki auth z workspace
- tworzenia "utils.py" bez wyraźnej odpowiedzialności domenowej

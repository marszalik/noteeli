# Noteeli

Webowa aplikacja w Pythonie oparta o FastAPI i szablony Mako. Wyświetla strukturę katalogu z notatkami, pozwala przeglądać pliki Markdown i edytować je w trybie WYSIWYG.

Opis architektury i konwencji projektu jest w `ARCHITECTURE.md`.

## Funkcje

- drzewo katalogów i plików w sidebarze
- podgląd i edycja plików Markdown po prawej stronie
- logowanie Google dla ruchu spoza `127.0.0.1`, `localhost` i `::1`
- lokalny bypass logowania dla adresów developerskich
- SQLite w `.noteeli/noteeli.sqlite3` na ustawienia i manualny order drzewa
- konfiguracja katalogu z notatkami i sortowania z poziomu UI

## Uruchomienie

1. Skopiuj `.env.example` do `.env` i uzupełnij wartości.
2. Zainstaluj zależności:

```bash
python3 -m venv .venv
./.venv/bin/pip install -e ".[dev]"
```

Albo przez PDM:

```bash
pdm install -d
```

3. Uruchom serwer:

```bash
./.venv/bin/uvicorn app.main:app --reload
```

Albo przez PDM:

```bash
pdm run dev
```

4. Otwórz aplikację pod adresem `http://127.0.0.1:8000`.

## Zmienne środowiskowe

- `NOTEELI_CONTENT_ROOT` - katalog bazowy z notatkami
- `NOTEELI_DATA_DIR` - katalog na bazę SQLite i dane aplikacji
- `NOTEELI_SESSION_SECRET` - sekret sesji
- `NOTEELI_GOOGLE_CLIENT_ID` - identyfikator klienta OAuth Google
- `NOTEELI_GOOGLE_CLIENT_SECRET` - sekret klienta OAuth Google

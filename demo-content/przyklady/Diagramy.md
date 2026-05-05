# Diagramy w Noteeli

Noteeli renderuje **Mermaid** (lokalnie, po stronie klienta) oraz
**PlantUML** (przez publiczny renderer plantuml.com).

## Schemat blokowy (flowchart)

```mermaid
flowchart LR
    A[Klient] -->|HTTP| B(Nginx)
    B --> C{Domena?}
    C -->|app.noteeli.com| D[Noteeli prod :8090]
    C -->|demo.noteeli.com| E[Noteeli demo :8091]
    D --> F[(SQLite)]
    D --> G[(Pliki .md)]
    E --> H[(Demo content)]
```

## Sekwencja

```mermaid
sequenceDiagram
    participant U as Użytkownik
    participant N as Noteeli
    participant S as Storage
    U->>N: Otwórz notatkę
    N->>S: read_text(path)
    S-->>N: zawartość markdown
    N-->>U: WYSIWYG render
    U->>N: Edycja (autosave)
    N->>S: write_text(path, content)
    S-->>N: OK
    N-->>U: ✓ Zapisano
```

## Diagram ER

```mermaid
erDiagram
    USER ||--o{ NOTE : owns
    USER {
        int id
        string email
    }
    NOTE ||--o{ ASSET : embeds
    NOTE {
        int id
        string path
        text content
    }
    ASSET {
        int id
        string filename
        bytes data
    }
```

## Gantt

```mermaid
gantt
    title Roadmap Noteeli
    dateFormat YYYY-MM-DD
    section Core
    MVP                 :done,   m1, 2026-01-01, 30d
    SFTP backend        :done,   m2, after m1, 14d
    Google Drive        :active, m3, after m2, 21d
    section UX
    Multi-theme         :done,   t1, 2026-04-01, 14d
    Markdown styles     :done,   t2, after t1, 7d
    iPad polishing      :        t3, after t2, 14d
```

## PlantUML — opcjonalnie

```plantuml
@startuml
actor User
participant "Noteeli" as N
database "SQLite" as DB

User -> N: GET /api/tree
N -> DB: SELECT prefs
DB -> N: row
N -> User: tree JSON
@enduml
```

> 💡 Gdy edytujesz dokument w trybie WYSIWYG, diagramy renderują się
> na żywo. Pole `mermaid` w nagłówku bloku kodu mówi edytorowi,
> że ma to zrenderować jako diagram zamiast pokazywać kod.

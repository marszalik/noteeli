# Diagrams in Noteeli

Noteeli renders **Mermaid** (locally, in the browser) and **PlantUML**
(via the public plantuml.com renderer).

## Flowchart

```mermaid
flowchart LR
    A[Client] -->|HTTP| B(Nginx)
    B --> C{Domain?}
    C -->|app.noteeli.com| D[Noteeli prod :8090]
    C -->|demo.noteeli.com| E[Noteeli demo :8092]
    D --> F[(SQLite)]
    D --> G[(Markdown files)]
    E --> H[(Demo content)]
```

## Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant N as Noteeli
    participant S as Storage
    U->>N: Open note
    N->>S: read_text(path)
    S-->>N: markdown content
    N-->>U: WYSIWYG render
    U->>N: Edit (autosave)
    N->>S: write_text(path, content)
    S-->>N: OK
    N-->>U: ✓ Saved
```

## ER diagram

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
    title Noteeli roadmap
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

## PlantUML — optional

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

> 💡 When you edit a document in WYSIWYG mode, diagrams render live.
> The `mermaid` language hint on a code block tells the editor to
> render it as a diagram instead of showing the source.

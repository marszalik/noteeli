# Formatowanie tekstu

## Nagłówki

W Markdown nagłówki tworzysz znakami `#`. Im więcej krzyżyków, tym mniejszy nagłówek.

### Trzeci poziom

#### Czwarty poziom

##### Piąty

###### Szósty

## Tekst

Możesz użyć **pogrubienia**, *kursywy*, ~~przekreślenia~~, oraz `kodu inline`.

> "Cytat blokowy też wygląda dobrze. Notatki są czytane częściej niż pisane,
> więc warto inwestować w czytelność." — Anon

## Listy

### Numerowana

1. Pierwszy punkt
2. Drugi punkt
   1. Z zagnieżdżeniem
   2. Drugi podpunkt
3. Trzeci punkt

### Nienumerowana

- Mleko
- Chleb
- Jajka
  - Białe
  - Brązowe

### Lista zadań (task list)

- [x] Zaplanować tydzień
- [x] Napisać pierwszy draft
- [ ] Wysłać do recenzji
- [ ] Opublikować

## Linki

[Strona Noteeli](https://noteeli.com) — dowiedz się więcej.

## Kod inline i bloki

Inline: użyj `console.log("hello")` żeby zobaczyć w konsoli.

Blok kodu z podpowiedzią języka:

```python
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

print(list(fib(10)))
```

```javascript
const greet = (name) => `Cześć, ${name}!`;
console.log(greet("Eli"));
```

## Tabela

| Funkcja | Status | Notatka |
|---|---|---|
| Markdown WYSIWYG | ✅ | Toast UI Editor |
| Diagramy | ✅ | Mermaid + PlantUML |
| Office preview | ✅ | docx / xlsx / pptx |
| Drag & drop obrazków | ✅ | Z auto-kopią |
| Multi-platform | ✅ | macOS / Linux / iPad |

## Pozioma linia

Trzy myślniki na osobnej linii dają linię poziomą:

---

Pod linią mogą być kolejne sekcje.

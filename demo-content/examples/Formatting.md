# Text formatting

## Headings

In Markdown you create headings with `#`. The more hashes, the smaller
the heading.

### Third level

#### Fourth level

##### Fifth

###### Sixth

## Text

You can use **bold**, *italic*, ~~strikethrough~~, and `inline code`.

> "Block quotes look good too. Notes are read more often than they are
> written, so it pays to invest in legibility." — Anon

## Lists

### Numbered

1. First item
2. Second item
   1. With a nested entry
   2. Second sub-item
3. Third item

### Bulleted

- Milk
- Bread
- Eggs
  - White
  - Brown

### Task list

- [x] Plan the week
- [x] Write the first draft
- [ ] Send for review
- [ ] Publish

## Links

[Noteeli website](https://noteeli.com) — find out more.

## Inline code and code blocks

Inline: use `console.log("hello")` to print to the console.

Fenced code block with a language hint:

```python
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

print(list(fib(10)))
```

```javascript
const greet = (name) => `Hi, ${name}!`;
console.log(greet("Eli"));
```

## Table

| Feature | Status | Note |
|---|---|---|
| Markdown WYSIWYG | ✅ | Toast UI Editor |
| Diagrams | ✅ | Mermaid + PlantUML |
| Office preview | ✅ | docx / xlsx / pptx |
| Image drag & drop | ✅ | With auto-copy |
| Multi-platform | ✅ | macOS / Linux / iPad |

## Horizontal rule

Three dashes on their own line make a horizontal line:

---

You can put more sections below the rule.

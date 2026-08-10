# Noteeli User Manual

Everything you can do in Noteeli, explained for the person using it — not the
person developing it. For installation and hosting, see the
[README](./README.md); for the full feature-by-feature inventory with test
coverage, see [functionalities.md](./functionalities.md).

## Contents

1. [First steps](#1-first-steps)
2. [The workspace at a glance](#2-the-workspace-at-a-glance)
3. [Files and folders](#3-files-and-folders)
4. [Writing notes](#4-writing-notes)
5. [Saving and autosave](#5-saving-and-autosave)
6. [Images and attachments](#6-images-and-attachments)
7. [Diagrams](#7-diagrams)
8. [Beyond Markdown: JSON, code, previews](#8-beyond-markdown-json-code-previews)
9. [Publishing notes publicly](#9-publishing-notes-publicly)
10. [Git: history, sync and team checkpoints](#10-git-history-sync-and-team-checkpoints)
11. [Personalisation](#11-personalisation)
12. [Where your notes live (storage)](#12-where-your-notes-live-storage)
13. [Accounts and access](#13-accounts-and-access)
14. [For administrators](#14-for-administrators)

---

## 1. First steps

Open your Noteeli instance in the browser. Depending on how it is set up you
will either land straight in the workspace (local access) or on a login page
(Google sign-in, or a username/password form if the admin configured one).

The first thing you see is the **file tree** on the left — these are real
folders and real files on the configured storage, not abstract "notes".
Anything you create in Noteeli exists as a plain file you could open with any
other tool, and anything you drop into the notes folder outside of Noteeli
shows up in the tree.

Click a Markdown file to start editing. That's it — there is no import step.

## 2. The workspace at a glance

- **Sidebar (left)** — the file tree, a search toggle, new-file / new-folder
  buttons, a refresh button, and at the bottom a small **version chip**
  (click it to read the release notes for the version you're running).
- **Topbar** — the name of the open file, save/reload buttons, editor font
  size controls, the profile quick-switcher, the **git menu** (if the
  workspace is a git repository), and the account menu (settings, logout).
- **Editor (center)** — the right editor for the file type opens
  automatically: Markdown WYSIWYG, JSON form editor, code editor with syntax
  highlighting, or a read-only preview for images, PDFs and Office files.
- **Status line** — short feedback after every action ("Saved.",
  "Autosaved.", error messages).

The sidebar can be collapsed (hamburger), pinned, and resized by dragging its
edge; on phones it becomes an overlay. Noteeli remembers your sidebar width,
the last file you had open, and reopens it on the next visit.

## 3. Files and folders

**Creating.** Use the sidebar toolbar buttons or right-click a folder →
*New file* / *New folder*. Markdown files get `.md` appended automatically if
you don't type an extension. On tablets and phones, long-press a row to open
the context menu.

**The context menu** (right-click any row) is the hub for file operations:
open, focus on folder, upload here, new file/folder, download, copy path,
rename, duplicate, refresh, delete — plus publish and git actions described
in their own sections below.

- **Rename** keeps the original extension unless you explicitly type a new
  one — renaming `photo.png` to `holiday` gives you `holiday.png`, not a
  broken file.
- **Delete** asks you to click twice (the button arms itself first), so a
  stray click never destroys a folder.
- **Duplicate** creates `name_1.md`, `name_2.md`, … next to the original.
- **Download** fetches a single file as-is; downloading a folder gives you a
  ZIP of the whole subtree.

**Moving and ordering.** Drag rows in the tree to move files between folders.
With *manual* sort mode (Settings → Appearance) you can also drag to reorder
within a folder and the order is remembered; *alphabetical* keeps things
sorted for you.

**Finding things.** The magnifier icon opens a filter box — type a name
fragment and the tree narrows down, auto-expanding folders that contain
matches. To work inside one project only, right-click a folder → *Focus* and
the tree scopes itself to that subtree (a bar appears to exit the scope).

**Hidden files.** Dotfiles (`.git/`, `.megaignore`, …) are hidden by default;
a toggle in the sidebar shows them when you need them.

**Uploading.** Right-click a folder → *Upload*, or use the upload panel: drop
several files at once. Files that already exist at the target are skipped and
reported, never silently overwritten.

## 4. Writing notes

Markdown files open in a **WYSIWYG editor** — headings, lists, tables, task
lists, links and images render as you type, with a toolbar for formatting and
undo/redo buttons.

Prefer raw Markdown? The **mode button** in the topbar cycles through four
views of the same note: **WYSIWYG → Markdown** (source view) **→ Kanban**
(board, see below) **→ Text** (plain-text editor). Your WYSIWYG/Markdown
choice is remembered per browser; Kanban and Text are picked per file. All
views edit the same plain `.md` file — there is no proprietary format
underneath.

The editor font size can be adjusted from the topbar (12–28 px) and is
remembered. Task-list checkboxes, tables and code blocks all follow the
active theme.

**Links between notes.** A relative Markdown link to another note
(`[plan](harmonogram/zjazdy.md)`) opens that note in Noteeli:
**Ctrl/Cmd+click** in the editor (a plain click keeps editing), plain
click on published pages. External links open in a new tab.
Obsidian users: switch off *Use [[Wikilinks]]* in Settings → Files &
Links so Obsidian writes standard Markdown links — they then work
everywhere (Noteeli, GitHub, Azure DevOps) instead of only in Obsidian.

**Reload from disk.** If a file changed outside your editor (another person,
a script, a git pull), the reload button in the topbar re-reads it — and
warns you first if you have unsaved edits.

### Kanban boards

A kanban board in Noteeli is a **plain Markdown file** — the same format as
Obsidian's Kanban plugin, so boards travel freely between both apps:

```markdown
---
kanban-plugin: board
---

## To do

- [ ] Prepare the course
    - [ ] Write the syllabus
    - [ ] Module 1 slides

## In progress

## Done
```

Any `.md` file whose frontmatter contains `kanban-plugin:` opens straight
onto the board: `## ` headings become columns, list items become cards.

**Creating a board** is just switching the view: make a regular new file
(or open any note) and click the topbar mode button until it reads
**Kanban**. Existing `## ` headings turn into columns immediately; an empty
note gets three default columns. Merely switching views changes nothing on
disk — the `kanban-plugin` frontmatter is written together with your first
real board edit, and from then on the file opens as a board by itself.
Boards made in Obsidian work as-is.

**Subtasks are cards too.** A nested list item renders as its own card,
indented under its parent with a connecting line — nest as deep as you like.
The parent shows a progress chip (`1/3`) and **cannot leave its column while
it still has subtasks**: move (or finish) the subtasks first. A subtask
dragged to another column becomes a standalone card — in the file it simply
moves out of the nested list, so the Markdown stays clean.

On the board you can drag cards between and within columns (drop onto a
card's middle to nest it as a subtask), tick checkboxes, click a card to edit
its text, add cards, subtasks and columns, and delete cards. Everything else
in the file — frontmatter, notes under a card, Obsidian's settings block —
is preserved untouched. Renaming columns, archiving and anything the board
view doesn't cover is one toggle away in the Markdown view.

Boards save through the regular autosave/save path, so git history,
checkpoints and publishing work exactly as for any other note. (Drag & drop
needs a mouse — on touch devices use the Markdown view.)

## 5. Saving and autosave

- **Manual save** — `Ctrl+S` or the Save button. The button stays disabled
  until you actually change something.
- **Autosave** — enable it in Settings → Editor. Noteeli then saves about a
  second after you pause typing ("Autosaved." appears in the status line) and
  hides the Save button entirely. Autosave is a personal setting: it follows
  your account, not the whole instance.

After every save the git indicators (see [section 10](#10-git-history-sync-and-team-checkpoints))
update automatically, so the change counter in the topbar always reflects
reality without reloading the page.

> **Heads-up for shared workspaces:** if two people edit the *same file* at
> the same time, the last save wins. Until conflict detection ships, agree on
> ownership of a file before editing it together.

## 6. Images and attachments

Three ways to get an image into a note:

1. **Paste** from the clipboard straight into the editor.
2. **Drag a file** from your desktop into the editor.
3. **Drag an image from the sidebar tree** into the editor — it embeds a
   reference to the existing file.

Where uploaded images land is configurable (Settings → Images):

- **Same folder as the note** — image sits next to the `.md` file.
- **Subfolder** — e.g. `assets/`; Noteeli creates it as needed. When you drag
  an image from elsewhere in the tree, Noteeli copies it into the configured
  location automatically (Obsidian-style), so notes stay portable.

`.excalidraw` sketches embed via their exported `.excalidraw.png` when one
exists next to the source file.

## 7. Diagrams

Fenced code blocks with `mermaid` render as live diagrams in both WYSIWYG
and source preview; the diagram theme follows the app theme. PlantUML blocks
render too (via the public plantuml.com server — note that this sends the
diagram source to that server). The toolbar has an *Insert diagram* dropdown
with ready-made templates for both.

## 8. Beyond Markdown: JSON, code, previews

- **JSON** (`.json`, `.jsonc`, `.json5`) opens in a form-style editor with
  expandable nodes; files that aren't valid JSON fall back to a raw code view
  so you can fix them. Saving pretty-prints valid JSON.
- **Code and plain text** (~30 languages: Python, JS/TS, Go, Rust, shell,
  SQL, YAML, …) opens in a code editor with syntax highlighting. Pick one of
  12 highlight themes — or *auto*, which follows the app theme. Unknown text
  files up to 1 MB open as plain text.
- **Read-only previews**: images, PDFs, Word documents (`.docx`) rendered as
  formatted text, and Excel sheets (`.xlsx`/`.xlsm`) rendered as tables — one
  per sheet.

## 9. Publishing notes publicly

Right-click a file or folder → **Publish**. Noteeli generates a public link
(`/{id}/{slug}`) that works without login and shows a read-only view.
Publishing a folder exposes that subtree only — siblings and parents stay
private, and path tricks are rejected server-side.

Published rows get a **globe badge** in the tree. The context menu then
offers *Copy public link* and *Unpublish*. When more than one item is
published, every shared page's sidebar shows a **Published notes**
section (file names only) so visitors can move between them. Renaming or deleting a published
file cleans up its public entry automatically — anyone opening the old link
afterwards sees a friendly "no longer published" notice.

## 10. Git: history, sync and team checkpoints

If the notes folder is a git repository (local or over SFTP), git features
light up automatically — no configuration inside Noteeli.

**Seeing changes.** Files with uncommitted changes get a status letter badge
in the tree (M modified, A added, U untracked, …) and folders containing
changes get a dot. The topbar **git menu button** shows a counter with the
number of changed files; these indicators refresh on their own after every
save and autosave.

**The git menu** shows the current branch, how far you are ahead/behind the
remote (`↑2 ↓1`), the list of changed files, a commit message box and the
operations: **Commit**, **Commit & Push**, **Fetch**, **Pull**, **Push**.
Remote and credentials are whatever the repository already has configured —
Noteeli doesn't manage them.

**Committing one thing.** Right-click a file or folder → *Commit (this
item)* or *Commit & push (this item)* to commit just that path with its own
message.

**Who made a commit?** When you're signed in with a real account, commits
made through Noteeli are signed with your name and email — history and blame
in a shared workspace attribute work to the right person. Local/anonymous
access uses the repository's own git identity.

**File history and line authors (blame).** With a file open, the git
menu has a **History & authors** entry (labeled with the file's name)
that opens the history panel:

- The **History** tab lists every commit that touched the file — who,
  when, and the commit message (renames are followed). Click a commit to
  unfold exactly what it changed, highlighted **word by word**: added
  words green, removed words struck through. Word-level matters for
  notes — rewording a sentence shows just the changed words, not two
  walls of "line removed / line added".
- The **Line authors** tab shows the file with a gutter telling you who
  wrote each line and how long ago, color-coded per person, with fresher
  lines tinted stronger — a quick "what happened here recently" heatmap.
  Lines you've saved but that aren't committed yet are marked as such.

**Silent checkpoints (optional, for teams).** With
`NOTEELI_GIT_AUTOCOMMIT=1` the server commits your work for you: every saved
file is queued, and once it has been quiet for a few minutes (default 5,
configurable) it is committed automatically — signed by whoever saved it
last, one commit per author. You'll see it as `Checkpoint: filename.md` in
the history. Nobody has to remember to commit, and `git log`/`git blame`
still tell the truth about who wrote what. Pending checkpoints are committed
immediately when the server shuts down, so restarts lose nothing. By
default checkpoints commit but don't push. Add
`NOTEELI_GIT_AUTOCOMMIT_PUSH=1` and each checkpoint is also pushed to the
repo's remote — handy when a private GitHub/GitLab repo is your source of
truth. If someone pushed to the remote in the meantime, clean changes are
replayed automatically; a genuine content conflict is *parked* (nothing
lost, the ↑/↓ counters in the git menu show it) for you to resolve once
with Pull.

## 11. Personalisation

Settings (account menu → Settings) are organised in five tabs: **Source**,
**Appearance**, **Editor**, **Images**, **Profiles**.

- **Themes** — Light, Dark, Noteeli, Webnote, Obsidian. The browser status
  bar tint follows along on mobile.
- **Languages** — English, Polish, Spanish, German, Russian.
- **Editor** — autosave toggle, font size.
- **Images** — upload location (see [section 6](#6-images-and-attachments)).
- **Profiles** — save the current preferences as a named set, then switch
  between sets from the topbar quick-switcher (handy for e.g. "writing" vs
  "reviewing" setups, or two different note roots).

On a shared instance, personal settings (theme, language, font, autosave,
sort mode, profiles) are **per account** — your dark theme doesn't restyle
your colleagues. Storage settings (which folder/server the instance points
at) are shared instance-wide.

## 12. Where your notes live (storage)

Settings → Source switches the backend:

- **Local folder** — the default; a directory on the server running Noteeli.
  Use *Browse* to pick it.
- **SFTP / SSH** — notes live on another machine; Noteeli connects with
  host/port/username/password. You choose whether the password is remembered
  (stored in Noteeli's database — the UI warns you) or asked for per session.
  Git works over SFTP too, executed on the remote machine.
- **Google Drive** — connect a Drive folder via OAuth. No git on Drive.

Administrators can **lock the workspace** (`NOTEELI_LOCK_WORKSPACE=1`): the
source and root are then pinned, the Source tab disappears, and the directory
picker can't wander above the workspace root — the right setup when sharing
one folder with a group.

## 13. Accounts and access

How you sign in depends on the instance configuration:

- **Google sign-in** — the admin lists allowed emails
  (`NOTEELI_ALLOWED_GOOGLE_EMAILS`); Gmail dot-variants are treated as the
  same account, so `jan.kowalski@gmail.com` and `jankowalski@gmail.com` both
  work.
- **Password login** — a single username/password pair set in the server
  config (`NOTEELI_LOCAL_USERNAME` / `NOTEELI_LOCAL_PASSWORD`).
- **Localhost** — requests from the machine Noteeli runs on skip login
  entirely (development convenience).
- **Demo mode** — a public, read-only showcase: everyone is a guest, every
  write is politely refused, git is off.

Log out from the account menu (top right).

## 14. For administrators

Deployment, the installer and env-file basics are in the
[README](./README.md). The variables most relevant to day-to-day use:

| Variable | What it does |
|---|---|
| `NOTEELI_CONTENT_ROOT` | Default notes directory |
| `NOTEELI_DATA_DIR` | Where the SQLite preferences DB and logs live |
| `NOTEELI_SESSION_SECRET` | Session cookie signing key |
| `NOTEELI_GOOGLE_CLIENT_ID` / `_SECRET` | Google OAuth credentials |
| `NOTEELI_ALLOWED_GOOGLE_EMAILS` | Comma/space-separated login allowlist |
| `NOTEELI_LOCAL_USERNAME` / `_PASSWORD` | Built-in password login |
| `NOTEELI_LOCK_WORKSPACE=1` | Pin storage source + root (shared instances) |
| `NOTEELI_GIT_AUTOCOMMIT=1` | Silent checkpoint commits (see [§10](#10-git-history-sync-and-team-checkpoints)) |
| `NOTEELI_GIT_AUTOCOMMIT_IDLE_SECONDS` | Idle window before a checkpoint (default 300) |
| `NOTEELI_DEMO_MODE=1` | Read-only public demo |
| `NOTEELI_LOG_RETENTION_DAYS` | Rotating file logs retention (default 14) |

Logs rotate daily under `<data_dir>/logs/noteeli.log` and cover the app plus
the web server's access/error output.

**Recommended setup for a small team sharing one notes repo:** Google login
with an allowlist, `NOTEELI_LOCK_WORKSPACE=1`, a git-initialised notes folder
with a configured remote, and `NOTEELI_GIT_AUTOCOMMIT=1` — everyone's work is
then continuously versioned and correctly attributed with zero ceremony.

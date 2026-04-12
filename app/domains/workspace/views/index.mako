<%inherit file="/views/base.mako"/>

<%def name="page_title()">Noteeli</%def>

<%def name="head_extra()">
  <link rel="stylesheet" href="https://uicdn.toast.com/editor/latest/toastui-editor.min.css" />
</%def>

<%def name="content()">
  <div
    class="app-shell"
    data-config='${frontend_config | n}'
    data-theme-mode="${preferences.theme_mode}"
    data-editor-font-size="${preferences.editor_font_size}"
  >
    <aside class="sidebar">
      <div class="brand-block">
        <span class="eyebrow">FastAPI + Mako</span>
        <h1>Noteeli</h1>
        <p id="content-root-display" class="sidebar-path">${content_root}</p>
      </div>

      <div class="sidebar-actions">
        <div class="sidebar-toolbar">
          <button id="new-file" class="button button-secondary" type="button">Nowy plik</button>
          <button id="new-directory" class="button button-secondary" type="button">Nowy katalog</button>
          <button id="refresh-tree" class="button button-secondary" type="button">Odswiez drzewo</button>
        </div>
      </div>

      <div id="tree-root" class="tree-root" aria-live="polite"></div>
    </aside>

    <main class="workspace-panel">
      <header class="workspace-topbar">
        <div>
          <div class="label">Wybrany plik</div>
          <h2 id="current-file-label">Wybierz notatke Markdown</h2>
          <p id="current-file-path" class="muted">Brak zaznaczonego pliku.</p>
        </div>

        <div class="topbar-actions">
          <div class="editor-zoom">
            <button id="decrease-font-size" class="icon-button icon-button-small" type="button" aria-label="Pomniejsz tekst edytora">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M10 4a6 6 0 1 0 3.9 10.56l4.27 4.27 1.41-1.41-4.27-4.27A6 6 0 0 0 10 4zm-3 5h6v2H7V9z" />
              </svg>
            </button>
            <span id="font-size-label" class="editor-zoom-label">${preferences.editor_font_size}px</span>
            <button id="increase-font-size" class="icon-button icon-button-small" type="button" aria-label="Powieksz tekst edytora">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M10 4a6 6 0 1 0 3.9 10.56l4.27 4.27 1.41-1.41-4.27-4.27A6 6 0 0 0 10 4zm-1 2h2v3h3v2h-3v3H9v-3H6V9h3V6z" />
              </svg>
            </button>
          </div>
          <button id="open-settings" class="icon-button" type="button" aria-label="Otworz ustawienia">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M10.3 2.4h3.4l.6 2.3c.6.2 1.2.4 1.8.7l2.1-1.2 2.4 2.4-1.2 2.1c.3.6.5 1.2.7 1.8l2.3.6v3.4l-2.3.6c-.2.6-.4 1.2-.7 1.8l1.2 2.1-2.4 2.4-2.1-1.2c-.6.3-1.2.5-1.8.7l-.6 2.3h-3.4l-.6-2.3c-.6-.2-1.2-.4-1.8-.7l-2.1 1.2-2.4-2.4 1.2-2.1c-.3-.6-.5-1.2-.7-1.8l-2.3-.6v-3.4l2.3-.6c.2-.6.4-1.2.7-1.8L3.5 6.6 5.9 4.2 8 5.4c.6-.3 1.2-.5 1.8-.7zm1.7 6.1a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7z" />
            </svg>
          </button>
          % if user.get("is_local"):
            <span class="user-chip">Tryb lokalny</span>
          % else:
            <span class="user-chip">${user.get("email")}</span>
            <form method="post" action="${request.url_for('logout_action')}">
              <button class="button button-secondary" type="submit">Wyloguj</button>
            </form>
          % endif
          <button id="save-button" class="button button-primary" type="button" disabled>Zapisz</button>
        </div>
      </header>

      <section class="editor-stage">
        <div id="editor"></div>

        <div id="empty-state" class="overlay-card">
          <strong>Wybierz plik z drzewa po lewej stronie.</strong>
          <p>Edytor obsluguje Markdown w trybie WYSIWYG.</p>
        </div>

        <div id="unsupported-state" class="overlay-card hidden">
          <strong>Ten plik nie jest obslugiwany.</strong>
          <p>Podglad i zapis dzialaja tylko dla plikow `.md` i `.markdown`.</p>
        </div>
      </section>

      <footer class="statusbar">
        <span id="status-message">Gotowe.</span>
      </footer>
    </main>
  </div>

  <div id="settings-modal" class="modal-backdrop hidden" aria-hidden="true">
    <section class="modal-card" role="dialog" aria-modal="true" aria-labelledby="settings-title">
      <header class="modal-header">
        <div>
          <div class="label">Konfiguracja</div>
          <h3 id="settings-title">Ustawienia</h3>
        </div>
        <button id="close-settings" class="icon-button" type="button" aria-label="Zamknij ustawienia">X</button>
      </header>

      <div class="modal-content">
        <label class="settings-label" for="content-root-input">Katalog notatek</label>
        <div class="settings-path-row">
          <input id="content-root-input" class="settings-input" type="text" value="${preferences.content_root}" />
          <button id="browse-content-root" class="button button-secondary settings-browse-button" type="button">Przegladaj</button>
        </div>

        <label class="settings-label" for="sort-mode-select">Sortowanie</label>
        <select id="sort-mode-select" class="settings-input">
          <option value="alphabetical" ${'selected' if preferences.sort_mode == 'alphabetical' else ''}>Alfabetyczne</option>
          <option value="manual" ${'selected' if preferences.sort_mode == 'manual' else ''}>Manualne</option>
        </select>

        <label class="settings-label" for="theme-mode-select">Motyw</label>
        <select id="theme-mode-select" class="settings-input">
          <option value="light" ${'selected' if preferences.theme_mode == 'light' else ''}>Jasny</option>
          <option value="dark" ${'selected' if preferences.theme_mode == 'dark' else ''}>Ciemny</option>
        </select>

        <label class="settings-label" for="editor-font-size-input">Rozmiar czcionki edytora</label>
        <input
          id="editor-font-size-input"
          class="settings-input"
          type="number"
          min="12"
          max="28"
          step="1"
          value="${preferences.editor_font_size}"
        />

        <p class="muted small-note">Baza SQLite: ${database_path}</p>
      </div>

      <footer class="modal-actions">
        <button id="cancel-settings" class="button button-secondary" type="button">Anuluj</button>
        <button id="save-settings" class="button button-primary" type="button">Zapisz ustawienia</button>
      </footer>
    </section>
  </div>

  <div id="directory-browser-modal" class="modal-backdrop hidden" aria-hidden="true">
    <section class="modal-card modal-card-wide" role="dialog" aria-modal="true" aria-labelledby="directory-browser-title">
      <header class="modal-header">
        <div>
          <div class="label">Wybór katalogu</div>
          <h3 id="directory-browser-title">Przegladarka katalogow</h3>
        </div>
        <button id="close-directory-browser" class="icon-button" type="button" aria-label="Zamknij przegladarke katalogow">X</button>
      </header>

      <div class="modal-content">
        <div class="directory-browser-current">
          <div class="settings-label">Biezaca lokalizacja</div>
          <div id="directory-browser-current-path" class="directory-browser-path muted"></div>
        </div>

        <div class="directory-browser-actions">
          <button id="directory-browser-up" class="button button-secondary" type="button">Poziom wyzej</button>
          <button id="directory-browser-select" class="button button-primary" type="button">Wybierz ten katalog</button>
        </div>

        <div id="directory-browser-list" class="directory-browser-list" aria-live="polite"></div>
      </div>

      <footer class="modal-actions">
        <button id="cancel-directory-browser" class="button button-secondary" type="button">Anuluj</button>
      </footer>
    </section>
  </div>

  <div id="create-modal" class="modal-backdrop hidden" aria-hidden="true">
    <section class="modal-card" role="dialog" aria-modal="true" aria-labelledby="create-title">
      <header class="modal-header">
        <div>
          <div class="label">Tworzenie</div>
          <h3 id="create-title">Nowy element</h3>
        </div>
        <button id="close-create" class="icon-button" type="button" aria-label="Zamknij tworzenie">X</button>
      </header>

      <div class="modal-content">
        <p id="create-parent-label" class="muted small-note">Lokalizacja: katalog glowny</p>

        <label class="settings-label" for="create-name-input">Nazwa</label>
        <input id="create-name-input" class="settings-input" type="text" placeholder="np. Notatka albo Projekty" />
        <p id="create-hint" class="muted small-note">Dla pliku rozszerzenie `.md` zostanie dodane automatycznie, jesli go nie podasz.</p>
      </div>

      <footer class="modal-actions">
        <button id="cancel-create" class="button button-secondary" type="button">Anuluj</button>
        <button id="confirm-create" class="button button-primary" type="button">Utworz</button>
      </footer>
    </section>
  </div>
</%def>

<%def name="scripts_extra()">
  <script src="https://uicdn.toast.com/editor/latest/toastui-editor-all.min.js"></script>
  <script defer src="${request.url_for('static', path='app.js')}"></script>
</%def>

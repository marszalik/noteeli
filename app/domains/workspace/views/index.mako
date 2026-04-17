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
        <div class="sidebar-toolbar sidebar-toolbar-icons">
          <button id="new-file" class="icon-button icon-button-small" type="button" aria-label="Nowy plik" title="Nowy plik">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13 9V3.5L18.5 9H13zM6 2c-1.11 0-2 .89-2 2v16c0 1.11.89 2 2 2h12c1.11 0 2-.89 2-2V8l-6-6H6zm2 9h3V8h2v3h3v2h-3v3h-2v-3H8v-2z"/></svg>
          </button>
          <button id="new-directory" class="icon-button icon-button-small" type="button" aria-label="Nowy katalog" title="Nowy katalog">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6h-8l-2-2H4c-1.11 0-2 .89-2 2v12c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-1 8h-3v3h-2v-3h-3v-2h3V9h2v3h3v2z"/></svg>
          </button>
          <button id="refresh-tree" class="icon-button icon-button-small" type="button" aria-label="Odswiez drzewo" title="Odswiez drzewo">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>
          </button>
          <span class="sidebar-toolbar-sep"></span>
          <button id="reset-tree-root" class="icon-button icon-button-small sidebar-tree-icon hidden" type="button" aria-label="Wroc do pelnego drzewa" title="Wroc do pelnego drzewa">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 6V3L5 8l5 5V9c3.31 0 6 2.69 6 6 0 .7-.12 1.36-.34 1.98l1.53 1.53A7.92 7.92 0 0 0 18 15c0-4.42-3.58-8-8-8zm-6 9c0 4.42 3.58 8 8 8 1.85 0 3.55-.63 4.9-1.69l-1.46-1.46A5.96 5.96 0 0 1 12 21c-3.31 0-6-2.69-6-6 0-.7.12-1.36.34-1.98L4.81 11.5A7.92 7.92 0 0 0 4 15z"/></svg>
          </button>
          <button id="toggle-hidden-files" class="icon-button icon-button-small sidebar-tree-icon" type="button" aria-label="Pokaz ukryte pliki" aria-pressed="false" title="Pokaz ukryte pliki">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6.5A2.5 2.5 0 0 1 6.5 4H10l1.4 1.5H17.5A2.5 2.5 0 0 1 20 8v1h-2V8a.5.5 0 0 0-.5-.5h-6.9L9.2 6H6.5A.5.5 0 0 0 6 6.5V8H4zm-.5 3H20l-1.6 8.1A2.5 2.5 0 0 1 15.95 20H7.05a2.5 2.5 0 0 1-2.45-2.4z"/></svg>
          </button>
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
          <button
            id="editor-mode-toggle"
            class="button button-secondary editor-mode-toggle"
            type="button"
            aria-label="Przelacz tryb edycji"
            title="Przelacz tryb: WYSIWYG <-> Markdown"
          >WYSIWYG</button>
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

        <div id="preview-stage" class="file-preview hidden">
          <img id="image-preview" class="file-preview-image hidden" alt="" />
          <iframe id="pdf-preview" class="file-preview-pdf hidden" title="Podglad PDF"></iframe>
        </div>

        <section id="upload-stage" class="upload-stage hidden" aria-labelledby="upload-stage-title">
          <div class="upload-card">
            <div class="label">Transfer plikow</div>
            <h3 id="upload-stage-title">Upload do katalogu</h3>
            <p id="upload-target-label" class="muted">Docelowy katalog: glowny</p>

            <div id="upload-dropzone" class="upload-dropzone" tabindex="0" role="button" aria-label="Upusc pliki tutaj lub wybierz z dysku">
              <strong>Upusc tutaj pliki albo serie plikow</strong>
              <p>Mozesz tez wybrac je z dysku. Upload nie nadpisuje istniejacych nazw.</p>
              <div class="upload-actions">
                <button id="upload-select-button" class="button button-secondary" type="button">Wybierz z dysku</button>
                <button id="upload-submit-button" class="button button-primary" type="button">Upload</button>
                <button id="upload-cancel-button" class="button button-secondary" type="button">Zamknij</button>
              </div>
              <input id="upload-file-input" type="file" multiple class="hidden" />
            </div>

            <div id="upload-file-list" class="upload-file-list" aria-live="polite"></div>
          </div>
        </section>

        <div id="empty-state" class="overlay-card">
          <strong>Wybierz plik z drzewa po lewej stronie.</strong>
          <p>Edytor obsluguje Markdown w trybie WYSIWYG.</p>
        </div>

        <div id="unsupported-state" class="overlay-card hidden">
          <strong>Ten plik nie jest obslugiwany.</strong>
          <p>Edycja dziala dla Markdown, a podglad dla obrazow i PDF. Ten typ pliku nie ma jeszcze obslugi.</p>
        </div>
      </section>

      <footer class="statusbar">
        <span id="status-message">Gotowe.</span>
      </footer>
    </main>
  </div>

  <div id="tree-context-menu" class="context-menu hidden" aria-hidden="true"></div>

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
        <label class="settings-label" for="source-type-select">Zrodlo notatek</label>
        <select id="source-type-select" class="settings-input">
          <option value="local" ${'selected' if preferences.source_type == 'local' else ''}>Lokalny dysk</option>
          <option value="sftp" ${'selected' if preferences.source_type == 'sftp' else ''}>SFTP / SSH</option>
          <option value="gdrive" ${'selected' if preferences.source_type == 'gdrive' else ''}>Google Drive</option>
        </select>

        <div id="local-source-section" ${'class="hidden"' if preferences.source_type != 'local' else '' | n}>
          <label class="settings-label" for="content-root-input">Katalog notatek</label>
          <div class="settings-path-row">
            <input id="content-root-input" class="settings-input" type="text" value="${preferences.content_root}" />
            <button id="browse-content-root" class="button button-secondary settings-browse-button" type="button">Przegladaj</button>
          </div>
        </div>

        <div id="sftp-source-section" ${'class="hidden"' if preferences.source_type != 'sftp' else '' | n}>
          <label class="settings-label" for="sftp-host-input">Host SFTP</label>
          <input id="sftp-host-input" class="settings-input" type="text" value="${preferences.sftp_host}" placeholder="np. 192.168.1.10 lub moj-serwer.pl" />

          <label class="settings-label" for="sftp-port-input">Port</label>
          <input id="sftp-port-input" class="settings-input" type="number" min="1" max="65535" value="${preferences.sftp_port}" />

          <label class="settings-label" for="sftp-username-input">Uzytkownik</label>
          <input id="sftp-username-input" class="settings-input" type="text" value="${preferences.sftp_username}" placeholder="np. eli" />

          <label class="settings-label" for="sftp-password-input">Haslo</label>
          <input id="sftp-password-input" class="settings-input" type="password" value="${preferences.sftp_password}" autocomplete="new-password" />

          <label class="settings-label" for="sftp-path-input">Sciezka zdalna</label>
          <input id="sftp-path-input" class="settings-input" type="text" value="${preferences.sftp_path}" placeholder="np. /home/eli/notatki" />
          <p class="muted small-note">Haslo przechowywane jest w lokalnej bazie SQLite.</p>
        </div>

        <div id="gdrive-source-section" ${'class="hidden"' if preferences.source_type != 'gdrive' else '' | n}>
          <div class="settings-path-row">
            % if preferences.gdrive_credentials:
              <span class="muted">Google Drive: polaczono</span>
              <a href="${request.url_for('auth_gdrive_start')}" class="button button-secondary settings-browse-button">Polacz ponownie</a>
            % else:
              <span class="muted">Google Drive: brak autoryzacji</span>
              <a href="${request.url_for('auth_gdrive_start')}" class="button button-primary settings-browse-button">Autoryzuj Drive</a>
            % endif
          </div>
          <p class="muted small-note">Po kliknieciu zostaniesz przekierowana do Google. Wymagane scope: Drive (odczyt i zapis).</p>
          <p class="muted small-note">Dodaj do Google Console: <strong>${request.url_for('auth_gdrive_callback')}</strong></p>

          <label class="settings-label" for="gdrive-folder-id-input">ID folderu (opcjonalne)</label>
          <input id="gdrive-folder-id-input" class="settings-input" type="text" value="${preferences.gdrive_folder_id}" placeholder="root = caly Drive" />
          <p class="muted small-note">Skopiuj ID folderu z URL w Google Drive lub zostaw 'root'.</p>
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
          <option value="obsidian" ${'selected' if preferences.theme_mode == 'obsidian' else ''}>Obsidian</option>
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

        <label class="settings-label" for="image-upload-mode-select">Wstawianie obrazkow</label>
        <select id="image-upload-mode-select" class="settings-input">
          <option value="same_dir" ${'selected' if preferences.image_upload_mode == 'same_dir' else ''}>Ten sam katalog co plik MD</option>
          <option value="subdir" ${'selected' if preferences.image_upload_mode == 'subdir' else ''}>Podkatalog o nazwie</option>
        </select>
        <div id="image-upload-subdir-section" ${'class="hidden"' if preferences.image_upload_mode != 'subdir' else '' | n}>
          <input id="image-upload-subdir-input" class="settings-input" type="text" value="${preferences.image_upload_subdir}" placeholder="np. assets" />
        </div>

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
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <script src="https://uicdn.toast.com/editor/latest/toastui-editor-all.min.js"></script>
  <script defer src="${request.url_for('static', path='app.js')}"></script>
</%def>

<%inherit file="/views/base.mako"/>

<%def name="page_title()">Noteeli</%def>
<%def name="initial_theme()">${preferences.theme_mode}</%def>

<%def name="head_extra()">
  <link rel="stylesheet" href="https://uicdn.toast.com/editor/latest/toastui-editor.min.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/jsoneditor@9/dist/jsoneditor.min.css" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/theme/dracula.min.css" />
</%def>

<%def name="content()">
  <div
    class="app-shell"
    data-config='${frontend_config | n}'
    data-theme-mode="${preferences.theme_mode}"
    data-editor-font-size="${preferences.editor_font_size}"
    data-language="${preferences.language}"
  >
    <aside class="sidebar" id="sidebar">
      <div class="brand-block">
        <div class="brand-row">
          <a href="/" class="brand-logo-link" aria-label="Noteeli">
            <img src="${request.url_for('static', path='logo.png')}" alt="Noteeli" class="brand-logo" />
          </a>
          <button id="sidebar-pin" class="icon-button icon-button-small sidebar-pin-btn" type="button" aria-label="Unpin sidebar" title="Unpin sidebar">
            <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>
          </button>
        </div>
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

    <div class="sidebar-resize-handle" id="sidebar-resize-handle" aria-hidden="true"></div>

    <main class="workspace-panel">
      <header class="workspace-topbar">
        <div class="topbar-left">
          <button id="sidebar-toggle" class="icon-button icon-button-small sidebar-toggle-btn" type="button" aria-label="Toggle sidebar" aria-expanded="true" title="Toggle sidebar">
            <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
          </button>
          <div>
            <div class="label">Wybrany plik</div>
            <h2 id="current-file-label">Wybierz notatke Markdown</h2>
            <p id="current-file-path" class="muted">Brak zaznaczonego pliku.</p>
          </div>
        </div>

        <div class="topbar-actions">
          <div class="profiles-menu">
            <button id="toggle-preference-profiles" class="icon-button" type="button" aria-label="Pokaz zapisane zestawy ustawien" aria-expanded="false" aria-controls="preference-profiles-dropdown" title="Zapisane zestawy ustawien">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M18 2H8a3 3 0 0 0-3 3v14a2 2 0 0 0 2 2h11a3 3 0 0 1 3 3V5a3 3 0 0 0-3-3zm0 17.08A4.97 4.97 0 0 0 17 19H7V5a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1zM8.5 7H16v2H8.5zm0 4H16v2H8.5zm0 4H13v2H8.5z" />
              </svg>
            </button>
            <div id="preference-profiles-dropdown" class="profiles-dropdown hidden" aria-hidden="true">
              <div class="profiles-dropdown-header">
                <div class="label">Szybki start</div>
                <strong>Zapisane zestawy</strong>
              </div>
              <div id="preference-profiles-list" class="profiles-dropdown-list"></div>
            </div>
          </div>
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
            class="button button-secondary button-sm editor-mode-toggle"
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
            <span class="user-chip" data-i18n="local_mode_chip">Tryb lokalny</span>
          % else:
            <span class="user-chip">${user.get("email")}</span>
            <form method="post" action="${request.url_for('logout_action')}">
              <button class="button button-secondary button-sm" type="submit" data-i18n="logout_button">Wyloguj</button>
            </form>
          % endif
          <button id="save-button" class="button button-primary button-sm" type="button" data-i18n="save_button" disabled>Zapisz</button>
        </div>
      </header>

      <section class="editor-stage">
        <div id="editor"></div>
        <div id="json-editor" class="json-editor-panel hidden"></div>
        <div id="code-editor" class="code-editor-panel hidden"></div>

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
          <div class="label" data-i18n="label_config">Konfiguracja</div>
          <h3 id="settings-title" data-i18n="settings_title">Ustawienia</h3>
        </div>
        <button id="close-settings" class="icon-button" type="button" aria-label="Zamknij ustawienia">X</button>
      </header>

      <div class="modal-content">
        <div class="settings-profile-panel">
          <div class="settings-profile-panel-header">
            <div>
              <div class="label" data-i18n="label_profiles">Profile</div>
              <strong id="profile-editor-title" data-i18n="profile_new">Nowy profil</strong>
            </div>
            <button id="cancel-profile-edit" class="button button-secondary hidden" type="button" data-i18n="cancel_edit">Anuluj edycje</button>
          </div>
          <div class="settings-path-row">
            <input id="profile-name-input" class="settings-input" type="text" placeholder="np. SFTP firmowy albo Projekty lokalne" />
            <button id="save-profile" class="button button-secondary settings-browse-button" type="button" data-i18n="save_profile">Zapamietaj</button>
          </div>
          <p class="muted small-note" data-i18n="profile_hint">Zapisuje aktualne pola formularza jako profil do szybkiego przelaczania z gornego menu.</p>
          <div id="settings-profile-list" class="settings-profile-list"></div>
        </div>

        <div class="settings-group">
          <h4 class="settings-group-title" data-i18n="group_source">Zrodlo notatek</h4>
          <select id="source-type-select" class="settings-input">
            <option value="local" data-i18n-opt="source_local" ${'selected' if preferences.source_type == 'local' else ''}>Lokalny dysk</option>
            <option value="sftp" ${'selected' if preferences.source_type == 'sftp' else ''}>SFTP / SSH</option>
            <option value="gdrive" ${'selected' if preferences.source_type == 'gdrive' else ''}>Google Drive</option>
          </select>

          <div id="local-source-section" ${'class="hidden"' if preferences.source_type != 'local' else '' | n}>
            <label class="settings-label" data-i18n="label_notes_dir" for="content-root-input">Katalog notatek</label>
            <div class="settings-path-row">
              <input id="content-root-input" class="settings-input" type="text" value="${preferences.content_root}" />
              <button id="browse-content-root" class="button button-secondary settings-browse-button" type="button" data-i18n="browse">Przegladaj</button>
            </div>
          </div>

        <div id="sftp-source-section" ${'class="hidden"' if preferences.source_type != 'sftp' else '' | n}>
          <label class="settings-label" for="sftp-host-input">Host SFTP</label>
          <input id="sftp-host-input" class="settings-input" type="text" value="${preferences.sftp_host}" placeholder="np. 192.168.1.10 lub moj-serwer.pl" />

          <label class="settings-label" data-i18n="label_port" for="sftp-port-input">Port</label>
          <input id="sftp-port-input" class="settings-input" type="number" min="1" max="65535" value="${preferences.sftp_port}" />

          <label class="settings-label" data-i18n="label_user" for="sftp-username-input">Uzytkownik</label>
          <input id="sftp-username-input" class="settings-input" type="text" value="${preferences.sftp_username}" placeholder="np. eli" />

          <label class="settings-label" data-i18n="label_password" for="sftp-password-input">Haslo</label>
          <input id="sftp-password-input" class="settings-input" type="password" value="${preferences.sftp_password}" autocomplete="new-password" />

          <label class="settings-label" data-i18n="label_remote_path" for="sftp-path-input">Sciezka zdalna</label>
          <input id="sftp-path-input" class="settings-input" type="text" value="${preferences.sftp_path}" placeholder="np. /home/eli/notatki" />
          <p class="muted small-note" data-i18n="sftp_password_hint">Haslo przechowywane jest w lokalnej bazie SQLite.</p>
        </div>

        <div id="gdrive-source-section" ${'class="hidden"' if preferences.source_type != 'gdrive' else '' | n}>
          <div class="settings-path-row">
            % if preferences.gdrive_credentials:
              <span class="muted" data-i18n="gdrive_connected">Google Drive: polaczono</span>
              <a href="${request.url_for('auth_gdrive_start')}" class="button button-secondary settings-browse-button" data-i18n="gdrive_reconnect">Polacz ponownie</a>
            % else:
              <span class="muted" data-i18n="gdrive_disconnected">Google Drive: brak autoryzacji</span>
              <a href="${request.url_for('auth_gdrive_start')}" class="button button-primary settings-browse-button" data-i18n="gdrive_authorize">Autoryzuj Drive</a>
            % endif
          </div>
          <p class="muted small-note" data-i18n="gdrive_hint">Po kliknieciu zostaniesz przekierowana do Google. Wymagane scope: Drive (odczyt i zapis).</p>
          <p class="muted small-note" data-i18n="gdrive_console_hint">Dodaj do Google Console: <strong>${request.url_for('auth_gdrive_callback')}</strong></p>

          <label class="settings-label" data-i18n="label_folder_id" for="gdrive-folder-id-input">ID folderu (opcjonalne)</label>
          <input id="gdrive-folder-id-input" class="settings-input" type="text" value="${preferences.gdrive_folder_id}" placeholder="root = caly Drive" />
          <p class="muted small-note" data-i18n="gdrive_folder_hint">Skopiuj ID folderu z URL w Google Drive lub zostaw 'root'.</p>
          </div>
        </div>

        <div class="settings-group">
          <h4 class="settings-group-title" data-i18n="group_appearance">Wyglad</h4>
          <label class="settings-label" data-i18n="label_language" for="language-select">Jezyk interfejsu</label>
          <select id="language-select" class="settings-input">
            <option value="pl" ${'selected' if preferences.language == 'pl' else ''}>Polski</option>
            <option value="en" ${'selected' if preferences.language == 'en' else ''}>English</option>
            <option value="es" ${'selected' if preferences.language == 'es' else ''}>Español</option>
            <option value="de" ${'selected' if preferences.language == 'de' else ''}>Deutsch</option>
            <option value="ru" ${'selected' if preferences.language == 'ru' else ''}>Русский</option>
          </select>

          <label class="settings-label" data-i18n="label_theme" for="theme-mode-select">Motyw</label>
          <select id="theme-mode-select" class="settings-input">
            <option value="noteeli" ${'selected' if preferences.theme_mode == 'noteeli' else ''}>Noteeli</option>
            <option value="light" data-i18n-opt="theme_light" ${'selected' if preferences.theme_mode == 'light' else ''}>Jasny</option>
            <option value="dark" data-i18n-opt="theme_dark" ${'selected' if preferences.theme_mode == 'dark' else ''}>Ciemny</option>
            <option value="obsidian" ${'selected' if preferences.theme_mode == 'obsidian' else ''}>Obsidian</option>
          </select>

          <label class="settings-label" data-i18n="label_font_size" for="editor-font-size-input">Rozmiar czcionki edytora</label>
          <input
            id="editor-font-size-input"
            class="settings-input"
            type="number"
            min="12"
            max="28"
            step="1"
            value="${preferences.editor_font_size}"
          />
        </div>

        <div class="settings-group">
          <h4 class="settings-group-title" data-i18n="group_editor">Edytor</h4>
          <label class="settings-label" data-i18n="label_sort" for="sort-mode-select">Sortowanie</label>
          <select id="sort-mode-select" class="settings-input">
            <option value="alphabetical" data-i18n-opt="sort_alpha" ${'selected' if preferences.sort_mode == 'alphabetical' else ''}>Alfabetyczne</option>
            <option value="manual" data-i18n-opt="sort_manual" ${'selected' if preferences.sort_mode == 'manual' else ''}>Manualne</option>
          </select>

          <label class="settings-toggle">
            <input id="autosave-enabled-input" type="checkbox" ${'checked' if preferences.autosave_enabled else ''} />
            <span>
              <strong data-i18n="label_autosave">Automatyczny zapis</strong>
              <small class="muted" data-i18n="autosave_hint">Zapisuje zmiany po krotkiej pauzie w pisaniu.</small>
            </span>
          </label>
        </div>

        <div class="settings-group">
          <h4 class="settings-group-title" data-i18n="group_images">Obrazki</h4>
          <label class="settings-label" data-i18n="label_image_upload" for="image-upload-mode-select">Wstawianie obrazkow</label>
          <select id="image-upload-mode-select" class="settings-input">
            <option value="same_dir" data-i18n-opt="img_same_dir" ${'selected' if preferences.image_upload_mode == 'same_dir' else ''}>Ten sam katalog co plik MD</option>
            <option value="subdir" data-i18n-opt="img_subdir" ${'selected' if preferences.image_upload_mode == 'subdir' else ''}>Podkatalog o nazwie</option>
          </select>
          <div id="image-upload-subdir-section" ${'class="hidden"' if preferences.image_upload_mode != 'subdir' else '' | n}>
            <input id="image-upload-subdir-input" class="settings-input" type="text" value="${preferences.image_upload_subdir}" placeholder="np. assets" />
          </div>
        </div>

        <p class="muted small-note" data-i18n="db_path_label">Baza SQLite: ${database_path}</p>
      </div>

      <footer class="modal-actions">
        <button id="cancel-settings" class="button button-secondary" type="button" data-i18n="cancel">Anuluj</button>
        <button id="save-settings" class="button button-primary" type="button" data-i18n="save_settings">Zapisz ustawienia</button>
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
          <div id="directory-browser-current-path" class="directory-browser-path"></div>
        </div>

        <div class="directory-browser-actions">
          <button id="directory-browser-up" class="button button-secondary button-sm" type="button"><svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="8,12 8,4"/><polyline points="4,8 8,4 12,8"/></svg>Poziom wyzej</button>
          <button id="directory-browser-new" class="button button-secondary button-sm" type="button"><svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 4.5A1.5 1.5 0 0 1 3.5 3h3.586a1 1 0 0 1 .707.293l.914.914A1 1 0 0 0 9.414 4.5H12.5A1.5 1.5 0 0 1 14 6v6a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 2 12V4.5Z"/><line x1="8" y1="8" x2="8" y2="12"/><line x1="6" y1="10" x2="10" y2="10"/></svg>Nowy folder</button>
          <button id="directory-browser-select" class="button button-primary button-sm" type="button"><svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="3,8 6,11 13,4"/></svg>Wybierz</button>
        </div>

        <div id="directory-browser-create" class="directory-browser-create hidden">
          <input id="directory-browser-create-input" class="settings-input" type="text" placeholder="Nazwa nowego folderu" />
          <div class="directory-browser-create-actions">
            <button id="directory-browser-create-confirm" class="button button-primary" type="button">Utworz i wejdz</button>
            <button id="directory-browser-create-cancel" class="button button-secondary" type="button">Anuluj</button>
          </div>
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
  <script src="https://cdn.jsdelivr.net/npm/jsoneditor@9/dist/jsoneditor.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/meta.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/mode/loadmode.min.js"></script>
  <script defer src="${request.url_for('static', path='app.js')}?v=${static_version}"></script>
</%def>

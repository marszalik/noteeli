<%inherit file="/views/base.mako"/>

<%def name="page_title()"><%
    _pv = context.get('public_view')
%>${(_pv.slug + " — Noteeli") if _pv else "Noteeli"}</%def>
<%def name="initial_theme()">${preferences.theme_mode}</%def>

<%def name="head_extra()">
<%
    _is_public = bool(context.get('public_view'))
%>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@400;500;600&display=swap" />
% if not _is_public:
  <link rel="stylesheet" href="https://uicdn.toast.com/editor/latest/toastui-editor.min.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/jsoneditor@9/dist/jsoneditor.min.css" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.css" />
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/theme/dracula.min.css" />
% else:
  <link rel="stylesheet" href="${request.url_for('publish_pygments_css')}" />
% endif
</%def>

<%def name="content()">
<%
    is_public = bool(context.get('public_view'))
    public_view = context.get('public_view')
%>
  % if demo_mode:
  <div class="demo-banner" role="status">
    <strong data-i18n="demo_banner_label">Demo mode</strong>
    <span data-i18n="demo_banner_text">— no changes will be saved.</span>
    <a href="https://noteeli.com" target="_blank" rel="noopener" data-i18n="demo_banner_cta">Get Noteeli</a>
    <span data-i18n="demo_banner_suffix">to write and keep your own notes.</span>
  </div>
  % endif
  % if is_public:
  <div class="public-banner" role="status">
    <strong>Public view</strong>
    — read-only.
    <a href="https://noteeli.com" target="_blank" rel="noopener">Get Noteeli</a>
    to publish your own notes.
  </div>
  % endif
  % if context.get('needs_storage_setup'):
  <div class="setup-banner" role="status">
    <strong>Welcome — one more step.</strong>
    Choose where Noteeli should store your notes:
    open <button id="open-settings-from-banner" class="setup-banner-link">Settings</button>
    and configure either <strong>SFTP</strong> or <strong>Google Drive</strong>.
    Your notes stay in storage you control.
  </div>
  % endif

  <div
    class="app-shell ${'is-demo' if demo_mode else ''} ${'is-public' if is_public else ''} ${'is-public-file' if is_public and public_view.kind == 'file' else ''}"
    data-config='${frontend_config | n}'
    data-theme-mode="${preferences.theme_mode}"
    data-editor-font-size="${preferences.editor_font_size}"
    data-language="${preferences.language}"
    data-compact-chrome="${'1' if preferences.compact_chrome else '0'}"
    ${'data-demo="1"' if demo_mode else '' | n}
    ${'data-public="1"' if is_public else '' | n}
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
          <button id="new-file" class="icon-button icon-button-small" type="button" aria-label="New file" title="New file">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13 9V3.5L18.5 9H13zM6 2c-1.11 0-2 .89-2 2v16c0 1.11.89 2 2 2h12c1.11 0 2-.89 2-2V8l-6-6H6zm2 9h3V8h2v3h3v2h-3v3h-2v-3H8v-2z"/></svg>
          </button>
          <button id="new-directory" class="icon-button icon-button-small" type="button" aria-label="New folder" title="New folder">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6h-8l-2-2H4c-1.11 0-2 .89-2 2v12c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-1 8h-3v3h-2v-3h-3v-2h3V9h2v3h3v2z"/></svg>
          </button>
          <button id="refresh-tree" class="icon-button icon-button-small" type="button" aria-label="Refresh tree" title="Refresh tree">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/></svg>
          </button>
          <button id="tree-search-toggle" class="icon-button icon-button-small" type="button" aria-label="Search files" aria-pressed="false" title="Search files" data-i18n-title="tree_search_title">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15.5 14h-.79l-.28-.27a6.5 6.5 0 1 0-.7.7l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0A4.5 4.5 0 1 1 14 9.5 4.5 4.5 0 0 1 9.5 14z"/></svg>
          </button>
          <span class="sidebar-toolbar-sep"></span>
          <button id="reset-tree-root" class="icon-button icon-button-small sidebar-tree-icon hidden" type="button" aria-label="Back to full tree" title="Back to full tree">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 6V3L5 8l5 5V9c3.31 0 6 2.69 6 6 0 .7-.12 1.36-.34 1.98l1.53 1.53A7.92 7.92 0 0 0 18 15c0-4.42-3.58-8-8-8zm-6 9c0 4.42 3.58 8 8 8 1.85 0 3.55-.63 4.9-1.69l-1.46-1.46A5.96 5.96 0 0 1 12 21c-3.31 0-6-2.69-6-6 0-.7.12-1.36.34-1.98L4.81 11.5A7.92 7.92 0 0 0 4 15z"/></svg>
          </button>
          <button id="toggle-hidden-files" class="icon-button icon-button-small sidebar-tree-icon" type="button" aria-label="Show hidden files" aria-pressed="false" title="Show hidden files">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6.5A2.5 2.5 0 0 1 6.5 4H10l1.4 1.5H17.5A2.5 2.5 0 0 1 20 8v1h-2V8a.5.5 0 0 0-.5-.5h-6.9L9.2 6H6.5A.5.5 0 0 0 6 6.5V8H4zm-.5 3H20l-1.6 8.1A2.5 2.5 0 0 1 15.95 20H7.05a2.5 2.5 0 0 1-2.45-2.4z"/></svg>
          </button>
        </div>
        <div id="tree-search-row" class="tree-search-row hidden">
          <input
            id="tree-search-input"
            type="search"
            class="tree-search-input"
            autocomplete="off"
            spellcheck="false"
            placeholder="Szukaj plików…"
            data-i18n-placeholder="tree_search_placeholder"
            aria-label="Search files by name"
          />
        </div>
      </div>

      <div id="tree-root" class="tree-root" aria-live="polite"></div>

      <a
        class="sidebar-version"
        href="https://github.com/marszalik/noteeli/releases/tag/v${app_version}"
        target="_blank"
        rel="noopener"
        title="View this version's changelog"
      >v${app_version}</a>
    </aside>

    <div class="sidebar-resize-handle" id="sidebar-resize-handle" aria-hidden="true"></div>

    <main class="workspace-panel">
      <header class="workspace-topbar">
        <div class="topbar-left">
          <button id="sidebar-toggle" class="icon-button icon-button-small sidebar-toggle-btn" type="button" aria-label="Toggle sidebar" aria-expanded="true" title="Toggle sidebar">
            <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
          </button>
          <div>
            <div class="label">Selected file</div>
            <h2 id="current-file-label">Pick a Markdown note</h2>
            <p id="current-file-path" class="muted">No file selected.</p>
          </div>
        </div>

        <div class="topbar-actions">
          <div class="profiles-menu">
            <button id="toggle-preference-profiles" class="icon-button" type="button" aria-label="Show saved preference profiles" aria-expanded="false" aria-controls="preference-profiles-dropdown" title="Saved preference profiles">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M18 2H8a3 3 0 0 0-3 3v14a2 2 0 0 0 2 2h11a3 3 0 0 1 3 3V5a3 3 0 0 0-3-3zm0 17.08A4.97 4.97 0 0 0 17 19H7V5a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1zM8.5 7H16v2H8.5zm0 4H16v2H8.5zm0 4H13v2H8.5z" />
              </svg>
            </button>
            <div id="preference-profiles-dropdown" class="profiles-dropdown hidden" aria-hidden="true">
              <div class="profiles-dropdown-header">
                <div class="label" data-i18n="quick_start">Quick start</div>
                <strong data-i18n="saved_profiles">Saved profiles</strong>
              </div>
              <div id="preference-profiles-list" class="profiles-dropdown-list"></div>
              <div class="profiles-dropdown-footer">
                <input
                  id="profile-quick-name"
                  type="text"
                  class="settings-input"
                  data-i18n-placeholder="save_new_profile_placeholder"
                  placeholder="Save current as new profile…"
                />
                <button
                  id="profile-quick-save"
                  type="button"
                  class="button button-primary button-sm"
                  data-i18n="save_action"
                >Save</button>
              </div>
            </div>
          </div>
          <div class="git-menu hidden" id="git-menu">
            <button id="git-menu-toggle" class="icon-button" type="button" aria-label="Git" aria-haspopup="true" aria-expanded="false" aria-controls="git-menu-dropdown" title="Git">
              <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
                <path d="M21.62 11.1 12.9 2.38a1.3 1.3 0 0 0-1.84 0l-1.81 1.8 2.3 2.3a1.54 1.54 0 0 1 1.95 1.97l2.22 2.21a1.54 1.54 0 1 1-.92.87l-2.07-2.07v5.45a1.54 1.54 0 1 1-1.27-.04V11.3a1.54 1.54 0 0 1-.84-2.02L8.56 7.0l-6.18 6.18a1.3 1.3 0 0 0 0 1.84l8.72 8.72a1.3 1.3 0 0 0 1.84 0l8.68-8.68a1.3 1.3 0 0 0 0-1.84z"/>
              </svg>
              <span id="git-menu-badge" class="git-menu-badge hidden">0</span>
            </button>
            <div id="git-menu-dropdown" class="git-dropdown hidden" role="menu" aria-hidden="true">
              <div class="git-dropdown-header">
                <div class="git-branch-row">
                  <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor" class="git-branch-icon"><path d="M6 3a3 3 0 0 0-1 5.83v6.34a3 3 0 1 0 2 0V12a4 4 0 0 0 4 4h1.17a3 3 0 1 0 0-2H11a2 2 0 0 1-2-2V8.83A3 3 0 0 0 6 3z"/></svg>
                  <strong id="git-branch-name">—</strong>
                  <span id="git-sync-state" class="git-sync-state"></span>
                </div>
              </div>
              <button id="git-file-history" class="git-menu-history hidden" type="button">
                <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
                  <path d="M3 5h2v2H3V5zm4 0h14v2H7V5zM3 11h2v2H3v-2zm4 0h14v2H7v-2zM3 17h2v2H3v-2zm4 0h14v2H7v-2z" />
                </svg>
                <span class="git-menu-history-text">
                  <span data-i18n="history_button_title">Historia i autorzy zmian</span>
                  <span id="git-file-history-name" class="git-menu-history-file"></span>
                </span>
              </button>
              <div id="git-changes-list" class="git-changes-list"></div>
              <div class="git-commit-box">
                <textarea id="git-commit-message" class="git-commit-message" rows="2" data-i18n-placeholder="git_commit_placeholder" placeholder="Commit message…"></textarea>
                <div class="git-commit-actions">
                  <button id="git-commit" class="button button-secondary button-sm" type="button" data-i18n="git_commit">Commit</button>
                  <button id="git-commit-push" class="button button-primary button-sm" type="button" data-i18n="git_commit_push">Commit &amp; Push</button>
                </div>
              </div>
              <div class="git-remote-actions">
                <button id="git-fetch" class="button button-secondary button-sm" type="button" data-i18n="git_fetch">Fetch</button>
                <button id="git-pull" class="button button-secondary button-sm" type="button" data-i18n="git_pull">Pull</button>
                <button id="git-push" class="button button-secondary button-sm" type="button" data-i18n="git_push">Push</button>
              </div>
              <p id="git-status-msg" class="git-status-msg muted"></p>
            </div>
          </div>
          <div class="editor-zoom">
            <button id="decrease-font-size" class="icon-button icon-button-small" type="button" aria-label="Decrease editor font size">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M10 4a6 6 0 1 0 3.9 10.56l4.27 4.27 1.41-1.41-4.27-4.27A6 6 0 0 0 10 4zm-3 5h6v2H7V9z" />
              </svg>
            </button>
            <span id="font-size-label" class="editor-zoom-label">${preferences.editor_font_size}px</span>
            <button id="increase-font-size" class="icon-button icon-button-small" type="button" aria-label="Increase editor font size">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M10 4a6 6 0 1 0 3.9 10.56l4.27 4.27 1.41-1.41-4.27-4.27A6 6 0 0 0 10 4zm-1 2h2v3h3v2h-3v3H9v-3H6V9h3V6z" />
              </svg>
            </button>
          </div>
          <button id="refresh-file" class="icon-button icon-button-small" type="button" aria-label="Reload file from disk" title="Reload file (it may have changed in the background)" data-i18n-title="refresh_file_title" disabled>
            <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
              <path d="M17.65 6.35A7.958 7.958 0 0 0 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0 1 12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" />
            </svg>
          </button>
          <button
            id="editor-mode-toggle"
            class="button button-secondary button-sm editor-mode-toggle"
            type="button"
            aria-label="Toggle edit mode"
            title="Toggle mode: WYSIWYG <-> Markdown"
          >WYSIWYG</button>

          <div class="user-menu">
            <button id="user-menu-toggle" class="icon-button" type="button" aria-label="Account menu" aria-haspopup="true" aria-expanded="false" aria-controls="user-menu-dropdown" title="Account">
              <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
              </svg>
            </button>
            <div id="user-menu-dropdown" class="user-menu-dropdown hidden" role="menu" aria-hidden="true">
              <div class="user-menu-identity">
                % if user.get("is_local"):
                  <span class="user-menu-label" data-i18n="local_mode_chip">Tryb lokalny</span>
                % else:
                  <span class="user-menu-email">${user.get("email")}</span>
                % endif
              </div>
              <button id="open-settings" class="user-menu-item" type="button" role="menuitem">
                <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
                  <path d="M10.3 2.4h3.4l.6 2.3c.6.2 1.2.4 1.8.7l2.1-1.2 2.4 2.4-1.2 2.1c.3.6.5 1.2.7 1.8l2.3.6v3.4l-2.3.6c-.2.6-.4 1.2-.7 1.8l1.2 2.1-2.4 2.4-2.1-1.2c-.6.3-1.2.5-1.8.7l-.6 2.3h-3.4l-.6-2.3c-.6-.2-1.2-.4-1.8-.7l-2.1 1.2-2.4-2.4 1.2-2.1c-.3-.6-.5-1.2-.7-1.8l-2.3-.6v-3.4l2.3-.6c.2-.6.4-1.2.7-1.8L3.5 6.6 5.9 4.2 8 5.4c.6-.3 1.2-.5 1.8-.7zm1.7 6.1a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7z" />
                </svg>
                <span data-i18n="settings_title">Ustawienia</span>
              </button>
              % if not user.get("is_local"):
                <form method="post" action="${request.url_for('logout_action')}" class="user-menu-logout-form">
                  <button class="user-menu-item user-menu-item-danger" type="submit" role="menuitem">
                    <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
                      <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4z" />
                    </svg>
                    <span data-i18n="logout_button">Wyloguj</span>
                  </button>
                </form>
              % endif
            </div>
          </div>

          <button id="save-button" class="button button-primary button-sm" type="button" data-i18n="save_button" disabled>Zapisz</button>
        </div>
      </header>

      <section class="editor-stage">
        <div id="editor"></div>
        <div id="json-editor" class="json-editor-panel hidden"></div>
        <div id="code-editor" class="code-editor-panel hidden"></div>
        <div id="public-content" class="public-content hidden"></div>

        <div id="preview-stage" class="file-preview hidden">
          <img id="image-preview" class="file-preview-image hidden" alt="" />
          <iframe id="pdf-preview" class="file-preview-pdf hidden" title="Podglad PDF"></iframe>
          <iframe id="office-preview" class="file-preview-office hidden" sandbox="allow-same-origin" title="Podglad dokumentu"></iframe>
        </div>

        <section id="upload-stage" class="upload-stage hidden" aria-labelledby="upload-stage-title">
          <div class="upload-card">
            <div class="label">Transfer plikow</div>
            <h3 id="upload-stage-title">Upload to folder</h3>
            <p id="upload-target-label" class="muted">Target folder: root</p>

            <div id="upload-dropzone" class="upload-dropzone" tabindex="0" role="button" aria-label="Upusc pliki tutaj lub wybierz z dysku">
              <strong>Upusc tutaj pliki albo serie plikow</strong>
              <p>Mozesz tez wybrac je z dysku. Upload nie nadpisuje istniejacych nazw.</p>
              <div class="upload-actions">
                <button id="upload-select-button" class="button button-secondary" type="button">Browse files</button>
                <button id="upload-submit-button" class="button button-primary" type="button">Upload</button>
                <button id="upload-cancel-button" class="button button-secondary" type="button">Close</button>
              </div>
              <input id="upload-file-input" type="file" multiple class="hidden" />
            </div>

            <div id="upload-file-list" class="upload-file-list" aria-live="polite"></div>
          </div>
        </section>

        <div id="empty-state" class="overlay-card">
          <strong>Pick a file from the tree on the left.</strong>
          <p>The editor supports Markdown in WYSIWYG mode.</p>
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
    <section class="modal-card modal-card-settings" role="dialog" aria-modal="true" aria-labelledby="settings-title">
      <header class="modal-header">
        <div>
          <div class="label" data-i18n="label_config">Konfiguracja</div>
          <h3 id="settings-title" data-i18n="settings_title">Ustawienia</h3>
        </div>
        <button id="close-settings" class="icon-button" type="button" aria-label="Close settings">X</button>
      </header>

      <div class="settings-body">
<% _locked = bool(context.get('lock_workspace')) %>
        <nav class="settings-tabs" role="tablist">
          % if not _locked:
          <button class="settings-tab is-active" type="button" data-tab="source" role="tab" data-i18n="group_source">Zrodlo</button>
          % endif
          <button class="settings-tab ${'is-active' if _locked else ''}" type="button" data-tab="appearance" role="tab" data-i18n="group_appearance">Wyglad</button>
          <button class="settings-tab" type="button" data-tab="editor" role="tab" data-i18n="group_editor">Edytor</button>
          <button class="settings-tab" type="button" data-tab="images" role="tab" data-i18n="group_images">Obrazki</button>
        </nav>

        <div class="settings-tab-content">
          % if not _locked:
          <section class="settings-tab-panel" data-panel="source" role="tabpanel">
            <label class="settings-label" data-i18n="label_source" for="source-type-select">Zrodlo notatek</label>
            <select id="source-type-select" class="settings-input">
              % if not hosted_mode:
              <option value="local" data-i18n-opt="source_local" ${'selected' if preferences.source_type == 'local' else ''}>Lokalny dysk</option>
              % endif
              <option value="sftp" ${'selected' if preferences.source_type == 'sftp' else ''}>SFTP / SSH</option>
              <option value="gdrive" ${'selected' if preferences.source_type == 'gdrive' else ''}>Google Drive</option>
            </select>

            <div id="local-source-section" ${'class="hidden"' if hosted_mode or preferences.source_type != 'local' else '' | n}>
              <label class="settings-label" data-i18n="label_notes_dir" for="content-root-input">Katalog notatek</label>
              <div class="settings-path-row">
                <input id="content-root-input" class="settings-input" type="text" value="${preferences.content_root}" />
                <button id="browse-content-root" class="button button-secondary settings-browse-button" type="button" data-i18n="browse">Przegladaj</button>
              </div>
            </div>

            <div id="sftp-source-section" ${'class="hidden"' if preferences.source_type != 'sftp' else '' | n}>
              <label class="settings-label" for="sftp-host-input">Host SFTP</label>
              <input id="sftp-host-input" class="settings-input" type="text" value="${preferences.sftp_host}" placeholder="e.g. 192.168.1.10 or my-server.com" />

              <label class="settings-label" data-i18n="label_port" for="sftp-port-input">Port</label>
              <input id="sftp-port-input" class="settings-input" type="number" min="1" max="65535" value="${preferences.sftp_port}" />

              <label class="settings-label" data-i18n="label_user" for="sftp-username-input">Uzytkownik</label>
              <input id="sftp-username-input" class="settings-input" type="text" value="${preferences.sftp_username}" placeholder="e.g. alex" />

              <label class="settings-label" data-i18n="label_password" for="sftp-password-input">Haslo</label>
              <input id="sftp-password-input" class="settings-input" type="password" value="" autocomplete="new-password" placeholder="${'•••••• (saved — leave blank to keep)' if preferences.has_stored_sftp_password else 'Required'}" />

              <label class="settings-label" data-i18n="label_remote_path" for="sftp-path-input">Sciezka zdalna</label>
              <input id="sftp-path-input" class="settings-input" type="text" value="${preferences.sftp_path}" placeholder="e.g. /home/alex/notes" />
              <p class="muted small-note" data-i18n="sftp_password_hint">Password is encrypted at rest with a key derived from your session secret.</p>

              <button id="sftp-connect-button" type="button" class="button button-primary" style="margin-top:12px">
                Connect to SFTP
              </button>
              <p id="sftp-connect-status" class="muted small-note"></p>
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
              <input id="gdrive-folder-id-input" class="settings-input" type="text" value="${preferences.gdrive_folder_id}" placeholder="root = entire Drive" />
              <p class="muted small-note" data-i18n="gdrive_folder_hint">Skopiuj ID folderu z URL w Google Drive lub zostaw 'root'.</p>
            </div>
          </section>
          % endif

          <section class="settings-tab-panel ${'' if _locked else 'hidden'}" data-panel="appearance" role="tabpanel">
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
              <option value="webnote" ${'selected' if preferences.theme_mode == 'webnote' else ''}>Webnote.li</option>
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

            <label class="settings-toggle">
              <input id="compact-chrome-input" type="checkbox" ${'checked' if preferences.compact_chrome else ''} />
              <span>
                <strong data-i18n="label_compact_chrome">Kompaktowy układ (bez ramek)</strong>
                <small class="muted" data-i18n="compact_chrome_hint">Usuwa zaokrąglone obramowania paneli i zewnętrzny margines, żeby zyskać miejsce na treść.</small>
              </span>
            </label>
          </section>

          <section class="settings-tab-panel hidden" data-panel="editor" role="tabpanel">
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

            <label class="settings-label" data-i18n="label_md_style" for="markdown-style-select">Markdown rendering style</label>
            <select id="markdown-style-select" class="settings-input">
              <option value="default" data-i18n-opt="md_style_default">Default</option>
              <option value="clean" data-i18n-opt="md_style_clean">Clean</option>
              <option value="magazine" data-i18n-opt="md_style_magazine">Magazine (serif)</option>
              <option value="compact" data-i18n-opt="md_style_compact">Compact</option>
              <option value="manuscript" data-i18n-opt="md_style_manuscript">Manuscript</option>
            </select>

            <label class="settings-label" data-i18n="label_code_theme" for="code-theme-select">Motyw kolorowania kodu</label>
            <select id="code-theme-select" class="settings-input">
              <option value="auto" data-i18n-opt="code_theme_auto">Automatyczny</option>
              <option value="default" data-i18n-opt="code_theme_default">Default (jasny)</option>
              <option value="material-darker">Material Darker (VS Code-like)</option>
              <option value="darcula">Darcula (JetBrains)</option>
              <option value="monokai">Monokai</option>
              <option value="dracula">Dracula</option>
              <option value="nord">Nord</option>
              <option value="ayu-dark">Ayu Dark</option>
              <option value="tomorrow-night-eighties">Tomorrow Night</option>
              <option value="eclipse" data-i18n-opt="code_theme_eclipse">Eclipse (jasny)</option>
              <option value="idea" data-i18n-opt="code_theme_idea">IntelliJ IDEA (jasny)</option>
              <option value="solarized">Solarized</option>
            </select>

            <p class="muted small-note" data-i18n="db_path_label">Baza SQLite: ${database_path}</p>
          </section>

          <section class="settings-tab-panel hidden" data-panel="images" role="tabpanel">
            <label class="settings-label" data-i18n="label_image_upload" for="image-upload-mode-select">Wstawianie obrazkow</label>
            <select id="image-upload-mode-select" class="settings-input">
              <option value="same_dir" data-i18n-opt="img_same_dir" ${'selected' if preferences.image_upload_mode == 'same_dir' else ''}>Ten sam katalog co plik MD</option>
              <option value="subdir" data-i18n-opt="img_subdir" ${'selected' if preferences.image_upload_mode == 'subdir' else ''}>Podkatalog o nazwie</option>
            </select>
            <div id="image-upload-subdir-section" ${'class="hidden"' if preferences.image_upload_mode != 'subdir' else '' | n}>
              <input id="image-upload-subdir-input" class="settings-input" type="text" value="${preferences.image_upload_subdir}" placeholder="e.g. assets" />
            </div>
          </section>

        </div>
      </div>

      <footer class="modal-actions">
        <button id="cancel-settings" class="button button-secondary" type="button" data-i18n="cancel">Cancel</button>
        <button id="save-settings" class="button button-primary" type="button" data-i18n="save_settings">Zapisz ustawienia</button>
      </footer>
    </section>
  </div>

  <div id="directory-browser-modal" class="modal-backdrop hidden" aria-hidden="true">
    <section class="modal-card modal-card-wide" role="dialog" aria-modal="true" aria-labelledby="directory-browser-title">
      <header class="modal-header">
        <div>
          <div class="label">Pick a folder</div>
          <h3 id="directory-browser-title">Folder browser</h3>
        </div>
        <button id="close-directory-browser" class="icon-button" type="button" aria-label="Close folder browser">X</button>
      </header>

      <div class="modal-content">
        <div class="directory-browser-current">
          <div class="settings-label">Biezaca lokalizacja</div>
          <div id="directory-browser-current-path" class="directory-browser-path"></div>
        </div>

        <div class="directory-browser-actions">
          <button id="directory-browser-up" class="button button-secondary button-sm" type="button"><svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="8,12 8,4"/><polyline points="4,8 8,4 12,8"/></svg>Poziom wyzej</button>
          <button id="directory-browser-new" class="button button-secondary button-sm" type="button"><svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 4.5A1.5 1.5 0 0 1 3.5 3h3.586a1 1 0 0 1 .707.293l.914.914A1 1 0 0 0 9.414 4.5H12.5A1.5 1.5 0 0 1 14 6v6a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 2 12V4.5Z"/><line x1="8" y1="8" x2="8" y2="12"/><line x1="6" y1="10" x2="10" y2="10"/></svg>Nowy folder</button>
          <button id="directory-browser-select" class="button button-primary button-sm" type="button"><svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="3,8 6,11 13,4"/></svg>Pick</button>
        </div>

        <div id="directory-browser-create" class="directory-browser-create hidden">
          <input id="directory-browser-create-input" class="settings-input" type="text" placeholder="Nazwa nowego folderu" />
          <div class="directory-browser-create-actions">
            <button id="directory-browser-create-confirm" class="button button-primary" type="button">Utworz i wejdz</button>
            <button id="directory-browser-create-cancel" class="button button-secondary" type="button">Cancel</button>
          </div>
        </div>

        <div id="directory-browser-list" class="directory-browser-list" aria-live="polite"></div>
      </div>

      <footer class="modal-actions">
        <button id="cancel-directory-browser" class="button button-secondary" type="button">Cancel</button>
      </footer>
    </section>
  </div>

  <div id="history-modal" class="modal-backdrop hidden" aria-hidden="true">
    <section class="modal-card modal-card-history" role="dialog" aria-modal="true" aria-labelledby="history-title">
      <header class="modal-header">
        <div>
          <div class="label">Git</div>
          <h3 id="history-title">—</h3>
        </div>
        <button id="close-history" class="icon-button" type="button" aria-label="Close">X</button>
      </header>
      <div class="history-tabs">
        <button id="history-tab-log" class="history-tab is-active" type="button" data-i18n="history_tab_log">Historia</button>
        <button id="history-tab-blame" class="history-tab" type="button" data-i18n="history_tab_blame">Autorzy linii</button>
      </div>
      <div class="modal-content history-content">
        <div id="history-log-view"></div>
        <div id="history-blame-view" class="hidden"></div>
      </div>
    </section>
  </div>

  <div id="create-modal" class="modal-backdrop hidden" aria-hidden="true">
    <section class="modal-card" role="dialog" aria-modal="true" aria-labelledby="create-title">
      <header class="modal-header">
        <div>
          <div class="label">Create</div>
          <h3 id="create-title">Nowy element</h3>
        </div>
        <button id="close-create" class="icon-button" type="button" aria-label="Close">X</button>
      </header>

      <div class="modal-content">
        <p id="create-parent-label" class="muted small-note">Location: root</p>

        <label class="settings-label" for="create-name-input">Nazwa</label>
        <input id="create-name-input" class="settings-input" type="text" placeholder="np. Notatka albo Projekty" />
        <p id="create-hint" class="muted small-note">Dla pliku rozszerzenie `.md` zostanie dodane automatycznie, jesli go nie podasz.</p>
      </div>

      <footer class="modal-actions">
        <button id="cancel-create" class="button button-secondary" type="button">Cancel</button>
        <button id="confirm-create" class="button button-primary" type="button">Utworz</button>
      </footer>
    </section>
  </div>
</%def>

<%def name="scripts_extra()">
<%
    _is_public = bool(context.get('public_view'))
%>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
% if not _is_public:
  <script src="https://uicdn.toast.com/editor/latest/toastui-editor-all.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/jsoneditor@9/dist/jsoneditor.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/codemirror.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/mode/meta.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/addon/mode/loadmode.min.js"></script>
% endif
  <script defer src="${request.url_for('static', path='app.js')}?v=${static_version}"></script>
</%def>

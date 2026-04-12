<%inherit file="/views/base.mako"/>

<%def name="page_title()">Logowanie | Noteeli</%def>

<%def name="content()">
  <main class="login-shell">
    <section class="login-card">
      <span class="eyebrow">Markdown Workspace</span>
      <h1>Noteeli</h1>
      <p class="login-copy">
        Aplikacja pokazuje drzewo plikow z wybranego katalogu i pozwala edytowac notatki Markdown po zalogowaniu przez Google.
      </p>

      % if error_message:
        <div class="alert alert-error">${error_message}</div>
      % endif

      % if google_configured:
        <a class="button button-primary button-large" href="${request.url_for('auth_google_login')}">
          Zaloguj sie przez Google
        </a>
      % else:
        <div class="alert">
          Logowanie Google nie jest skonfigurowane. Ustaw `NOTEELI_GOOGLE_CLIENT_ID` i `NOTEELI_GOOGLE_CLIENT_SECRET`.
        </div>
      % endif

      <p class="login-hint">
        Wejscie przez `127.0.0.1`, `localhost` albo `::1` pomija logowanie i otwiera aplikacje od razu.
      </p>
    </section>
  </main>
</%def>

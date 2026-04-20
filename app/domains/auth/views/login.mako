<%inherit file="/views/base.mako"/>

<%def name="page_title()">NoteEli</%def>

<%def name="content()">
  <main class="login-shell">
    <div class="login-center">
      <h1 class="login-wordmark">NoteEli</h1>

      <div class="login-actions">
        % if error_message:
          <p class="login-error">${error_message}</p>
        % endif

        % if google_configured:
          <a class="login-google-btn" href="${request.url_for('auth_google_login')}">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Continue with Google
          </a>
        % else:
          <span class="login-unconfigured">—</span>
        % endif

        % if password_configured:
          <details class="login-password-details" ${'open' if error_message else ''}>
            <summary class="login-password-summary">
              <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
                <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>
              </svg>
              Login with password
            </summary>
            <form class="login-password-form" method="post" action="${request.url_for('auth_password_login')}">
              <label class="login-field">
                <span>Username</span>
                <input type="text" name="username" autocomplete="username" required />
              </label>
              <label class="login-field">
                <span>Password</span>
                <input type="password" name="password" autocomplete="current-password" required />
              </label>
              <button class="login-submit-btn" type="submit">Sign in</button>
            </form>
          </details>
        % endif
      </div>
    </div>
  </main>
</%def>

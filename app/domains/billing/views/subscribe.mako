<%inherit file="/views/base.mako"/>

<%def name="page_title()">Subscribe — Noteeli</%def>

<%def name="content()">
<div class="subscribe-shell">
  <div class="subscribe-card">
    <div class="subscribe-logo">
      <img src="${request.url_for('static', path='favicon.svg')}" alt="Noteeli" width="48" height="48" />
    </div>
    <h1 class="subscribe-title">Noteeli</h1>
    <p class="subscribe-tagline">Your Markdown workspace in the browser</p>

    <div class="subscribe-plan">
      <div class="subscribe-plan-name">Pro</div>
      <div class="subscribe-plan-price">
        <span class="subscribe-plan-amount">€5</span>
        <span class="subscribe-plan-period">/ month</span>
      </div>
      <ul class="subscribe-features">
        <li>SFTP storage — connect your own server</li>
        <li>Google Drive storage</li>
        <li>Full Markdown editor (WYSIWYG + source)</li>
        <li>Publish notes as public read-only pages</li>
        <li>All future features included</li>
      </ul>
    </div>

    <form method="post" action="${request.url_for('billing_checkout')}">
      <button type="submit" class="subscribe-btn">
        Subscribe with Paddle
      </button>
    </form>

    % if user_email:
    <p class="subscribe-account">Logged in as <strong>${user_email}</strong></p>
    % endif

    <p class="subscribe-footer">
      Payments handled by <a href="https://paddle.com" target="_blank" rel="noopener">Paddle</a>.
      Cancel any time — no lock-in.
    </p>
  </div>
</div>
</%def>

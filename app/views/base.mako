<!doctype html>
<html lang="pl">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <script>
      // Service-worker self-heal — runs from the always-fresh (no-store)
      // HTML shell on every page load, BEFORE app.js. Noteeli no longer
      // ships a service worker; a stale one from an older PWA install can
      // pin outdated assets and, on iOS/Safari especially, resists the
      // kill-switch SW's own lazy update cycle. Because this lives in the
      // HTML (not in app.js, which may itself be served stale), it reaches
      // clients that the app.js cleanup never could. It unregisters every
      // SW, purges Cache Storage, then reloads once (guarded — no loop).
      (function () {
        if (!("serviceWorker" in navigator)) return;
        navigator.serviceWorker.getRegistrations().then(function (regs) {
          if (!regs.length) return;
          Promise.all(regs.map(function (r) { return r.unregister(); }))
            .then(function () {
              if (window.caches && caches.keys) {
                return caches.keys().then(function (keys) {
                  return Promise.all(keys.map(function (k) { return caches.delete(k); }));
                });
              }
            })
            .then(function () {
              if (!sessionStorage.getItem("sw-nuked")) {
                sessionStorage.setItem("sw-nuked", "1");
                location.reload();
              }
            })
            .catch(function () {});
        }).catch(function () {});
      })();
    </script>
    <title>${self.page_title()}</title>
    <link rel="icon" type="image/svg+xml" href="${request.url_for('static', path='favicon.svg')}" />
    <link rel="stylesheet" href="${request.url_for('static', path='app.css')}?v=${static_version}" />
    ${self.head_extra()}
  </head>
  <body data-theme="${self.initial_theme()}">
    ${self.content()}
    ${self.scripts_extra()}
  </body>
</html>

<%def name="page_title()">Noteeli</%def>
<%def name="head_extra()"></%def>
<%def name="scripts_extra()"></%def>
<%def name="initial_theme()">noteeli</%def>

<!doctype html>
<html lang="pl">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${self.page_title()}</title>
    <link rel="icon" type="image/svg+xml" href="${request.url_for('static', path='favicon.svg')}" />
    <link rel="manifest" href="/manifest.webmanifest" />
    <meta name="theme-color" content="#0b1220" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
    <meta name="apple-mobile-web-app-title" content="Noteeli" />
    <link rel="apple-touch-icon" href="${request.url_for('static', path='icon-192.png')}" />
    <link rel="stylesheet" href="${request.url_for('static', path='app.css')}" />
    ${self.head_extra()}
  </head>
  <body>
    ${self.content()}
    ${self.scripts_extra()}
  </body>
</html>

<%def name="page_title()">Noteeli</%def>
<%def name="head_extra()"></%def>
<%def name="scripts_extra()"></%def>

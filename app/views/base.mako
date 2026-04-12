<!doctype html>
<html lang="pl">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${self.page_title()}</title>
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

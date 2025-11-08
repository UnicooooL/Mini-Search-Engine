<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>ECE326 Lab 2</title>
    <link rel="stylesheet" href="/static/main.css">
  </head>
  <body>
    <header>
      <h1>ECE326 Search</h1>
      % if email:
        <div class="user">Signed in as {{email}}</div>
        <form method="post" action="/logout"><button>Sign out</button></form>
      % end
    </header>
    <main>
      {{!base}}
    </main>
  </body>
</html>

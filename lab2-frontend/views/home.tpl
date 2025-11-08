% rebase('base', email=email)
% if email:
  <form method="post" action="/search" class="row">
    <input name="q" placeholder="Search term" required>
    <button>Search</button>
  </form>

  <h3>Your recent searches</h3>
  % if qs:
    <ul>
      % for x in qs:
        <li>{{x}}</li>
      % end
    </ul>
  % else:
    <p>(No history yet)</p>
  % end
% else:
  <p><b>Anonymous mode</b></p>
  <form method="post" action="/search" class="row">
    <input name="q" placeholder="Search term" required>
    <button>Search</button>
  </form>
  <p style="margin-top:1rem">
    <a href="/login"><button type="button">Sign in with Google</button></a>
  </p>
% end

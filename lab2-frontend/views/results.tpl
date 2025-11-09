% rebase('base', email=email)

<h2>Search Results for "{{q}}"</h2>

<form method="post" action="/search" class="row" style="margin-bottom: 1rem;">
  <input name="q" placeholder="Search term" required>
  <button>Search</button>
</form>

% if not results:
  <p>No results found for "{{q}}".</p>
% else:
  <ul>
  % for r in results:
    <li>
      <a href="{{r['url']}}" target="_blank">{{r['url']}}</a>
      <span> — PageRank: {{r['pagerank']}}</span>
    </li>
  % end
  </ul>


  <p>
	% if total_pages > 1:
	<div class="pagination">
		% if has_prev:
		<a href="/search?q={{q}}&page={{page-1}}">&laquo; Previous</a>
		% end

		% for p in pages:
		% if p == page:
			<span class="current">{{p}}</span>
		% else:
			<a href="/search?q={{q}}&page={{p}}">{{p}}</a>
		% end
		% end

		% if has_next:
		<a href="/search?q={{q}}&page={{page+1}}">Next &raquo;</a>
		% end
	</div>
	% end
	
<p><a href="/">Back</a></p>

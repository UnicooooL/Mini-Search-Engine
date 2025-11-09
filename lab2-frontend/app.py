from bottle import Bottle, request, redirect, template, static_file, error
from beaker.middleware import SessionMiddleware
from oauth2client.client import flow_from_clientsecrets
from googleapiclient.discovery import build
import httplib2, sqlite3, os, json

with open('search_data.json', 'r') as f:
    DATA = json.load(f)
    
APP = Bottle()

# OAuth config — must match your Google Cloud OAuth client.
REDIRECT_URI   = 'http://localhost:8080/redirect'  # HTTP for local dev
CLIENT_SECRETS = 'client_secret.json'               # downloaded JSON
DB_PATH        = 'history.db'                       # per-user history
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEARCH_DB_PATH = os.path.join(BASE_DIR, '..', 'backend', 'search.db')

# ---------------- History (per user, keep last 10) ----------------

def init_db():
    """Ensure the history table exists"""
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS history(
              user_id TEXT,
              query   TEXT,
              ts      DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

def add_query(user_id, q):
    """Record one query for this user and trim to the 10 most recent"""
    if not (user_id and q):
        return
    with sqlite3.connect(DB_PATH) as con:
        con.execute("INSERT INTO history(user_id, query) VALUES(?,?)", (user_id, q))
        # Keep newest 10 for this user
        con.execute("""
          DELETE FROM history
          WHERE user_id=? AND rowid NOT IN (
            SELECT rowid FROM history
            WHERE user_id=?
            ORDER BY ts DESC
            LIMIT 10
          )
        """, (user_id, user_id))

def recent_queries(user_id):
    """Fetch up to 10 recent queries for UI display (newest first)."""
    if not user_id:
        return []
    with sqlite3.connect(DB_PATH) as con:
        # .execute runs the SQL; iterating rows returns tuples, r[0] is 'query'
        return [r[0] for r in con.execute(
            "SELECT query FROM history WHERE user_id=? ORDER BY ts DESC LIMIT 10",
            (user_id,)
        )]

# --------------- Lab 1 placeholder (TOD: will replace) ---------------

def run_query(q: str):
    """
    Use only the first word in the query.
    Search against backend/search.db using:
      Lexicon(word_id, word)
      InvertedIndex(word_id, doc_id)
      Documents(doc_id, url, title, description)
      PageRank(doc_id, score)
    Return a list of {url, pagerank} sorted by pagerank (desc).
    """
    if not q:
        return []

    
    term = q.strip().split()[0].lower()

    con = sqlite3.connect(SEARCH_DB_PATH)
    cur = con.cursor()

    cur.execute("SELECT word_id FROM Lexicon WHERE lower(word) = ?", (term,))
    rows = cur.fetchall()
    if not rows:
        con.close()
        return []
    word_ids = [r[0] for r in rows]

    placeholders = ",".join("?" for _ in word_ids)
    cur.execute(
        f"SELECT DISTINCT doc_id FROM InvertedIndex WHERE word_id IN ({placeholders})",
        word_ids,
    )
    doc_rows = cur.fetchall()
    if not doc_rows:
        con.close()
        return []
    doc_ids = [r[0] for r in doc_rows]

    placeholders = ",".join("?" for _ in doc_ids)
    cur.execute(
        f"""
        SELECT d.url, p.score
        FROM Documents AS d
        JOIN PageRank AS p ON d.doc_id = p.doc_id
        WHERE d.doc_id IN ({placeholders})
        ORDER BY p.score DESC
        """,
        doc_ids,
    )
    results_rows = cur.fetchall()
    con.close()

    results = [
        {"url": url, "pagerank": float(score)}
        for (url, score) in results_rows
    ]
    return results



# ------------------------------- Routes -------------------------------

@APP.get('/')
def home():
    """Home page — shows email + history if signed in, else anonymous view."""
    s = request.environ['beaker.session']
    email = s.get('email')
    qs = recent_queries(s.get('sub'))
    return template('home', email=email, qs=qs)

@APP.route('/search', method=['GET', 'POST'])
def do_search():
    s = request.environ['beaker.session']

    if request.method == 'POST':
        raw_q = request.forms.get('q', '').strip()
        page = 1
    else:
        raw_q = request.query.get('q', '').strip()
        try:
            page = int(request.query.get('page', '1') or 1)
        except ValueError:
            page = 1

    if page < 1:
        page = 1
        
    term = raw_q.split()[0] if raw_q else ""

    if s.get('sub') and raw_q and page == 1:
        add_query(s['sub'], raw_q)

    all_results = run_query(term) if term else []

    PAGE_SIZE = 5
    total = len(all_results)
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE  # 向上取整

    if page > total_pages and total_pages > 0:
        page = total_pages

    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    results = all_results[start:end]

    has_next = page < total_pages
    has_prev = page > 1
    pages = list(range(1, total_pages + 1))  # [1,2,3,...]


    return template(
        'results',
        email=s.get('email'),
        q=term,
        results=results,
        page=page,
        has_next=has_next,
        has_prev=has_prev,
        pages=pages,
        total_pages=total_pages,
    )


@APP.get('/login')
def login():
    """Kick off Google OAuth by redirecting to the consent page"""
    flow = flow_from_clientsecrets(
        CLIENT_SECRETS,
        scope=['profile', 'email'],
        redirect_uri=REDIRECT_URI
    )
    url = flow.step1_get_authorize_url()
    print("AUTH URL:", url)
    return redirect(url)

@APP.get('/redirect')
def oauth_redirect():
    """
    OAuth callback: exchange ?code for credentials, fetch user info,
    stash email + stable user id ('sub') in session, then go home.
    """
    code = request.query.get('code')
    if not code:
        return redirect('/')

    # Exchange 'code' -> credentials (access token + id_token)
    creds = flow_from_clientsecrets(
        CLIENT_SECRETS, scope=['profile', 'email'], redirect_uri=REDIRECT_URI
    ).step2_exchange(code)

    # Build authorized client and call Google UserInfo API
    http = httplib2.Http()
    authed = creds.authorize(http)
    users = build('oauth2', 'v2', http=authed)
    info = users.userinfo().get().execute()  # executes HTTP; returns dict

    # Persist identity in server-side session
    s = request.environ['beaker.session']
    s['email'] = info.get('email')
    s['sub']   = creds.id_token.get('sub') or info.get('id')
    s.save()
    return redirect('/')

@APP.post('/logout')
def logout():
    """Local sign-out: clear session """
    s = request.environ['beaker.session']
    s.delete()
    return redirect('/')

@APP.get('/static/<path:path>')
def static(path):
    """Serve CSS/images during dev."""
    return static_file(path, root='./static')

@APP.error(404)
def error404(e):
    s = request.environ.get('beaker.session')
    email = s.get('email') if s else None
    return template('error', email=email)

@APP.error(405)
def error405(e):
    s = request.environ.get('beaker.session')
    email = s.get('email') if s else None
    return template('error', email=email)

if __name__ == '__main__':
    init_db()
    session_opts = {
        'session.type': 'file',
        'session.data_dir': './.sessions',
        'session.auto': True,
        'session.cookie_expires': True,
        'session.secure': False,  # HTTP on localhost
    }
    app = SessionMiddleware(APP, session_opts)
    from bottle import run
    run(app=app, host='0.0.0.0', port=8080, debug=True, reloader=True)

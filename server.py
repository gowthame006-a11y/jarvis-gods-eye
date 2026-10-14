"""Dependency-free local application server with SQLite and session authentication."""
import os, json, sqlite3, secrets, hashlib, hmac, time
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from domain import dispatch, initialize
ROOT=Path(__file__).parent
DB=os.environ.get('APP_DB',str(ROOT/'app.sqlite3'))
SESSIONS={}
def connect():
    db=sqlite3.connect(DB); db.row_factory=sqlite3.Row; return db
def password_hash(password,salt):
    return hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),200000).hex()
def setup():
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,username TEXT UNIQUE,salt TEXT,password TEXT,role TEXT)')
        if not db.execute('SELECT 1 FROM users').fetchone():
            password=os.environ.get('DEMO_PASSWORD') or secrets.token_urlsafe(12)
            for username,role in [('employee','employee'),('manager','manager')]:
                salt=secrets.token_hex(16)
                db.execute('INSERT INTO users(name,username,salt,password,role) VALUES(?,?,?,?,?)',(username.title(),username,salt,password_hash(password,salt),role))
            print('FIRST RUN credentials: employee / manager; password:',password,flush=True)
        initialize(db)
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send(self,status,data):
        raw=json.dumps(data).encode(); self.send_response(status)
        self.send_header('Content-Type','application/json'); self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(raw)
    def do_GET(self): self.handle_request()
    def do_POST(self): self.handle_request()
    def handle_request(self):
        path=urlparse(self.path).path
        if path=='/' and self.command=='GET':
            raw=(ROOT/'static/index.html').read_bytes(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.end_headers(); self.wfile.write(raw); return
        if not path.startswith('/api/'): return self.send(404,{'error':'Not found'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>1000000: return self.send(413,{'error':'Request too large'})
            data=json.loads(self.rfile.read(length) or b'{}')
            if not isinstance(data,dict): raise ValueError('JSON object required')
            with connect() as db:
                if path=='/api/login' and self.command=='POST':
                    row=db.execute('SELECT * FROM users WHERE username=?',(data.get('username'),)).fetchone()
                    if not row or not hmac.compare_digest(row['password'],password_hash(str(data.get('password','')),row['salt'])): return self.send(401,{'error':'Invalid credentials'})
                    token=secrets.token_urlsafe(32); SESSIONS[token]=(row['id'],time.time()+28800)
                    return self.send(200,{'token':token,'name':row['name'],'role':row['role']})
                token=self.headers.get('Authorization','').removeprefix('Bearer ')
                session=SESSIONS.get(token)
                if not session or session[1]<time.time(): return self.send(401,{'error':'Login required'})
                user=dict(db.execute('SELECT id,name,role FROM users WHERE id=?',(session[0],)).fetchone())
                if path=='/api/logout' and self.command=='POST': SESSIONS.pop(token,None); return self.send(200,{'ok':True})
                result=dispatch(db,user,self.command,path,data)
                self.send(200,result)
        except PermissionError as exc: self.send(403,{'error':str(exc)})
        except (ValueError,KeyError,TypeError,json.JSONDecodeError) as exc: self.send(400,{'error':str(exc)})
        except Exception:
            import traceback; traceback.print_exc(); self.send(500,{'error':'Internal server error'})
if __name__=='__main__':
    setup(); port=int(os.environ.get('PORT','8000')); print(f'Open http://127.0.0.1:{port}',flush=True)
    ThreadingHTTPServer((os.environ.get('BIND_HOST','127.0.0.1'),port),Handler).serve_forever()

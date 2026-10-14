import unittest,sqlite3
from domain import initialize,dispatch
class DomainTest(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:'); self.db.row_factory=sqlite3.Row
        self.db.execute('CREATE TABLE users(id INTEGER PRIMARY KEY,name TEXT)')
        self.db.executemany('INSERT INTO users VALUES(?,?)',[(1,'Employee'),(2,'Manager')])
        initialize(self.db); self.user={'id':1,'role':'employee'}; self.manager={'id':2,'role':'manager'}
    def tearDown(self): self.db.close()
    def test_commands_task_ownership_and_simulation(self):
        dispatch(self.db,self.user,'POST','/api/chat',{'message':'add task Build demo'})
        dispatch(self.db,self.manager,'POST','/api/toggle',{'id':1})
        self.assertEqual(dispatch(self.db,self.user,'GET','/api/dashboard',{})['tasks'][0]['done'],0)
        dispatch(self.db,self.user,'POST','/api/toggle',{'id':1})
        self.assertEqual(dispatch(self.db,self.user,'GET','/api/dashboard',{})['tasks'][0]['done'],1)
        dispatch(self.db,self.user,'POST','/api/simulate',{})
        d=dispatch(self.db,self.user,'GET','/api/dashboard',{})
        self.assertEqual(len(d['vehicles']),2); self.assertEqual(len(d['events']),1)
    def test_blank_task_rejected(self):
        with self.assertRaises(ValueError): dispatch(self.db,self.user,'POST','/api/task',{'title':' '})
import tempfile,threading,json,urllib.request,urllib.error,os
from pathlib import Path
import server
class HTTPTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();server.DB=str(Path(self.temp.name)/'test.sqlite3')
        os.environ['DEMO_PASSWORD']='test-password';server.setup()
        self.http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
        self.url='http://127.0.0.1:'+str(self.http.server_port)
    def tearDown(self):
        self.http.shutdown();self.http.server_close();self.thread.join();self.temp.cleanup()
    def request(self,path,data=None,token=''):
        req=urllib.request.Request(self.url+path,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        return urllib.request.urlopen(req)
    def test_login_protected_dashboard_and_logout(self):
        with self.assertRaises(urllib.error.HTTPError) as err: self.request('/api/dashboard')
        self.assertEqual(err.exception.code,401)
        with self.assertRaises(urllib.error.HTTPError): self.request('/api/login',{'username':'employee','password':'wrong'})
        token=json.load(self.request('/api/login',{'username':'employee','password':'test-password'}))['token']
        self.assertEqual(self.request('/api/dashboard',token=token).status,200)
        self.request('/api/logout',{},token)
        with self.assertRaises(urllib.error.HTTPError): self.request('/api/dashboard',token=token)
        self.assertIn(b'<html',self.request('/').read())

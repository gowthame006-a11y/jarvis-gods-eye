from datetime import datetime,timezone
import random
VEHICLES=[{'id':'BIKE-01','lat':13.1143,'lon':80.1548,'speed':32},{'id':'CAR-02','lat':13.0827,'lon':80.2707,'speed':24}]
def initialize(db):
    db.execute('CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY,user_id INTEGER,title TEXT,done INTEGER DEFAULT 0)')
    db.execute('CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,user_id INTEGER,message TEXT,created TEXT)')
def dispatch(db,user,method,path,data):
    if path=='/api/dashboard' and method=='GET':
        return {'tasks':[dict(r) for r in db.execute('SELECT * FROM tasks WHERE user_id=? ORDER BY id DESC',(user['id'],))],'events':[dict(r) for r in db.execute('SELECT * FROM events WHERE user_id=? ORDER BY id DESC LIMIT 30',(user['id'],))],'vehicles':VEHICLES,'mode':'Simulation — synthetic locations; no live surveillance'}
    if path=='/api/task' and method=='POST':
        title=str(data['title']).strip()
        if not title or len(title)>200: raise ValueError('Task must contain 1–200 characters')
        db.execute('INSERT INTO tasks(user_id,title) VALUES(?,?)',(user['id'],title)); return {'ok':True}
    if path=='/api/toggle' and method=='POST':
        db.execute('UPDATE tasks SET done=1-done WHERE id=? AND user_id=?',(data['id'],user['id'])); return {'ok':True}
    if path=='/api/simulate' and method=='POST':
        # Simulation is shared across sessions and intentionally not persisted.
        for v in VEHICLES: v['lat']+=random.uniform(-.001,.001); v['lon']+=random.uniform(-.001,.001); v['speed']=random.randint(0,55)
        message='Simulation advanced: '+', '.join(v['id']+' '+str(v['speed'])+' km/h' for v in VEHICLES)
        db.execute('INSERT INTO events(user_id,message,created) VALUES(?,?,?)',(user['id'],message,datetime.now(timezone.utc).isoformat())); return {'ok':True}
    if path=='/api/chat' and method=='POST':
        message=str(data['message']).strip()
        if not message or len(message)>1000: raise ValueError('Message must contain 1–1000 characters')
        low=message.lower()
        if low.startswith('add task '): return dispatch(db,user,'POST','/api/task',{'title':message[9:]}) | {'reply':'Task created.'}
        if 'time' in low: reply='UTC time: '+datetime.now(timezone.utc).strftime('%H:%M:%S')
        elif 'task' in low: reply='You have '+str(db.execute('SELECT COUNT(*) FROM tasks WHERE user_id=? AND done=0',(user['id'],)).fetchone()[0])+' open tasks.'
        elif 'vehicle' in low or 'status' in low: reply='Two simulated vehicles available. Select Advance simulation to update positions.'
        else: reply='Available commands: add task <title>, show tasks, vehicle status, time. This offline command assistant does not call an LLM.'
        return {'reply':reply}
    raise ValueError('Unknown operation')

import os, sqlite3, hashlib, re, json
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from production import make_video, PipelineError

ROOT=Path(__file__).parent
OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
DB=ROOT/'tao.db'
FEEDS=[('TechCrunch','https://techcrunch.com/feed/'),('The Verge','https://www.theverge.com/rss/index.xml'),('Hacker News','https://hnrss.org/frontpage')]
WISDOM=[
 ('知人者智，自知者明。','Knowing others is intelligence; knowing yourself is true clarity.','Dao De Jing 33','Self-knowledge matters more than technological power.'),
 ('千里之行，始於足下。','A journey of a thousand miles begins beneath your feet.','Dao De Jing 64','Lasting progress begins with small deliberate steps.'),
 ('知足不辱，知止不殆。','Knowing contentment avoids disgrace; knowing when to stop avoids danger.','Dao De Jing 44','Progress needs limits as much as ambition.'),
 ('上善若水。','The highest goodness is like water.','Dao De Jing 8','Adaptability can be stronger than force.')]
app=FastAPI(title='Tao Tech Daily')
def db():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
with db() as c:
 c.execute('CREATE TABLE IF NOT EXISTS stories(id INTEGER PRIMARY KEY,headline TEXT,source TEXT,url TEXT UNIQUE,quote TEXT,translation TEXT,chapter TEXT,insight TEXT,script TEXT,status TEXT DEFAULT "draft",video TEXT,created TEXT)')
 c.execute('CREATE TABLE IF NOT EXISTS reviews(story_id INTEGER PRIMARY KEY,verified INTEGER DEFAULT 0,quote_checked INTEGER DEFAULT 0,approved INTEGER DEFAULT 0,note TEXT DEFAULT "")')
def admin(x_admin_token:str|None=Header(None)):
 token=os.getenv('STUDIO_ADMIN_TOKEN')
 if not token or x_admin_token!=token:raise HTTPException(401,'Set STUDIO_ADMIN_TOKEN and supply X-Admin-Token')
@app.post('/api/ingest',dependencies=[Depends(admin)])
def ingest():
 added=0
 with db() as c:
  for source,url in FEEDS:
   try:
    xml=urlopen(Request(url,headers={'User-Agent':'TaoTechDaily/1.0'}),timeout=12).read()
    for item in ET.fromstring(xml).findall('.//item')[:10]:
     title=item.findtext('title','').strip();link=item.findtext('link','').strip()
     if not title or not link:continue
     q,t,ch,ins=WISDOM[int(hashlib.sha256(title.encode()).hexdigest(),16)%len(WISDOM)]
     script=f'Today in technology: {title}. But what does progress really mean? Laozi wrote: {t} {ins} The future needs wisdom, not just speed.'
     added+=c.execute('INSERT OR IGNORE INTO stories(headline,source,url,quote,translation,chapter,insight,script,created) VALUES(?,?,?,?,?,?,?,?,?)',(title,source,link,q,t,ch,ins,script,datetime.now(timezone.utc).isoformat())).rowcount
   except Exception as exc:print('Feed failed',source,exc)
 return {'added':added,'warning':'Verify source article and Taoist translation before approval'}
@app.get('/api/stories')
def stories():
 with db() as c:return [dict(x) for x in c.execute('SELECT s.*,COALESCE(r.verified,0) verified,COALESCE(r.quote_checked,0) quote_checked,COALESCE(r.approved,0) approved FROM stories s LEFT JOIN reviews r ON s.id=r.story_id ORDER BY s.id DESC LIMIT 100')]
class Edit(BaseModel):
 quote:str|None=None;translation:str|None=None;chapter:str|None=None;insight:str|None=None;script:str|None=None
@app.patch('/api/stories/{id}',dependencies=[Depends(admin)])
def edit(id:int,body:Edit):
 fields=body.model_dump(exclude_none=True)
 with db() as c:
  if not c.execute('SELECT id FROM stories WHERE id=?',(id,)).fetchone():raise HTTPException(404)
  if fields:c.execute('UPDATE stories SET '+','.join(k+'=?' for k in fields)+' WHERE id=?',(*fields.values(),id))
  c.execute('INSERT OR IGNORE INTO reviews(story_id) VALUES(?)',(id,))
  c.execute('UPDATE reviews SET approved=0 WHERE story_id=?',(id,))
 return {'ok':True}
class Review(BaseModel):
 verified:bool=False;quote_checked:bool=False;approved:bool=False
@app.post('/api/stories/{id}/review',dependencies=[Depends(admin)])
def review(id:int,body:Review):
 if body.approved and not (body.verified and body.quote_checked):raise HTTPException(400,'Both factual and quote verification required')
 with db() as c:
  if not c.execute('SELECT id FROM stories WHERE id=?',(id,)).fetchone():raise HTTPException(404)
  c.execute('INSERT OR REPLACE INTO reviews(story_id,verified,quote_checked,approved) VALUES(?,?,?,?)',(id,int(body.verified),int(body.quote_checked),int(body.approved)))
 return {'ok':True}
@app.post('/api/stories/{id}/render',dependencies=[Depends(admin)])
def render(id:int,mode:str='preview'):
 with db() as c:row=c.execute('SELECT * FROM stories WHERE id=?',(id,)).fetchone()
 if not row:raise HTTPException(404)
 try:result=make_video(dict(row),mode)
 except PipelineError as exc:raise HTTPException(400,str(exc))
 with db() as c:
  c.execute('UPDATE stories SET video=?,status="draft" WHERE id=?',(result['video'].split('/')[-1],id))
  c.execute('UPDATE reviews SET approved=0 WHERE story_id=?',(id,))
 return result
@app.post('/api/stories/{id}/publish',dependencies=[Depends(admin)])
def publish(id:int):
 with db() as c:
  r=c.execute('SELECT s.video,COALESCE(v.approved,0) approved FROM stories s LEFT JOIN reviews v ON v.story_id=s.id WHERE s.id=?',(id,)).fetchone()
  if not r:raise HTTPException(404)
  if not r['video'] or not r['approved']:raise HTTPException(403,'Render and approve before publishing')
  c.execute('UPDATE stories SET status="published" WHERE id=?',(id,))
 return {'ok':True}
@app.get('/videos/{name}')
def video(name:str):
 if not re.fullmatch(r'tao_\d+\.mp4',name):raise HTTPException(404)
 path=OUT/name
 if not path.is_file():raise HTTPException(404)
 return FileResponse(path,media_type='video/mp4')
@app.get('/',response_class=HTMLResponse)
def home():return (ROOT/'static/index.html').read_text()
@app.get('/watch',response_class=HTMLResponse)
def watch():return (ROOT/'static/watch.html').read_text()

"""Private local editorial workflow; never exposed through the public web server."""
import argparse, hashlib, sqlite3, sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
import xml.etree.ElementTree as ET
from production import make_video,PipelineError
ROOT=Path(__file__).parent;DB=ROOT/'tao.db'
FEEDS=[('TechCrunch','https://techcrunch.com/feed/'),('The Verge','https://www.theverge.com/rss/index.xml'),('Hacker News','https://hnrss.org/frontpage')]
WISDOM=[
('知人者智，自知者明。','Knowing others is intelligence; knowing yourself is true clarity.','Dao De Jing 33','Self-knowledge matters more than technological power.'),
('千里之行，始於足下。','A journey of a thousand miles begins beneath your feet.','Dao De Jing 64','Lasting progress begins with small deliberate steps.'),
('知足不辱，知止不殆。','Knowing contentment avoids disgrace; knowing when to stop avoids danger.','Dao De Jing 44','Progress needs limits as much as ambition.'),
('上善若水。','The highest goodness is like water.','Dao De Jing 8','Adaptability can be stronger than force.')]
def connect():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
 c.execute('CREATE TABLE IF NOT EXISTS stories(id INTEGER PRIMARY KEY,headline TEXT,source TEXT,url TEXT UNIQUE,quote TEXT,translation TEXT,chapter TEXT,insight TEXT,script TEXT,status TEXT DEFAULT "draft",video TEXT,created TEXT)')
 c.execute('CREATE TABLE IF NOT EXISTS reviews(story_id INTEGER PRIMARY KEY,verified INTEGER DEFAULT 0,quote_checked INTEGER DEFAULT 0,approved INTEGER DEFAULT 0,note TEXT DEFAULT "")')
 return c
def get(c,id):
 row=c.execute('SELECT * FROM stories WHERE id=?',(id,)).fetchone()
 if not row:raise ValueError('Story not found: '+str(id))
 return row
def ingest(c):
 count=0
 for source,url in FEEDS:
  try:
   data=urlopen(Request(url,headers={'User-Agent':'TaoTechDaily/2.0'}),timeout=15).read()
   for item in ET.fromstring(data).findall('.//item')[:10]:
    headline=item.findtext('title','').strip();link=item.findtext('link','').strip()
    if not headline or not link:continue
    quote,translation,chapter,insight=WISDOM[int(hashlib.sha256(headline.encode()).hexdigest(),16)%len(WISDOM)]
    script=f'Today in technology: {headline}. But what does progress really mean? Laozi wrote: {translation} {insight} The future needs wisdom, not just speed.'
    count+=c.execute('INSERT OR IGNORE INTO stories(headline,source,url,quote,translation,chapter,insight,script,created) VALUES(?,?,?,?,?,?,?,?,?)',(headline,source,link,quote,translation,chapter,insight,script,datetime.now(timezone.utc).isoformat())).rowcount
  except Exception as e:print('Feed unavailable:',source,e)
 c.commit();print('Added',count,'stories. Verify article details before publication.')
def main():
 p=argparse.ArgumentParser(description='Private Tao Tech Daily production CLI')
 sub=p.add_subparsers(dest='command',required=True)
 sub.add_parser('ingest');sub.add_parser('list')
 for name in ('show','render','approve','publish'):
  cmd=sub.add_parser(name);cmd.add_argument('id',type=int)
  if name=='render':cmd.add_argument('--mode',choices=['preview','production'],default='preview')
 cmd=sub.add_parser('edit');cmd.add_argument('id',type=int)
 for field in ('script','quote','translation','chapter','insight'):cmd.add_argument('--'+field)
 a=p.parse_args()
 with connect() as c:
  if a.command=='ingest':ingest(c)
  elif a.command=='list':
   for r in c.execute('SELECT id,headline,status FROM stories ORDER BY id DESC LIMIT 30'):print(f"{r['id']:>3} [{r['status']}] {r['headline'][:90]}")
  elif a.command=='show':
   r=get(c,a.id)
   for k in r.keys():print(k+':',r[k])
  elif a.command=='edit':
   get(c,a.id);fields={k:getattr(a,k) for k in ('script','quote','translation','chapter','insight') if getattr(a,k) is not None}
   if not fields:raise ValueError('Provide at least one --script, --quote, --translation, --chapter or --insight')
   c.execute('UPDATE stories SET '+','.join(k+'=?' for k in fields)+' WHERE id=?',(*fields.values(),a.id))
   c.execute('INSERT OR IGNORE INTO reviews(story_id) VALUES(?)',(a.id,))
   c.execute('UPDATE reviews SET approved=0 WHERE story_id=?',(a.id,))
   c.commit();print('Updated. Previous approval revoked.')
  elif a.command=='render':
   r=get(c,a.id);result=make_video(dict(r),a.mode)
   c.execute('UPDATE stories SET video=?,status="draft" WHERE id=?',(Path(result['video']).name,a.id))
   c.execute('INSERT OR IGNORE INTO reviews(story_id) VALUES(?)',(a.id,))
   c.execute('UPDATE reviews SET approved=0 WHERE story_id=?',(a.id,))
   c.commit();print('Rendered:',result['video'],'— review before approving.')
  elif a.command=='approve':
   r=get(c,a.id)
   if not r['video'] or not (ROOT/'output'/r['video']).is_file():raise ValueError('Render a video first')
   print('Source:',r['url']);print('Quote:',r['quote'],r['translation'],r['chapter'])
   print('Video:',ROOT/'output'/r['video'])
   confirmation=input('Have you personally verified source facts, quotation, and video? Type APPROVE: ')
   if confirmation!='APPROVE':print('Not approved');return
   c.execute('INSERT OR REPLACE INTO reviews(story_id,verified,quote_checked,approved) VALUES(?,?,?,?)',(a.id,1,1,1))
   c.commit();print('Approved')
  elif a.command=='publish':
   r=get(c,a.id)
   approved=c.execute('SELECT approved FROM reviews WHERE story_id=?',(a.id,)).fetchone()
   if not approved or not approved['approved'] or not r['video'] or not (ROOT/'output'/r['video']).is_file():raise ValueError('Render and approve before publishing')
   c.execute('UPDATE stories SET status="published" WHERE id=?',(a.id,))
   c.commit();print('Published to local gallery')
if __name__=='__main__':
 try:main()
 except (ValueError,PipelineError) as e:print('Error:',e,file=sys.stderr);sys.exit(1)

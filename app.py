"""Public, read-only video gallery. Production is handled by studio.py CLI."""
import re, sqlite3
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse

ROOT=Path(__file__).parent
OUT=ROOT/'output'
DB=ROOT/'tao.db'
app=FastAPI(title='Tao Tech Daily — Video Gallery',docs_url=None,redoc_url=None)

@app.get('/api/videos')
def videos():
    if not DB.exists(): return []
    with sqlite3.connect(DB) as c:
        c.row_factory=sqlite3.Row
        rows=c.execute("""
          SELECT id,headline,source,url,quote,translation,chapter,insight,video,created
          FROM stories WHERE status='published' AND video IS NOT NULL
          ORDER BY id DESC LIMIT 100
        """).fetchall()
    return [dict(r) for r in rows if (OUT/r['video']).is_file()]

@app.get('/videos/{name}')
def video(name:str):
    if not re.fullmatch(r'tao_\d+\.mp4',name):raise HTTPException(404)
    if not DB.exists():raise HTTPException(404)
    with sqlite3.connect(DB) as c:
        found=c.execute("SELECT 1 FROM stories WHERE video=? AND status='published'",(name,)).fetchone()
    path=OUT/name
    if not found or not path.is_file():raise HTTPException(404)
    return FileResponse(path,media_type='video/mp4')

@app.get('/',response_class=HTMLResponse)
def home():return (ROOT/'static/watch.html').read_text()
@app.get('/watch',response_class=HTMLResponse)
def watch():return home()

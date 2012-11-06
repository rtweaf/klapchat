import uuid
import sqlite3
import crypt

from fastapi import FastAPI, Request, Form, Cookie
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from routers import ws
from sessions_manager import sessions

SALT = '$6$kKfYXf90JkYpGL85'


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['https://127.0.0.1:8000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.mount('/static', StaticFiles(directory='static'), name='static')
app.include_router(ws.router)

templates = Jinja2Templates(directory='templates')

conn: sqlite3.Connection = sqlite3.connect('db.sqlite')
cur: sqlite3.Cursor = conn.cursor()


@app.get('/favicon.ico')
async def icon(req: Request):
    return FileResponse('static/favicon.ico')


@app.get('/')
async def home(req: Request):
    return templates.TemplateResponse('index.html', {'request': req})


@app.get('/login')
async def login(req: Request, session_id: str = Cookie(None)):
    if session_id in sessions:
        return RedirectResponse('/client', 302)

    return templates.TemplateResponse('login.html', {'request': req})


@app.post('/login')
async def login(username: str = Form(), password: str = Form()):
    cur.execute('SELECT password, id FROM users WHERE name = ?', (username,))
    fetch = cur.fetchall()

    if len(fetch) < 1 or fetch[0][0] != crypt.crypt(password, fetch[0][0]):
        res = RedirectResponse('/login', 302)
        res.set_cookie('retry')
        return res

    session_id = str(uuid.uuid4())
    sessions[session_id] = {'username': username, 'id': fetch[0][1]}
    
    res = RedirectResponse('/client', 302)
    res.set_cookie('session_id', session_id)
    
    return res
 

@app.get('/client')
async def client(req: Request, session_id = Cookie(None)):
    if session_id in sessions:
        return templates.TemplateResponse('client.html', {'request': req})

    return RedirectResponse('/login', 302)
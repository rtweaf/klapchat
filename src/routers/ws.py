import sqlite3
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from sessions_manager import sessions
from .ws_utils import fmt, errfmt


router = APIRouter()


class WebSocket(WebSocket):
    session_id: int


class ConnectionManager:
    def __init__(self) -> None:
        self.conn: sqlite3.Connection = sqlite3.connect('db.sqlite')
        self.cur: sqlite3.Cursor = self.conn.cursor()
        self.conns: dict[str, list[WebSocket]] = {}

        self.cur.execute(
            'CREATE TABLE IF NOT EXISTS users '
            '(name TEXT, password TEXT, id TEXT)'
        )
        self.cur.execute(
            'CREATE TABLE IF NOT EXISTS rooms '
            '(name TEXT, id TEXT, owner_id TEXT)'
        )
        self.cur.execute(
            'CREATE TABLE IF NOT EXISTS relation '
            '(user_id TEXT, room_id TEXT)'
        )

        self.cur.execute('SELECT id FROM rooms')
        for id in self.cur.fetchall():
            self.conns[id[0]] = []

    async def is_room_exist(self, id: str) -> bool:
        return id in self.conns

    async def is_member(self, ws: WebSocket, room_id: str) -> bool:
        self.cur.execute(
            'SELECT room_id FROM relation WHERE user_id = ?',
            (sessions[ws.session_id]['id'],)
        )

        return (room_id,) in self.cur.fetchall()

    def is_connected(self, ws: WebSocket, id: str) -> bool:
        return id in self.conns and ws in self.conns[id]

    async def is_owner(self, ws: WebSocket, room_id: str) -> bool:
        self.cur.execute('SELECT id FROM rooms WHERE owner_id = ?',
                        (sessions[ws.session_id]['id'],))
        return (room_id,) in self.cur.fetchall()

    async def broadcast(self, authors_ws: WebSocket, ev: str, room_id: str,
                        **kwargs: dict) -> None:
        for ws in self.conns[room_id]:
            await ws.send_json(fmt(ev, **kwargs) | {'author':
                                sessions[authors_ws.session_id]['username']})

    async def connect_room(self, ws: WebSocket, id: str):
        for i in list(self.conns.values()):
            if ws in i:
                return errfmt('already_connected')

        if await self.is_member(ws, id):
            self.conns[id].append(ws)
            await self.broadcast(ws, 'connected', id, id=id)
            return

        return errfmt('not_member')

    async def disconnect_room(self, ws: WebSocket, id: str):
        if not self.is_connected(ws, id):
            return errfmt('not_connected')

        # first broadcast so that client can receive disconnected event
        await self.broadcast(ws, 'disconnected', id)
        self.conns[id].remove(ws)

    async def push_message(self, ws: WebSocket, room_id: str, content: str):
        if not self.is_connected(ws, room_id):
            return errfmt('not_connected')

        await self.broadcast(ws, 'message', room_id, content=content)

    async def create_room(self, ws: WebSocket, name: str):
        self.cur.execute('SELECT id FROM rooms WHERE name = ?', (name,))
        if self.cur.fetchall() != []:
            return errfmt('already_exists')

        if len(name) > 32:
            return errfmt('max_name_len')

        for c in name:
            if not 97 <= ord(c) <= 122:
                return errfmt('unallowed_chars')

        while True:
            id = str(uuid.uuid4())
            self.cur.execute('SELECT id FROM rooms WHERE id = ?', (id,))
            if self.cur.fetchall() == []:
                break
        
        self.conns[id] = []
        self.cur.execute('INSERT INTO rooms VALUES (?, ?, ?)', (
            name, id, sessions[ws.session_id]['id']
        ))
        self.conn.commit()
        await self.join_room(ws, id)

        return fmt('room_created', id=id)

    async def delete_room(self, ws: WebSocket, id: str):
        if not await self.is_owner(ws, id):
            return errfmt('not_owner')

        for ws in self.conns[id]:
            await self.leave_room(ws, id, True)

        del self.conns[id]
        self.cur.execute('DELETE FROM rooms WHERE id = ?', (id,))
        return fmt('room_deleted')

    async def join_room(self, ws: WebSocket, id: str):
        if not await self.is_room_exist(id):
            return errfmt('no_such')
        
        self.cur.execute(
            'INSERT INTO relation VALUES (?, ?)',
            (sessions[ws.session_id]['id'], id,)
        )

        # first connect so that client can receives joined event
        await self.connect_room(ws, id)
        self.cur.execute('SELECT name FROM rooms WHERE id = ?', (id,))
        await self.broadcast(ws, 'joined', id, name=self.cur.fetchall()[0][0],
                            id=id)

    async def leave_room(self, ws: WebSocket, id: str,
                        ignore_owner: bool = False):
        if not await self.is_member(ws, id):
            return errfmt('not_member')
        
        if await self.is_owner(ws, id) and not ignore_owner:
            return errfmt('owner_cant_leave')
            
        self.cur.execute(
            'DELETE FROM relation WHERE user_id = ? and room_id = ?',
            (sessions[ws.session_id]['id'], id)
        )
        
        self.cur.execute('SELECT name FROM rooms WHERE id = ?', (id,))
        await self.broadcast(ws, 'left', id, name=self.cur.fetchall()[0][0],
                            id=id)
        await self.disconnect_room(ws, id)

    async def get_rooms(self, ws: WebSocket):
        self.cur.execute(
            'SELECT room_id FROM relation WHERE user_id = ?',
            (sessions[ws.session_id]['id'],)
        )

        rooms = {}
        
        for i in self.cur.fetchall():
            self.cur.execute('SELECT name FROM rooms WHERE id = ?', (i[0],))
            rooms[i[0]] = self.cur.fetchall()[0][0]
        
        return fmt('rooms', rooms=rooms)

    async def get_members(self, ws: WebSocket, id: str):
        if not self.is_connected(ws, id):
            return errfmt('not_connected')
        
        fmt('members',
            members=[sessions[ws.session_id] for ws in self.conns[id]])

    async def whoami(self, ws: WebSocket):
        return fmt('youare', username=sessions[ws.session_id]['username'])

    async def change_username(self, ws: WebSocket, name: str):
        pass

    async def change_roomname(self, ws: WebSocket, id: str, name: str):
        pass


manager = ConnectionManager()


@router.websocket('/ws')
async def ws_endpoint(ws: WebSocket):
    try:
        await ws.accept()
        while True:
            recv = await ws.receive_json()
            try:
                if not recv['sessionId'] in sessions:
                    return ws.close(4404, 'Invalid session id')

                ws.session_id = recv['sessionId']
                match recv['event']:
                    case 'connectRoom':
                        d = await manager.connect_room(ws, recv['roomId'])
                    case 'disconnectRoom':
                        d = await manager.disconnect_room(ws, recv['roomId'])
                    case 'pushMessage':
                        d = await manager.push_message(ws, recv['roomId'],
                                                        recv['content'])
                    case 'createRoom':
                        d = await manager.create_room(ws, recv['roomName'])
                    case 'deleteRoom':
                        d = await manager.delete_room(ws, recv['roomId'])
                    case 'joinRoom':
                        d = await manager.join_room(ws, recv['roomId'])
                    case 'leaveRoom':
                        d = await manager.leave_room(ws, recv['roomId'])
                    case 'getRooms':
                        d = await manager.get_rooms(ws)
                    case 'getMembers':
                        d = await manager.get_members(ws)
                    case 'whoAmI':
                        #todo: whoIs
                        d = await manager.whoami(ws)
                    case 'changeUsername':
                        pass
                    case 'changeRoomname':
                        pass
                    case _:
                        return ws.close(4404, 'Unknow operation')

                if d is not None:
                    await ws.send_json(d)
            except ZeroDivisionError:
                pass
            #except KeyError as ex:
                #return await ws.close(4400, f'Missing argument {ex}')
            #except ValueError:
                #return await ws.close(4400, 'Invalid data type for the argument')
    except WebSocketDisconnect:
        return
    except RuntimeError:
        return
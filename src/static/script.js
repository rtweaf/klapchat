const ws = new WebSocket('ws://localhost:8000/ws');

const cached_data = {
    'currRoom': '',
    'myUsername': ''
};

getCookie = (name) => {
    return document.cookie
        .split('; ')
        .find((row) => row.startsWith(name))
        ?.split('=')[1];
};

getSesId = () => getCookie('session_id');

ws.onopen = (_ev) => {
    ws.send(JSON.stringify({
        'event': 'whoAmI',
        'sessionId': getSesId()
    }));

    ws.send(JSON.stringify({
        'event': 'getRooms',
        'sessionId': getSesId()
    }));
};

ws.onclose = (ev) => {
    alert(ev.reason);
};

ws.onmessage = (ev) => {
    console.log(JSON.parse(ev.data))
    const d = JSON.parse(ev.data);
    switch (d.event) {
        case 'error':
            document.getElementById('error').innerText = d.description;
            break;

        case 'youare':
            cached_data.myUsername = d.username;
            break;

        case 'rooms':
            const rooms = document.getElementById('rooms');
            for (const [key, value] of Object.entries(d.rooms)) {
                rooms.add(new Option(value, key));
            }
            break;

        case 'message':
            document.getElementById('messages').innerHTML += 
                `<p><p class="username">${d.author}</p> ${d.content}</p>`;
            break;

        case 'connected':
            if (d.author == cached_data.myUsername) {
                document.getElementById('message-content').disabled = false;
                document.getElementById('message-push').disabled = false;
                document.getElementById('rooms').disabled = true;
                cached_data.currRoom = d.id;
                document.getElementById('rooms').value = d.id;
            }
            document.getElementById('messages').innerHTML +=
                `<p class="status-g">${d.author} connected</p>`;
            break;
        
        case 'disconnected':
            if (d.author == cached_data.myUsername) {
                document.getElementById('message-content').disabled = true;
                document.getElementById('message-push').disabled = true;
                document.getElementById('rooms').disabled = false;
                cached_data.currRoom = '';
            }

            document.getElementById('messages').innerHTML +=
                `<p class="status-r">${d.author} disconnected</p>`;
            break;
        
        case 'joined':
            if (d.author = cached_data.myUsername) {
                document.getElementById('rooms').add(new Option(d.name, d.id));
            }

            document.getElementById('messages').innerHTML +=
                `<p class="status-g">${d.author} joined</p>`;
            break;

        case 'left':
            if (d.author = cached_data.myUsername) {
                const rooms = document.getElementById('rooms');
                for (let i = 0; i < rooms.length; ++i) {
                    if (rooms.options[i].value == d.id) {
                        rooms.remove(i);
                    }
                }
            }

            document.getElementById('messages').innerHTML +=
                `<p class="status-r">${d.author} left</p>`;
            break;
    }
};

joinRoom = () => {
    ws.send(JSON.stringify({
        'event': 'joinRoom',
        'roomId': prompt('room id'),
        'sessionId': getSesId()
    }));
};

createRoom = () => {
    ws.send(JSON.stringify({
        'event': 'createRoom',
        'roomName': prompt('room name'),
        'sessionId': getSesId(),
    }));
};

connectRoom = () => {
    ws.send(JSON.stringify({
        'event': 'connectRoom',
        'roomId': document.getElementById('rooms').value,
        'sessionId': getSesId()
    }));
};

disconnectRoom = () => {
    ws.send(JSON.stringify({
        'event': 'disconnectRoom',
        'roomId': cached_data.currRoom,
        'sessionId': getSesId()
    }));
};

deleteRoom = () => {
    ws.send(JSON.stringify({
        'event': 'deleteRoom',
        'roomId': document.getElementById('rooms').value,
        'sessionId': getSesId()
    }));
};

leaveRoom = () => {
    ws.send(JSON.stringify({
        'event': 'leaveRoom',
        'roomId': document.getElementById('rooms').value,
        'sessionId': getSesId()
    }));
};

copyId = () => {
    navigator.clipboard.writeText(document.getElementById('rooms').value).then(
        () => {},
        () => {
            document.getElementById('error').innerText = 'plz allow clipboard perms';
        }
    );
};

pushMessage = () => {
    ws.send(JSON.stringify({
        'event': 'pushMessage',
        'roomId': cached_data.currRoom,
        'content': document.getElementById('message-content').value,
        'sessionId': getSesId()
    }));
};
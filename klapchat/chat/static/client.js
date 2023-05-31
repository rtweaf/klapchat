let socket = new WebSocket(`ws://${window.location.host}/ws/`);

//document.getElementById('send').onclick = (event) => {
//    socket.send(JSON.stringify({ 'type': 'message', 'message': document.getElementById('message').value }));
//};


socket.onopen = (event) => {
    socket.send(JSON.stringify({'type': 'joined_channels'}));
};

socket.onclose = (event) => {
    try {
        socket = new WebSocket(`ws://${window.location.host}/ws/`);
    } catch (err) {
        alert(err);
    }
}

socket.onmessage = (event) => {
    switch (event.data['type']) {
        case 'joined_channels':
            event.data['type'].channels_id.forEach(channel => {
                console.log(channel);
            });
            break;
    }
};

document.getElementById('channels').onchange = (event) => {

};
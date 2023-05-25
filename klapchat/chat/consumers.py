import json

from channels.generic.websocket import WebsocketConsumer


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, _):
        pass

    def receive(self, text_data=None, bytes_data=None):
        pass

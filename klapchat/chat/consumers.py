import json

from django.core import exceptions
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Channel


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def connect_channel(self, channel_id):
        try:
            if Channel.objects.filter(id=channel_id,
                                      members__in=[self.scope['user']]):
                await self.channel_layer.group_add(channel_id, channel_id)
                await self.close()
            else:
                await self.send(json.dumps({
                    'type': 'error.not_member',
                    'description': 'You are not a member of this channel.'}))
        except exceptions.ValidationError as ex:
            await self.send(json.dumps({'type': 'error.validation',
                                        'description': ex}))

    async def join_channel(self, channel_id):
        try:
            if channel := Channel.objects.filter(id=channel_id):
                channel.member.add(self.scope['user'])
        except exceptions.ValidationError as ex:
            await self.send(json.dumps({'type': 'error.validation',
                                        'description': ex}))
    
    async def joined_channels(self):
        return self.send(
            json.dumps({'type': 'joined_channels',
                        'channels_id': Channel.objects.filter(
                            members__in=[self.scope['user']])})
        )

    async def receive(self, text_data=None):
        if text_data:
            await self.send(json.dumps(text_data))
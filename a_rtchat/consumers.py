from channels.generic.websocket import WebsocketConsumer
from django.shortcuts import get_object_or_404
from .models import *
import json
from asgiref.sync import async_to_sync
from django.template.loader import render_to_string
from django.db.models import Max
from datetime import timedelta
from django.utils import timezone

class ChatroomConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.chatroom_name = self.scope['url_route']['kwargs']['chatroom_name'] 
        self.chatroom = get_object_or_404(ChatGroup, group_name=self.chatroom_name)
        
        async_to_sync(self.channel_layer.group_add)(
            self.chatroom_name, self.channel_name
        )
        self.accept()
        
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.chatroom_name, self.channel_name
        )
        
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        body = text_data_json['body']
        
        message = GroupMessage.objects.create(
            body = body,
            author = self.user, 
            group = self.chatroom 
        )
        event = {
            'type': 'message_handler',
            'message_id': message.id,
        }
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )
        chat_groups = self.user.chat_groups.annotate(
            latest_message_time=Max('chat_messages__created')
        ).order_by('-latest_message_time')
        event1 = {
            'type': 'contact_update',
        }
        # Broadcast contact update to all users in group
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event1
        )
        
    def message_handler(self, event):
        message_id = event['message_id']
        message = GroupMessage.objects.get(id=message_id)
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        context = {
            'message': message,
            'user': self.user,
            'chat_group': self.chatroom,
            'now': now,
            'yesterday': yesterday
        }
        chat_groups = self.user.chat_groups.annotate(
            latest_message_time=Max('chat_messages__created')
        ).order_by('-latest_message_time')
        
        # Render chat message
        html = render_to_string("a_rtchat/partials/chat_message_p.html", context=context)
        self.send(text_data=html)
        

    def contact_update(self, event):
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        chat_groups = self.user.chat_groups.annotate(
            latest_message_time=Max('chat_messages__created')
        ).order_by('-latest_message_time')
        context = {
            'chat_groups': chat_groups,
            'user': self.user,
            'now': now,
            'yesterday': yesterday
        }
        html_contact = render_to_string("a_rtchat/partials/contact_p.html", context=context)
        self.send(text_data=html_contact)

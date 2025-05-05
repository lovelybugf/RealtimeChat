from django.urls import path
from a_rtchat.views import *

urlpatterns = [
    path('',chat_view, name= "home"),
    path('chat/<username>', get_or_create_chatroom, name="send-message"),
    path('chat/room/<chatroom_name>', chat_view, name="chatroom"),
    path('chat/new_groupchat/', new_chat_group, name="new-chatgroup"),
    path('chat/manage_group/<chatroom_name>', manage_group, name="manage-group"),
    path('chat/file-upload/<chatroom_name>', chat_file_upload, name="chat-file-upload"),
    path('start-game/', start_Ransanmoi, name="start_game"),
    path('start-xo/', start_XO, name="start_xo"),  
]
from django.urls import path
from a_rtchat.views import *

urlpatterns = [
    path('',chat_view, name= "home"),
]
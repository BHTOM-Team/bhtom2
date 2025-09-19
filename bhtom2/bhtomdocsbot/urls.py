from django.urls import path
from .views import chat_start, chat_message

urlpatterns = [
    path("chat/start",  chat_start),
    path("chat/start/", chat_start),
    path("chat/message",  chat_message),
    path("chat/message/", chat_message),
]
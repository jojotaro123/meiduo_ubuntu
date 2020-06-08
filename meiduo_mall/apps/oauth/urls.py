from django.urls import re_path,path
from . import views

urlpatterns = [
    path('qq/authorization/',views.QQURLView.as_view()),
    path('oauth_callback/',views.QQUserView.as_view()),



]
from django.urls import re_path,path
from . import views

urlpatterns = [
    # 判断用户名是否重复
    re_path('^usernames/(?P<username>\w{5,20})/count/$',views.UsernameCountView.as_view()),
    re_path(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
    # path('register/',views.RegisterView.as_view()),
    re_path(r'^register/$', views.RegisterView.as_view()),
    path('login/',views.LoginView.as_view()),
    path('logout/',views.LogoutView.as_view()),
    path('info/',views.UserInfoView.as_view()),
    path('emails/', views.EmailView.as_view()),
    re_path(r'^addresses/create/$',views.CreateAddressView.as_view()),
    path('addresses/', views.AddressView.as_view()),
    re_path(r'addresses/(?P<address_id>\d+)/',views.UpdateDestroyAddressView.as_view()),

    re_path(r'^addresses/(?P<address_id>\d+)/default/$', views.DefaultAddressView.as_view()),

]


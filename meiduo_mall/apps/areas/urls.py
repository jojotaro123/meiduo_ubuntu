from django.urls import re_path,path
# from apps.areas import views
from . import views

urlpatterns = [
    path('areas/',views.ProvinceAreasView.as_view()),
    re_path('^areas/(?P<pk>[1-9]\d+)/$',views.SubAreasView.as_view()),


]
from django.shortcuts import render

# Create your views here.
from django import http
from django.views import View
from apps.users.models import User

class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        '''判断用户名是否重复'''
        # 1.查询username在数据库中的个数
        print('进去用户名是否重复方法')
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return http.JsonResponse({'code':400,
                                 'errmsg':'访问数据库失败'})

        # 2.返回结果(json) ---> code & errmsg & count

        print('访问用户名重复方法数据库检查成功')
        return http.JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'count':count})



class MobileCountView(View):

    def get(self, request, mobile):
        '''判断手机号是否重复注册'''
        # 1.查询mobile在mysql中的个数
        print('1')
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return http.JsonResponse({'code':400,
                                 'errmsg':'查询数据库出错'})

        # 2.返回结果(json)
        return http.JsonResponse({'code':0,
                             'errmsg':'ok',
                             'count':count})



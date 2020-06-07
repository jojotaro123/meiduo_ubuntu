from django.shortcuts import render

# Create your views here.
from django import http
from django.views import View
from apps.users.models import User
import json
from django.http import JsonResponse
import re
from django_redis import get_redis_connection
from django.contrib.auth import login,logout,authenticate


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

        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return http.JsonResponse({'code':400,
                                 'errmsg':'查询数据库出错'})

        # 2.返回结果(json)
        return http.JsonResponse({'code':0,
                             'errmsg':'ok',
                             'count':count})


class RegisterView(View):
    def post(self, request):
        print('进来了')
        # 将拿到的json表单数据变为字典
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        password2 = dict.get('password2')
        mobile = dict.get('mobile')
        allow = dict.get('allow')
        sms_code_client = dict.get('sms_code')

        if not all([username,password,password2,mobile,allow,sms_code_client]):
            return http.JsonResponse({'code':400,
                                      'errmsg':'缺少必传参数'})

        # 3.单个检验: username
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return JsonResponse({'code': 400,
                                 'errmsg': 'username格式不正确'})

        # 4.password
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return JsonResponse({'code': 400,
                                 'errmsg': 'password格式不正确'})

        # 5.password 和 password2
        if password != password2:
            return JsonResponse({'code': 400,
                                 'errmsg': '两次输入密码不一致'})

        # 6.mobile
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': 'mobile格式不正确'})

        # 7.allow
        if allow != True:
            return JsonResponse({'code': 400,
                                 'errmsg': '请勾选协议'})


        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        if not sms_code_server:
            return JsonResponse({'code': 400,
                                 'errmsg': '验证码过期'})

        if sms_code_server.decode() != sms_code_client:
            return JsonResponse({'code': 400,
                                 'errmsg': '验证码不一样'})

        try:
            user = User.objects.create_user(username,password,mobile)

        except Exception as e:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '保存到数据库出错'})

        login(request, user)

        return http.JsonResponse({'code': 0,
                                  'errmsg': 'ok'})

class LoginView(View):

    def post(self,request):
        request_data = request.body.decode()
        request_dict = json.loads(request_data)

        account = request_dict['username']
        password = request_dict['password']
        remembered = request_dict['remembered']

        if not all([account,password]):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '缺少用户名或密码'})

        if re.match(r'^1[3-9]\d{9}$', account):
            User.USERNAME_FIELD = 'mobile'


        user = authenticate(request=request,username=account,password=password)

        if user is None:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '用户名或密码错误'})

        login(request,user)

        if remembered != True:
            request.session.set_expiry(0)


        else:
            request.session.set_expiry(None)

        response = http.JsonResponse({'code': 0,
                                  'errmsg': 'ok'})

        response.set_cookie('username',account)

        return response

class LogoutView(View):

    def delete(self,request):
        logout(request)

        response = http.JsonResponse({'code': 0,
                                  'errmsg': 'ok'})
        response.delete_cookie('username')

        return response
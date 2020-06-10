from django.shortcuts import render
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django import http
from django.views import View
from apps.oauth.models import OAuthQQUser
from apps.oauth.utils import generate_access_token,check_access_token_openid
from django.contrib.auth import login
import json,re
from django_redis import get_redis_connection
from apps.users.models import User

# Create your views here.

class QQURLView(View):
    def get(self,request):
        next = request.GET.get('next')

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        # 调用提供QQ登录扫码链接的接口函数
        login_url = oauth.get_qq_url()

        # 响应结果
        return http.JsonResponse({'code': 0, 'errmsg': 'OK', 'login_url': login_url})


class QQUserView(View):
    def get(self,requset):
        code = requset.GET.get('code')
        if not code:
            return http.JsonResponse({'code': 400, 'errmsg': '缺少code'})

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        try:
            # 用code 获得 access_token
            access_token = oauth.get_access_token(code)

            # 用 access_token 获得 openid
            openid = oauth.get_open_id(access_token)

        except Exception as e:
            return http.JsonResponse({'code': 400, 'errmsg': 'OAuth2.0认证失败'})


        # 用openid判断是否已经登录
        try:
            oauth_model = OAuthQQUser.objects.get(openid=openid)

        except OAuthQQUser.DoesNotExist as e:
            access_token = generate_access_token(openid)
            return http.JsonResponse({'code': 300, 'errmsg': '用户未绑定的', 'access_token': access_token})

        else:
            login(requset=requset,user=oauth_model.user)
            response = http.JsonResponse({'code': 0, 'errmsg': 'OK'})
            response.set_cookie('username',oauth_model.user.username)

            return response

    def post(self,request):
       # 绑定qq用户

        request_body = request.body.decode()
        dict = json.loads(request_body)

        mobile = dict['mobile']

        password = dict['password']

        sms_code = dict['sms_code']

        access_token = dict['access_token']



       # 校验参数

        if not all([mobile,password,sms_code]):
            return {'code': 400, 'errmsg': '缺少必传参数'}

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400, 'errmsg': '参数mobile有误'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.JsonResponse({'code': 400, 'errmsg': '参数password有误'})

        redis_conn = get_redis_connection('verify_code')

        sms_code_server = redis_conn.get('sms_%s' % mobile)

        if not sms_code_server:
            return http.JsonResponse({'code': 400, 'errmsg': '短信验证码失效'})

        sms_code_str = sms_code_server.decode()

        if sms_code.lower() != sms_code_str.lower():
            return http.JsonResponse({'code': 400, 'errmsg': '短信验证码错误'})

        # 校验openid

        openid = check_access_token_openid(access_token)

        if not openid:
            return http.JsonResponse({'code': 400, 'errmsg': '参数openid有误'})

        # 判断手机号对应的用户是否存在
        try:
            user = User.objects.get(mobile=mobile)

        except User.DoesNotExist:

            user = User.objects.create_user(username=mobile,password=password,mobile=mobile)

        else:
            if not user.check_password(password):
                return http.JsonResponse({'code': 400, 'errmsg': '密码错误'})

        try:
            OAuthQQUser.objects.create(user=user, openid=openid)

        except Exception as e:
            return http.JsonResponse({'code': 400, 'errmsg': 'QQ登录失败'})


        # 状态保持

        login(request=request,user=user)

        response = http.JsonResponse({'code': 0, 'errmsg': 'OK'})
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)

         # 响应结果
        return response


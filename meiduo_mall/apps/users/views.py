from django.shortcuts import render

# Create your views here.
from django import http
from django.views import View
from apps.users.models import User,Address
import json
from django.http import JsonResponse
import re,logging
from django_redis import get_redis_connection
from django.contrib.auth import login,logout,authenticate
from meiduo_mall.utils.views import LoginRequiredJSONMixin
from apps.users.utils import generate_email_verify_url, check_email_verify_url
from django.core.mail import send_mail
from celery_tasks.email.tasks import send_email_verify_url

logger = logging.getLogger('django')

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
            user = User.objects.create_user(username,password=password,mobile=mobile)

        except Exception as e:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '保存到数据库出错'})

        login(request, user)
        response = http.JsonResponse({'code': 0,
                                  'errmsg': 'ok'})
        response.set_cookie('username',username)

        return response

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


class UserInfoView(LoginRequiredJSONMixin, View):

    def get(self,request):
        print('userinfo')
        data_dict = {
            'code': 0,
            'errmsg': 'OK',
            'info_data': {
                'username': request.user.username,
                'mobile': request.user.mobile,
                'email': request.user.email,
                'email_active': request.user.email_active
            }
        }

        return http.JsonResponse(data_dict)



class EmailView(LoginRequiredJSONMixin, View):
    def put(self,request):

        request_str = request.body.decode()
        request_dict = json.loads(request_str)

        email = request_dict.get('email')

        # 校验参数
        if not email:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '缺少email参数'})

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '参数email有误'})

        try:
            request.user.email = email
            request.user.save()

        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': '400', 'errmsg': '数据错误'})

        # 验证激活邮箱
        verify_url = generate_email_verify_url(user=request.user)
        send_email_verify_url.delay(email, verify_url)

        return http.JsonResponse({'code': '0', 'errmsg': 'ok'})


class EmailActiveView(View):
    """验证激活邮箱
    PUT /emails/verification/
    """

    def put(self, request):
        """实现验证激活邮箱的逻辑"""
        # 接收参数
        token = request.GET.get('token')

        # 校验参数
        if not token:
            return http.JsonResponse({'code': 400, 'errmsg': '缺少token'})

        # 实现核心逻辑
        # 通过token提取要验证邮箱的用户
        user = check_email_verify_url(token=token)

        # 将要验证邮箱的用户的email_active字段设置True
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': '邮箱验证失败'})

        # 响应结果
        return http.JsonResponse({'code': 0, 'errmsg': '邮箱验证成功'})





class CreateAddressView(View):
    def post(self,request):
        request_json = request.body.decode()
        json_dict = json.loads(request_json)

        # 用已登录用户, 一查多,因为设置了related_name='addresses',所以直接 一方对象.addresses获取多方对象
        try:
            count = request.user.addresses.filter(is_deleted=False).count()

        except Exception as e:
            return http.JsonResponse({'code': 400, 'errmsg': '获取地址失败'})


        # 判断地址个数是否超过20
        if count > 300:
            return http.JsonResponse({'code': 400, 'errmsg': '超过设置收货地址上限20个'})

        # 接收参数
        request_json = request.body.decode()
        request_dict = json.loads(request_json)


        receiver = request_dict.get('receiver')
        province_id = request_dict.get('province_id')
        city_id = request_dict.get('city_id')
        district_id = request_dict.get('district_id')
        place =request_dict.get('place')
        mobile = request_dict.get('mobile')
        tel = request_dict.get('tel')
        email = request_dict.get('email')
        title = request_dict.get('title')



        # 校验参数
        if not all([receiver,province_id, city_id, district_id, place, mobile]):
            return http.JsonResponse({'code': 400, 'errmsg': '信息不完整'})

        # if not re.match(r'^1[3-9]\d{9}$', mobile):
        #     return http.JsonResponse({'code': 400, 'errmsg': '手机格式不对'})

        # if tel:
        #     if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
        #         return http.JsonResponse({'code': 400, 'errmsg': '参数tel有误'})
        # if email:
        #     if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        #         return http.JsonResponse({'code': 400, 'errmsg': '参数email有误'})

        # 添加数据到数据库 tb_address表
        try:
            address = Address.objects.create(
                user=request.user,
                province_id = province_id,
                city_id = city_id,
                district_id = district_id,
                title = receiver,
                receiver = receiver,
                place = place,
                mobile=mobile,
                tel = tel,
                email = email,

                 )

            # 补充逻辑,给用户添加默认地址
            # 这里 user表的default_address属性外键是Address,所以可以用 属性=外键对象 这种方式赋值.
            if not request.user.default_address:
                # 如果没有默认地址，就把当前的地址作为该用户的默认地址
                request.user.default_address = address
                # request.user.default_address_id = address.id
                request.user.save()


        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': '新增地址出错,请重试'})


        # 响应数据给前端
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应保存结果
        return http.JsonResponse({'code': 0,
                                  'errmsg': '新增地址成功',
                                  'address': address_dict})



class AddressView(LoginRequiredJSONMixin, View):

    def get(self,request):
        # 核心逻辑：查询当前登录用户未被逻辑删除的地址
        address_list = request.user.addresses.filter(is_deleted=False)
        address_dict_list = []
        for address in address_list:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }
            address_dict_list.append(address_dict)

            # 查询当前登录用户默认地址的ID
        default_address_id = request.user.default_address_id

        return http.JsonResponse({
            "code": 0,
            "errmsg": "ok",
            "default_address_id": default_address_id,
            "addresses": address_dict_list
        })



class UpdateDestroyAddressView(View):

    def delete(self,request,address_id):

        try:
            address = Address.objects.get(id=address_id)
            address.is_deleted = True
            address.save()

        except Exception as e:
            return http.JsonResponse({'code': 400, 'errmsg': '删除地址出错'})

        return http.JsonResponse({'code': 0,
                                  'errmsg': '删除地址成功'})






class DefaultAddressView(View):
    """设置默认地址"""

    def put(self, request, address_id):
        """设置默认地址"""
        try:
            # 接收参数,查询地址
            address = Address.objects.get(id=address_id)

            # 设置地址为默认地址
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400,
                                      'errmsg': '设置默认地址失败'})

        # 响应设置默认地址结果
        return http.JsonResponse({'code': 0,
                                  'errmsg': '设置默认地址成功'})


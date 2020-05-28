from django.views import View
from django import http
from django.http import HttpResponse
from django_redis import get_redis_connection
import logging
from libs.captcha.captcha import captcha
from libs.yuntongxun.ccp_sms import CCP
from celery_tasks.sms.tasks import ccp_send_sms_code


logger = logging.getLogger('django')

class ImageCodeView(View):
    '''返回图形验证码的类视图'''

    def get(self, request, uuid):
        '''
        生成图形验证码, 保存到redis中, 另外返回图片
        :param request:请求对象
        :param uuid:浏览器端生成的唯一id
        :return:一个图片
        '''
        # 1.调用工具类 captcha 生成图形验证码
        text, image = captcha.generate_captcha()

        # 2.链接 redis, 获取链接对象
        redis_conn = get_redis_connection('verify_code')

        # 3.利用链接对象, 保存数据到 redis, 使用 setex 函数
        # redis_conn.setex('<key>', '<expire>', '<value>')
        redis_conn.setex('img_%s' % uuid, 300, text)

        # 4.返回(图片)
        return HttpResponse(image,
                            content_type='image/jpg')


class SMSCodeView(View):

    def get(self,request,mobile):

        # 连接redis数据库
        redis_conn = get_redis_connection('verify_code')
        # 检查是否存在防止频繁发送短信验证码的checkpoint
        redis_checkpoint = redis_conn.get('check_point_%s'%mobile)

        if redis_checkpoint:

            return http.JsonResponse({'code': 400,
                                      'errmsg': '发送短信过于频繁'})

        # 以下代码检查图片验证码是否输对

        # 提取路径参数里的用户输入验证码和浏览器生产的uuid
        user_text = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        if not all([user_text,uuid]):
            response = http.JsonResponse({'code': 400,
                                      'errmsg': '缺少必传参数'})

            return response


        # 取出redis数据库中的key(uuid)和value(text)  25行里设置的东西
        redis_text = redis_conn.get('img_%s' % uuid)
        if not redis_text:
            response=http.JsonResponse({'code': 400,
                                      'errmsg': '验证码过期或失效'})
            return response

        try:
            # 删除数据库验证码数据,因为已经取到了,所以没必要保留,防止用户恶意注册

            redis_conn.delete('img_%s' % uuid)

        except Exception as e:
            logger.error(e)


        # 数据库取得的验证码为byte类型,需要解码
        redis_text_str = redis_text.decode()


        if user_text.lower() != redis_text_str.lower():
            print('验证码输错了')
            response = http.JsonResponse({'code': 400,
                                      'errmsg': '验证码输错了'})

            return response


        sms_code = 'konodioda'
        logger.info(sms_code)

        pl = redis_conn.pipeline()

        # redis_conn.setex('sms_%s' % mobile, 300, sms_code)
        pl.setex('sms_%s' % mobile, 300, sms_code)

        # redis_conn.setex('send_flag_%s' % mobile, 60, 1)
        pl.setex('send_flag_%s' % mobile, 60, 1)

        # 执行管道:
        pl.execute()

        # CCP().send_template_sms(mobile, [sms_code, 5], 1)
        # print('发送验证码成功')

        ccp_send_sms_code.delay(mobile, sms_code)

        return http.JsonResponse({'code': 0,
                                  'errmsg': '发送短信成功'})



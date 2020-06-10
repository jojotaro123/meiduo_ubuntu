from django.core.mail import send_mail
from django.conf import settings
from celery_tasks.main import celery_app

@celery_app.task(name='send_email_verify_url')
def send_email_verify_url(to_email, verify_url):
    """发送验证激活邮件的异步任务
    普通字符串: wadhaslbeouqysdakjl248723y时间内弗兰克几十年
    html超文本字符串: <p><a></a></p>
    """
    # send_mail(
    #     subject='标题',
    #     message='邮件正文：普通字符串',
    #     from_email='发件人',
    #     recipient_list='[收件人列表]',
    #     html_message='邮件正文：html超文本字符串'
    # )

    # 标题
    subject = "KonoDioda"
    # 发送内容:
    html_message = '<p>我不做人拉！JOJO</p>' \
                   '<p>WRYYYYYYYYYY。</p>' \
                    '<img src="https://imgsa.baidu.com/forum/w%3D580/sign=c2f1167442086e066aa83f4332097b5a/ee15212ac65c1038292b4487bc119313b17e89e7.jpg" alt="dio">'\
                   '<p>您的邮箱为：%s 。请点击此链接成为吸血鬼：</p>' \
                   '<p><a href="%s">%s<a></p>' % (to_email, verify_url, verify_url)

    send_mail(
        subject=subject,
        message='',
        from_email=settings.EMAIL_FROM,
        recipient_list=[to_email],
        html_message=html_message
    )
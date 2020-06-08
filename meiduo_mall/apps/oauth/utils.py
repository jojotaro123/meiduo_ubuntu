from itsdangerous import TimedJSONWebSignatureSerializer as Serializer,BadData
from django.conf import settings

def generate_access_token(openid):

    # 创建序列化器对象
    s = Serializer(settings.SECRET_KEY,600)

    data = {'openid':openid}

    token = s.dumps(data)

    return token.decode()


def check_access_token_openid(access_token):

    s = Serializer(settings.SECRET_KEY,600)

    try:
        data = s.loads(access_token)

    except BadData:
        return None

    openid = data.get('openid')
    # 返回openid明文
    return openid
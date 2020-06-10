from django.contrib.auth.mixins import LoginRequiredMixin
from django import http


class LoginRequiredJSONMixin(LoginRequiredMixin):
    """自定义LoginRequiredMixin
    如果用户未登录，响应JSON，且状态码为400
    """

    def handle_no_permission(self):
        return http.JsonResponse({'code': 400, 'errmsg': '用户未登录'})


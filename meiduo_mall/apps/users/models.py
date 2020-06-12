from django.db import models
from django.contrib.auth.models import AbstractUser
# from meiduo_mall.utils import BaseModel
from meiduo_mall.utils.BaseModel import BaseModel

# Create your models here.

class User(AbstractUser):
    """自定义用户模型类"""

    # 额外增加 mobile 字段
    mobile = models.CharField(max_length=11,
                              unique=True,
                              verbose_name='手机号')

    email_active = models.BooleanField(default=False, verbose_name='邮箱状态')

    default_address = models.ForeignKey('Address',
                                        related_name='users',
                                        null=True,
                                        blank=True,
                                        on_delete=models.SET_NULL,
                                        verbose_name='默认地址')



    # 对当前表进行相关设置:
    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    # 在 str 魔法方法中, 返回用户名称
    def __str__(self):
        return self.username

class Address(BaseModel):
    """用户地址: 多方
    用户和地址是一对多的关联关系
    自定义了一查多的关联字段：
        related_name='addresses'
        查询用户关联的地址(一查多)：用户模型对象.addresses
        查询地址属于的用户(多查一)：地址模型对象.user
    """
    user = models.ForeignKey(User, related_name='addresses', on_delete=models.CASCADE, verbose_name='用户')
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province', verbose_name='省')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city', verbose_name='市')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district', verbose_name='区')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        # ordering：指定默认的排序规则，如果指定了默认的排序规则，那么凡是得到的查询集默认都是按照该规则拍好顺序的
        # '-update_time'：表示默认的排序规则为按照修改时间倒序。最近一次新建或者修改的地址排列在最前面
        ordering = ['-update_time']



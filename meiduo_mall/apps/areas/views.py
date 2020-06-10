from django.shortcuts import render
from apps.areas.models import Area
from django import http
from django.views import View
from django.core.cache import cache
# Create your views here.

class ProvinceAreasView(View):

    """查询省份数据
      GET /areas/
      """

    def get(self,request):

        list = cache.get('list')
        if not list:
            try:
                province_query = Area.objects.filter(parent=None)

                list = [{'id':area.id,'name':area.name} for area in province_query]

            except Exception as e:
                return http.JsonResponse({"code": "400", "errmsg": "省份数据出错"})

            cache.set('list',list,3600)

        return http.JsonResponse({"code": "0", "errmsg": "OK", "province_list": list})



class SubAreasView(View):
    def get(self,request,pk):
        """提供市或区地区数据
              1.查询市或区数据
              2.序列化市或区数据
              3.响应市或区数据
              4.补充缓存数据
              """
        sub_data = cache.get('sub_area_%s' % pk)
        if sub_data:
            return http.JsonResponse({"code":"0",
  "errmsg":"OK",'sub_data':sub_data})

        child_set = Area.objects.filter(parent=pk)
        parent_area = Area.objects.get(id=pk)

        child_list = [{'id': area.id, 'name': area.name} for area in child_set]



        # subs = [{'id':area.id,'name':area.name} for　area in child_set]　　
        try:
            sub_data = {"id":parent_area.id,
          "name":parent_area.name,
          "subs":child_list}

        except Exception as e:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '城市或区县数据错误'})
        cache.set('sub_area_%s' % pk,sub_data,3600)

        return http.JsonResponse({"code":"0",
  "errmsg":"OK",'sub_data':sub_data})


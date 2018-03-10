from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('questions.views',
    url(r'^getqtioninfo/','getqtioninfo'),

    url(r'^choose/','mgrchoose'),

    url(r'^ask/','mgrask'),
    url(r'^skill/','mgrskill'),
    url(r'^infiltration/','mgrinfiltration'),
    url(r'^skilladd/','addskill'),
    url(r'^checkquedel/(\d+)/$','checkquedel'),
    url(r'^skilldel/(\d+)/$','delskill'),
    url(r'^qidcheck/','qidcheck'),
    url(r'^skilllinkcheck/','skilllinkcheck'),
    url(r'^skillinfo/','skillinfo'),
    url(r'^skilledit/(\d+)/$','editskill'),
    url(r'^infiltrationadd/','addinfiltration'),
    url(r'^infiltrationdel/(\d+)/$','delinfiltration'),
    url(r'^infiltrationlinkcheck/','infiltrationlinkcheck'),
    url(r'^infiltrationinfo/','infiltrationinfo'),
    url(r'^infiltrationedit/(\d+)/$','editinfiltration'),
    url(r'^chooseadd/','addchoose'),
    url(r'^choosedel/(\d+)/$','delchoose'),
    url(r'^chooseinfo/','chooseinfo'),
    url(r'^instartexam/','instartexam'),
    url(r'^chooseedit/(\d+)/$','editchoose'),


    url(r'^askadd/$','askadd'),
    url(r'^askdel/(\d+)/$','askdel'),
    url(r'^askinfo/$','askinfo'),

    url(r'^askedit/(\d+)/$','askedit'),

    



    

)

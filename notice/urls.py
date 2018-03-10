from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('notice.views',
	url(r'^$', 'noticeManage'),

	

	# url(r'^getAnsInfo/(\d+)/$', 'getAnsInfo'),
	url(r'^add/$', 'add'),
	url(r'^del/(\d+)/$', 'deltinoce'),

	url(r'^editGetInfo/(\d+)/$', 'editGetInfo'),
	url(r'^editSubmit/$', 'editSubmit'),


	url(r'^readnotice/$', 'readnotice'),

	


	



	)
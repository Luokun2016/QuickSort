from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('examinations.views',
	url(r'^$', 'examManage'),
	url(r'^display/$', 'examDisplay'),
	url(r'^add/$', 'examAddGetInfo'),
	url(r'^checkexamno/$','examCheckexamno'),
	url(r'^save/$', 'examSave'),
	url(r'^delete/$', 'examDelete'),
	url(r'^edit/$', 'examEdit'),
	url(r'^update/$', 'examUpdate'),
	url(r'^control/$', 'examControl'),
	url(r'^controlRes/$', 'controlRes'),
	url(r'^controlVm/$', 'controlVm'),

	url(r'^cur/$', 'examCur'),
	url(r'^total/$', 'examTotal'),
	url(r'^historycur/$', 'examHistoryCur'),
	url(r'^delfiles/$', 'delHistoryCur'),
	url(r'^controlChecklab/$', 'controlChecklab'),

	url(r'^getAnsInfo/(\d+)/$', 'getAnsInfo'),
	url(r'^givemark/(\d+)/$', 'givemark'),
	url(r'^timegrade/$', 'timegrade'),

	



	)
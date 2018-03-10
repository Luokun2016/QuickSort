from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('atkdfs.views',
	url(r'^$', 'atkdfsManage'),
	url(r'^add/$', 'atkdfsAddGetInfo'),
	url(r'^getQuestionNum/$', 'getQuestionNum'),
	url(r'^save/$', 'atkdfsSave'),
	url(r'^checkexamno/$','atkdfsCheckexamno'),
	url(r'^edit/$', 'atkdfsEdit'),
	url(r'^update/$', 'atkdfsUpdate'),
	url(r'^delete/$', 'atkdfsDelete'),
	url(r'^display/$', 'atkdfsDisplay'),
	url(r'^control/$', 'atkdfsControl'),
	url(r'^controlRes/$', 'controlRes'),
	url(r'^controlVm/$', 'controlVm'),
	url(r'^cur/$', 'atkdfsCur'),
	# url(r'^total/$', 'examTotal'),
	url(r'^historycur/$', 'atkdfsHistoryCur'),
	url(r'^delfiles/$', 'delHistoryCur'),
	url(r'^controlChecklab/$', 'controlChecklab'),



	)
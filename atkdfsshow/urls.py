from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('atkdfsshow.views',
	url(r'^$', 'showstate'),
	url(r'^warnMsg/$', 'warnMsg'),
	url(r'^getitem/$', 'getSelectItem'),
	url(r'^teamrank/$', 'teamrank'),
	url(r'^getgroups/$', 'getgroups'),
	url(r'^getAllgroup/$', 'getAllgroup'),
	)
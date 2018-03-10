from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('sysmgr.views',
	url(r'^configip/$', 'getip'),
	url(r'^changeip/$', 'changeip'),
	url(r'^upsystem/$', 'updata'),
	url(r'^uploadtool/$', 'uploadtool'),
	url(r'^unzipfile/$', 'unzip_file'),
	url(r'^syslog/$', 'syslog'),
	url(r'^outputlog/$', 'outputlog'),
	)
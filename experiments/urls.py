from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('experiments.views',
    url(r'^elesdel/(\d+)/$','elesdel'),
    url(r'^stepsdel/(\d+)/$','stepsdel'),
    url(r'^toolsdel/(\d+)/$','toolsdel'),
    url(r'^videosdel/(\d+)/$','videosdel'),
	)
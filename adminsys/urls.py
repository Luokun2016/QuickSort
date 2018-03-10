from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic import TemplateView
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^mysite/', include('mysite.foo.urls')),
    #url(r'^$','adminsys.views.sysadmin'),
    url(r'^main/$', TemplateView.as_view(template_name="templates/main.html")),
    (r'^statics/(?P<path>.*)$','django.views.static.serve',{'document_root': settings.STATIC_ROOT}),
)

from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.defaults import *

urlpatterns = patterns('Tools.views',
    url(r'^$', 'showtool'),
    url(r'^tooledit/$', 'edittool'),
    url(r'^tooladd/$', 'addtool'),
    url(r'^toolupload/$', 'uploadtool'),
    url(r'^tools/$', 'showtool'),
    url(r'^tooldel/(\d+)/$','deltool'),
    url(r'^toolinfo/$','toolinfo'),
    url(r'^toolnamecheck/$','namechecktool'),
    url(r'^toollengthcheck/$','lengthchecktool'),
    url(r'^toolfilecheck/$','filechecktool'),
    
    url(r'^cancel/$','cancelupload'),
    )


urlpatterns += patterns('',
    url(r'^rmPreImg/$', 'vms.views.rmPreImg'),
    url(r'^rmPreImgVgt/$', 'vgates.views.rmPreImgVgt'),
    url(r'^selectServer/$', 'vms.views.selectServer'),
    url(r'^selectServerVgt/','vgates.views.selectServer'),
    url(r'^getInstanceInfo/(\d+)/$','vms.views.getInstanceInfo'),
    url(r'^getInstanceInfoVgt/(\d+)/$','vgates.views.getInstanceInfo'),
    url(r'^selectServerEditVM/','vms.views.selectServerEditVM'),
    url(r'^selectServerEditVgt/','vgates.views.selectServerEditVgt'),
    url(r'^vmdelonserver/(\d+)/$','vms.views.delvm'),
    url(r'^vgtdelonserver/(\d+)/$','vgates.views.delvgt'),
    url(r'^selectServerVMStart/(\d+)/$','vms.views.selectServerVMStart'),
    url(r'^selectServerVgtStart/(\d+)/$','vgates.views.selectServerVgtStart'),
    url(r'^selectServerVMStop/(\d+)/$','vms.views.selectServerVMStop'),
    url(r'^selectServerVgtStop/(\d+)/$','vgates.views.selectServerVgtStop'),
    url(r'^selectServerResetVM/$','vms.views.selectServerResetVM'),
    url(r'^getVgateStatus/$','vgates.views.getVgateStatus'),
    url(r'^getVmStatus/$','vms.views.getVmStatus'),

    url(r'^getServerIp/', 'client.views.getServerIp'),
    url(r'^selectVM/','client.views.selectVM'),
    url(r'^stopVM/','client.views.stopVM'),
    url(r'^controlChecklab/','client.views.controlChecklab'),
    url(r'^clearRes/','client.views.clearRes'),
    url(r'^gettop10/','client.views.gettop10'),

    
    url(r'^registerstudent/','students.views.registerstudent'),
    url(r'^registerteacher/','teachers.views.registerteacher'),
    url(r'^accetpstudent/','students.views.accetstudent'),
    url(r'^accetpteacher/','teachers.views.accetpadmin'),
    url(r'^cancelstudent/','students.views.cancelregister'),
    url(r'^canceladmin/','teachers.views.canceladmin'),
    # url(r'^spangled/','students.views.spangled'),
    )


#-*- coding: utf-8 -*- 
'''
实现对服务器性能的监控，包括CPU，内存，硬盘等信息的获取
实现对服务器ip地址的管理
另外还实现了对操作日志的导出功能，将系统管理->系统日志中的内容导出为excel文件以供下载
'''

from sysmgr.models import *
from libvirt import libvirtError
from tsssite.settings import TIME_JS_REFRESH
from tsssite.server import ConnServer
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
from django.utils.translation import ugettext_lazy as _
from tsssite.settings import HERE, UPDATAFILE
import socket  
import fcntl  
import struct  
import os
import re
import zipfile
import subprocess
from adminsys.models import *
import datetime
from xlwt import *
import json
from vgates.models import *
from vms.models import *
from vswitches.models import *
from client.models import *

get_ip=""
old_ip="172.0.0.1"

# 获取CPU使用率
def cpuusage(request):
    """
    Return CPU Usage in %
    """
    #if not request.user.is_authenticated():
        #return HttpResponseRedirect('/login')
    host_id = 1
    host = Host.objects.get(id=host_id)
    try:
        conn = ConnServer(host)
    except:
        conn = None
    if conn:
        cpu_usage = conn.cpu_get_usage()
    return HttpResponse(cpu_usage)

# 获取内存使用率
def memusage(request):
    """
    Return Memory Usage in %
    """
    #if not request.user.is_authenticated():
        #return HttpResponseRedirect('/login')
    host_id = 1
    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except:
        conn = None
    if conn:
        mem_usage = conn.memory_get_usage()
    return HttpResponse(mem_usage[2])

# 获取硬盘使用率
def diskusage(request):
    host_id = 1
    host = Host.objects.get(id=host_id)
    try:
        conn = ConnServer(host)
    except:
        conn = None
    if conn:
        disk_usage = conn.disk_get_usage()
    return HttpResponse(disk_usage[3])

# 整合页面信息返回
def mgrsys(request):
    """
    Overview page.
    """
    #if not request.user.is_authenticated():
        #return HttpResponseRedirect('/login')
    hosts=Host.objects.filter(id__gt=1)
    # hosts=Host.objects.order_by('id')

    host_id = 1
    errors = []
    time_refresh = TIME_JS_REFRESH
    host = Host.objects.get(id=host_id)
    all_vm = hostname = arch = cpus = cpu_model = \
        type_conn = libvirt_ver = all_mem = \
        mem_usage = mem_percent = cpu_usage = \
        all_disk = disk_usage = disk_free = disk_percent = None

    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None

    if not conn:
        errors.append(e.message)
    else:
        have_kvm = conn.hard_accel_node()
        if not have_kvm:
            msg = _('Your CPU doesn\'t support hardware virtualization')
            errors.append(msg)

        #all_vm = sort_host(conn.vds_get_node())
        hostname, arch, cpus, cpu_model, type_conn, libvirt_ver = conn.node_get_info()
        all_mem, mem_usage, mem_percent = conn.memory_get_usage()
        cpu_usage = conn.cpu_get_usage()
        all_disk, disk_usage, disk_free, disk_percent = conn.disk_get_usage()
        hostname = host.hostname#added by lizc
        if request.method == 'POST':
            vname = request.POST.get('vname', '')
            dom = conn.lookupVM(vname)
            if 'start' in request.POST:
                try:
                    dom.create()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'shutdown' in request.POST:
                try:
                    dom.shutdown()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'destroy' in request.POST:
                try:
                    dom.destroy()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'suspend' in request.POST:
                try:
                    dom.suspend()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'resume' in request.POST:
                try:
                    dom.resume()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)

        conn.close()

    return render_to_response('templates/serverstate.html', {'host_id': host_id,
                                                'hosts':hosts,
                                                'errors': errors,
                                                'time_refresh': time_refresh,
                                                'all_vm': all_vm,
                                                'hostname': hostname,
                                                'arch': arch, 'cpus': cpus, 'cpu_model': cpu_model, 'cpu_usage': cpu_usage,
                                                'type_conn': type_conn, 'libvirt_ver': libvirt_ver,
                                                'all_mem': all_mem, 'mem_usage': mem_usage, 'mem_percent': mem_percent,
                                                'all_disk': all_disk, 'disk_usage': disk_usage, 'disk_percent': disk_percent
                                                },
                              context_instance=RequestContext(request))

def test(v):
    test.result = v
    return v
#配置服务器IP方法
def getip(request):
    global get_ip
    global old_ip
    if not 'username' in request.session:
        return HttpResponseRedirect('/Login/')
    getip=""
    getmask=""
    getgate=""
    getdns=" "
    get_ip= "ifcfg-"+get_interfaces()

    f = open("/etc/sysconfig/network-scripts/"+get_ip, "r")  
    while True:  
        line = f.readline()  
        if line:  
            if line.find("IPADDR=")>-1:
                getip=line[7:]
                old_ip=getip
            if line.find("NETMASK=")>-1:
                getmask=line[8:]
            if line.find("GATEWAY=")>-1:
                getgate=line[8:]
            if line.find("DNS=")>-1:
                getdns=line[4:] 
        else:  
          break
    f.close()  

    return render_to_response('templates/configip.html',{'getip':getip,'getmask':getmask,'getgate':getgate,'getdns':getdns},context_instance=RequestContext(request))

def get_interfaces():
    """
    获取所有网络接口信息
    遇到任何错误均抛出异常
    """
    changge_filename=''
    interfaces = {}
    # 获取接口名、索引号、启停状态、连接状态、硬件地址、IPv4地址
    for line in os.popen('ip -o addr show'):
        if test(re.match('^\d+:\s+(\w+)\s+inet\s+(\S+)\s+.+?\n$', line)):
            m = test.result
            name = m.group(1)
            interfaces[name]=(m.group(2))   
    try:
        csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        csock.connect(('8.8.8.8', 80))
        (addr, port) = csock.getsockname()
        csock.close()
        addr = addr+"/24"
    except socket.error:
        addr="127.0.0.1/24"
    for m_ip in interfaces.keys():
        if interfaces[m_ip]==addr:
            changge_filename=m_ip
    return changge_filename


# 修改服务器IP信息
def changeip(request):
    global get_ip
    global old_ip
    if not 'username' in request.session:
        return HttpResponseRedirect('/Login/')
    if request.method == 'POST':
        # 获取信息 
        getip=request.POST['change_ip']
        getmask=request.POST['change_mask']
        getgate=request.POST['change_gate']
        getdns=request.POST['change_dns']

        have_dn=0

        filepath='/etc/sysconfig/network-scripts/'

        f = open(filepath+get_ip,"r")  
        lines = f.readlines()#读取全部内容  
        for line in lines:
            if line.find("DNS=")>-1:
                 have_dn=1
        f.close()         
  
        # 创建sh文件并写入信???

        f=open(filepath+'changenetwork.sh','w') 


        f.write("#!/bin/bash"+'\n')
        f.write("ip="+ getip +'\n')
        f.write("mask="+ getmask +'\n')
        f.write("gate="+ getgate +'\n')
        
        if have_dn==1 and getdns!='/':
            f.write("dns="+ getdns +'\n')
            f.write('sed -i "/DNS/ s/\(.*=\).*/DNS=$dns/" '+filepath+get_ip +'\n')
                
        f.write('sed -i "/IPADDR/ s/\(.*=\).*/IPADDR=$ip/" '+filepath+get_ip +'\n')
        f.write('sed -i "/NETMASK/ s/\(.*=\).*/NETMASK=$mask/" '+filepath+get_ip +'\n')
        f.write('sed -i "/GATEWAY/ s/\(.*=\).*/GATEWAY=$gate/" '+filepath+get_ip +'\n')    
        if have_dn==0 and getdns!='/':
            f.write("echo 'DNS="+ getdns +"' >> '+filepath+'"+get_ip+'\n')
        f.write("service network restart"+'\n')    
        f.close()   
        # (去掉old_ip最后一位的回车占位符)
        old_ip=old_ip[:-1]
        # old_ip='172.19.8.210'
        # 更改数据库中有关的IP信息
        vmls = Vm.objects.filter(containerIP=old_ip)
        for vml in vmls:
            vml.containerIP=getip
            vml.save() 

        vgatels = Vgate.objects.filter(containerIP=old_ip)   
        for vgatel in vgatels:
            vgatel.containerIP=getip
            vgatel.save() 

        host = Host.objects.get(id=2)
        host.hostname=getip
        host.save()

        vswitchls = Vswitch.objects.filter(containerIP=old_ip)   
        for vswitchl in vswitchls:
            vswitchl.containerIP=getip
            vswitchl.save()  

        crs = Res.objects.filter(containerIP=old_ip)  
        for cr in crs:
            cr.containerIP=getip
            cr.save()          

        # 创建py文件并写入信???
        pf=open(filepath+'run.py','w')  
        pf.write('#!/usr/bin/python'+'\n')
        pf.write('import os, sys, stat'+'\n')
        pf.write('os.chmod("'+filepath+'changenetwork.sh", stat.S_IRWXU)'+'\n')
        pf.write('os.system("'+filepath+'changenetwork.sh ")'+'\n')
        pf.close()  
        # 执行py文件
        os.system("python "+filepath+"run.py")
        old_ip=get_ip
        os.system("rm -rf "+filepath+"changenetwork.sh")
        os.system("rm -rf "+filepath+"run.py")
    return render_to_response('templates/configip.html',{'getip':getip,'getmask':getmask,'getgate':getgate,'getdns':getdns},context_instance=RequestContext(request))

#系统升级
def updata(request):
    if not 'username' in request.session:
        return HttpResponseRedirect('/Login/')
    return render_to_response('templates/updatasystem.html')

# 解压文件
def unzip_file(request):
    zipfilename = UPDATAFILE+'/'+request.POST['filename']
    unziptodir=UPDATAFILE+'/'
    if not os.path.exists(unziptodir):
        os.makedirs(unziptodir, 0777)
    zfobj = zipfile.ZipFile(zipfilename)

    for name in zfobj.namelist():
        name = name.replace('\\','/')
        if name.endswith('/'):
            os.makedirs(os.path.join(unziptodir, name))
        else:
            try:

                ext_filename = os.path.join(unziptodir, name)
                ext_dir= os.path.dirname(ext_filename)
                if not os.path.exists(ext_dir):
                    os.makedirs(ext_dir,0777)
                outfile = open(ext_filename, 'wb')
                outfile.write(zfobj.read(name))
                # outfile.close()   
            except Exception, e:
                print e.message
            finally:
                outfile.close()
    data={}
    data['result']=1
    return HttpResponse(json.dumps(data))              
# 上传文件
def uploadtool(request):
    if not 'username' in request.session:
        return HttpResponseRedirect('/Login/')
    errors = []
    if request.method == 'POST':
        data=request.FILES["data"]
        name = request.POST["name"];

        if not os.path.isdir(UPDATAFILE):
            comd = "rm -rf "+UPDATAFILE
            os.system(comd)
            comd = "mkdir "+UPDATAFILE
            os.system(comd)

        path=UPDATAFILE+'/'
        with open(path+str(name), 'a+') as info:
            for chunk in data.chunks():
                info.write(chunk)
    return HttpResponseRedirect('/sysmgr/upsystem/')


def syslog(request):
    if not 'username' in request.session:
        return HttpResponseRedirect('/Login/')
    search_type = 0
    if "search_type" in request.GET:
        search_type = request.GET["search_type"]
        if search_type == "1":
            if request.GET["userid"]:
                # logs = Records.objects.filter(userid=request.GET["userid"]).order_by('-id')
                logs = Records.objects.filter(userid__contains=request.GET["userid"]).order_by('-id')
            else:
                logs = Records.objects.order_by('-id')
        elif search_type == "2":
            if request.GET["userType"]:
                usertype = request.GET["userType"]
                if usertype == u"学员":
                    ut = 1
                elif usertype == u"教练":
                    ut = 0
                elif usertype == u"管理员":
                    ut = 2
                else:
                    ut = -1
                logs = Records.objects.filter(usertype=ut).order_by('-id')
            else:
                logs = Records.objects.order_by('-id')
        elif search_type == "3":
            stime = request.GET["startTime"]
            etime = request.GET["endTime"]
            if stime and etime:
                start_time = datetime.datetime.strptime(stime, '%Y-%m-%d %H:%M')
                end_time = datetime.datetime.strptime(etime, '%Y-%m-%d %H:%M')
                logs = Records.objects.filter(starttime__range=[start_time, end_time]).order_by('-id')
            elif stime and (not etime):
                start_time = datetime.datetime.strptime(stime, '%Y-%m-%d %H:%M')
                logs = Records.objects.filter(starttime__gte=start_time).order_by('-id')
            elif etime and (not stime):
                end_time = datetime.datetime.strptime(etime, '%Y-%m-%d %H:%M')
                logs = Records.objects.filter(starttime__lte=end_time).order_by('-id')
            else:
                logs = Records.objects.order_by('-id')
    else:
        logs = Records.objects.order_by('-id')

    # 分页部分
    try:
        page = int(request.GET.get("page", 1))
        if page < 1:
            page = 1
    except ValueError:
            page = 1
    paginator = Paginator(logs, 12)
    try:
        logs_list = paginator.page(page)
    except(EmptyPage, InvalidPage, PageNotAnInteger):
        logs_list = paginator.page(paginator.num_pages)

    page_long = len(paginator.page_range)
    if page_long <= 5:
        # page_range = paginator.page_range[0:page_long]
        page_range = {
            'page_first': 0,
            'page_center': paginator.page_range[0:page_long],
            'page_last': 0
        }
    else:
        if page <= 3:
            # page_range = paginator.page_range[0:4]
            page_range = {
                'page_first': 0,
                'page_center': paginator.page_range[0:4],
                'page_last': page_long
            }
        else:
            if (page_long - page) > 2:
                # page_range = paginator.page_range[page-2:page+1]
                page_range = {
                    'page_first': 1,
                    'page_center': paginator.page_range[page-2:page+1],
                    'page_last': page_long
                }
            else:
                # page_range = paginator.page_range[page_long-3:page_long]
                page_range = {
                    'page_first': 1,
                    'page_center': paginator.page_range[page_long-4:page_long],
                    'page_last': 0
                }

    for log in logs_list:
        log.usertype = ["教练", "学员", "管理员"][log.usertype]
        log.starttime = log.starttime.strftime('%Y-%m-%d %H:%M:%S')
        log.endtime = log.endtime.strftime('%Y-%m-%d %H:%M:%S')
        log.result = "OK" if log.result else "ERROR"

    datas = {"logs": logs_list, "page_range": page_range}
    if search_type:
        datas["search_type"] = search_type
        if search_type == "1":
            datas['userid'] = request.GET["userid"]
        elif search_type == "2":
            datas['usertype'] = request.GET["userType"]
        elif search_type == "3":
            datas['startTime'] = request.GET["startTime"]
            datas['endTime'] = request.GET["endTime"]
    else:
        datas["search_type"] = "1"

    return render_to_response('templates/syslog.html',datas, context_instance=RequestContext(request))


def outputlog(request):
    if not 'username' in request.session:
        return HttpResponseRedirect('/Login/')
    search_type = request.POST["search_type"]
    if search_type == "1":
        if request.POST["userid"]:
            # logs = Records.objects.filter(userid=request.POST["userid"])
            logs = Records.objects.filter(userid__contains=request.POST["userid"])
        else:
            logs = Records.objects.all()
    elif search_type == "2":
        if request.POST["userType"]:
            usertype = request.POST["userType"]
            if usertype == u"学员":
                ut = 1
            elif usertype == u"教练":
                ut = 0
            elif usertype == u"管理员":
                ut = 2
            else:
                ut = -1
            logs = Records.objects.filter(usertype=ut)
        else:
            logs = Records.objects.all()
    elif search_type == "3":
        stime = request.POST["startTime"]
        etime = request.POST["endTime"]
        if stime and etime:
            start_time = datetime.datetime.strptime(stime, '%Y-%m-%d %H:%M')
            end_time = datetime.datetime.strptime(etime, '%Y-%m-%d %H:%M')
            logs = Records.objects.filter(starttime__range=[start_time, end_time])
        elif stime and (not etime):
            start_time = datetime.datetime.strptime(stime, '%Y-%m-%d %H:%M')
            logs = Records.objects.filter(starttime__gte=start_time)
        elif etime and (not stime):
            end_time = datetime.datetime.strptime(etime, '%Y-%m-%d %H:%M')
            logs = Records.objects.filter(starttime__lte=end_time)
        else:
            logs = Records.objects.all()

    wbk = Workbook()
    sheet = wbk.add_sheet("logs")
    sheet.write(0, 0, u"用户")
    sheet.write(0, 1, u"类型")
    sheet.write(0, 2, u"操作")
    sheet.write(0, 3, u"开始时间")
    sheet.write(0, 4, u"结束时间")
    sheet.write(0, 5, u"结果")
    for i in range(1, len(logs) + 1):
        sheet.write(i, 0, logs[i - 1].userid)
        sheet.write(i, 1, [u"教练", u"学员", u"管理员"][logs[i - 1].usertype])
        sheet.write(i, 2, logs[i - 1].operate)
        sheet.write(i, 3, logs[i - 1].starttime.strftime('%Y-%m-%d %H:%M:%S'))
        sheet.write(i, 4, logs[i - 1].endtime.strftime('%Y-%m-%d %H:%M:%S'))
        sheet.write(i, 5, "OK" if logs[i - 1].result else "ERROR")

    wbk.save('logs.xls')

    if not os.path.isdir("document/logs"):
        comd = "mkdir document/logs"
        os.system(comd)
    path = os.path.join(HERE, 'document/logs/')
    command = "mv logs.xls " + path
    os.system(command)

    return HttpResponse(json.dumps('/document/logs/logs.xls'))
